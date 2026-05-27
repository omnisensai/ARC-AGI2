"""Family-level contract validator — gate beyond per-sample verification.

build_micro.py proves each GENERATED task is correct (solver matches output) +
AST-clean. That is necessary but NOT sufficient: if the generator never emits a
dangerous case, the family CONTRACT can stay under-specified while thousands of
samples pass (this is how the boundary_mask bg-majority bug hid).

This validator adds:
  (4) PROPERTY/PRECONDITION AUDIT — over a fresh batch, assert the preconditions
      each solver relies on actually hold (bg is the unique mode; ray has exactly
      one source; components have a unique largest; line endpoints collinear;
      periodic has a recoverable minimal period; ...).
  (5) ADVERSARIAL PROBES — feed hostile inputs the generator avoids (non-collinear
      endpoints, zero/multiple markers, ties, all-bg, 1x1, solid). Each must
      TERMINATE within a hard timeout and return a well-formed grid OR raise a
      controlled exception. A HANG / MALFORMED / NON-DETERMINISTIC result fails.

Correctness, timeout, and AST audit (gates 1-3) remain build_micro's job; this
complements them. Exit code is nonzero if any family violates its contract.
"""
import argparse, json, os, subprocess, sys, tempfile
from collections import Counter, deque
from math import gcd
from pathlib import Path

P2 = Path(__file__).resolve().parent.parent


# ----------------------------- helpers -----------------------------------
def pairs(task):
    return task["train"] + task["test"]


def is_rect_int(g):
    return (isinstance(g, list) and len(g) > 0 and all(isinstance(r, list) for r in g)
            and len({len(r) for r in g}) == 1 and len(g[0]) > 0
            and all(isinstance(v, int) for r in g for v in r))


def mode(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def bg_unique(g):
    top = Counter(v for row in g for v in row).most_common(2)
    return len(top) == 1 or top[0][1] > top[1][1]


def comps_of(g, bg, conn8):
    H, W = len(g), len(g[0])
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if conn8:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = [[False] * W for _ in range(H)]
    out = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in nb:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                out.append(cells)
    return out


def collinear(p, q):
    dr, dc = q[0] - p[0], q[1] - p[1]
    return dr == 0 or dc == 0 or abs(dr) == abs(dc)


# ----------------------- per-family preconditions -------------------------
# Each returns a short violation string, or None if the pair is well-formed.
def pc_complete_line(g):
    bg = mode(g)
    pts = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] != bg]
    if len(pts) >= 2 and not collinear(pts[0], pts[-1]):
        return "non-collinear endpoints"
    return None


def _pc_components(conn8):
    def f(g):
        comps = comps_of(g, mode(g), conn8)
        sizes = sorted((len(c) for c in comps), reverse=True)
        if len(sizes) >= 2 and sizes[0] == sizes[1]:
            return "largest-component size tie (selection ambiguous)"
        return None
    return f


def pc_extract_largest(g):
    bg = mode(g)
    nz = Counter(v for row in g for v in row if v != bg)
    if len(nz) < 2:
        return "fewer than 2 non-bg colours (need blobs + a marker)"
    m = min(nz, key=lambda k: nz[k])
    if nz[m] != 1:
        return f"marker colour is not a single cell (count {nz[m]})"
    comps = [c for c in comps_of(g, bg, False) if g[c[0][0]][c[0][1]] != m]
    sizes = sorted((len(c) for c in comps), reverse=True)
    if len(sizes) < 2:
        return "fewer than 2 blobs"
    if sizes[0] == sizes[1]:
        return "largest-blob size tie (selection ambiguous)"
    return None


def _edge_markers(g):
    H, W = len(g), len(g[0]); bg = mode(g)
    return [(r, c) for r in range(H) for c in range(W)
            if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]


def _corner_markers(g):
    H, W = len(g), len(g[0]); bg = mode(g)
    return [(r, c) for (r, c) in ((0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)) if g[r][c] != bg]


def pc_ray_edge(g):
    n = len(_edge_markers(g))
    return None if n == 1 else f"expected exactly 1 edge source, found {n}"


def pc_ray_corner(g):
    n = len(_corner_markers(g))
    return None if n == 1 else f"expected exactly 1 corner source, found {n}"


def pt_ray_blocker(task):
    # TASK-level: at least one pair must put a blocker ON the ray path, else the
    # whole task is indistinguishable from ray_to_edge (no-blocker pairs are OK
    # as variety, but a task with zero is mislabeled).
    for p in pairs(task):
        g = p["input"]; H, W = len(g), len(g[0]); bg = mode(g)
        em = _edge_markers(g)
        if len(em) != 1:
            continue
        r, c = em[0]
        dr, dc = (1, 0) if r == 0 else (-1, 0) if r == H - 1 else (0, 1) if c == 0 else (0, -1)
        rr, cc = r + dr, c + dc
        while 0 <= rr < H and 0 <= cc < W:
            if g[rr][cc] != bg:
                return None
            rr += dr; cc += dc
    return "no pair has an on-path blocker (task == ray_to_edge)"


def pc_periodic_ext(g):
    bg = mode(g)
    for r in range(len(g)):
        cols = [g[r][c] for c in range(len(g[0])) if g[r][c] != bg]
        if len(cols) >= 2 and len(set(cols)) != 1:
            return "active row has mixed colours (period colour ambiguous)"
    return None


def pc_periodic_repair(g):
    H, W = len(g), len(g[0])

    def consistent(pr, pc):
        seen = {}
        for r in range(H):
            for c in range(W):
                v = g[r][c]
                if v == 0:
                    continue
                k = (r % pr, c % pc)
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    pr = pc = None
    for a in range(1, H + 1):
        for b in range(1, W + 1):
            if consistent(a, b):
                pr, pc = a, b; break
        if pr:
            break
    have = set()
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                have.add((r % pr, c % pc))
    missing = pr * pc - len(have)
    if missing > 0:
        return f"{missing} residue class(es) fully holed (unrecoverable)"
    return None


# --------------------- per-family config registry -------------------------
def pc_single_seed(g):
    bg = mode(g)
    nz = Counter(v for row in g for v in row if v != bg)
    if not nz:
        return "no seed/marker (all background)"
    mn = min(nz.values())
    if mn != 1:
        return f"seed/marker is not a single cell (rarest non-bg count {mn})"
    if sum(1 for v in nz.values() if v == mn) != 1:
        return "ambiguous seed/marker (multiple rarest non-bg colours)"
    return None


def pc_copy_markers(g):
    bg = mode(g)
    comps = comps_of(g, bg, False)
    big = [c for c in comps if len(c) >= 2]
    singles = [c for c in comps if len(c) == 1]
    if len(big) != 1:
        return f"expected exactly 1 multi-cell prototype, found {len(big)}"
    if not singles:
        return "no marker pixels"
    pcol = g[big[0][0][0]][big[0][0][1]]
    if any(g[s[0][0]][s[0][1]] == pcol for s in singles):
        return "a marker shares the prototype colour"
    return None


def pc_recolor_marker(g):
    H, W = len(g), len(g[0]); bg = mode(g)
    nz = Counter(v for row in g for v in row if v != bg)
    if not nz:
        return "no objects"
    C = max(nz, key=lambda k: nz[k])
    nb8 = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = [[False] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if g[r][c] == C and not seen[r][c]:
                comp = []; st = [(r, c)]; seen[r][c] = True
                while st:
                    y, x = st.pop(); comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == C:
                            seen[ny][nx] = True; st.append((ny, nx))
                mcols = set()
                for (y, x) in comp:
                    for dy, dx in nb8:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != bg and g[ny][nx] != C:
                            mcols.add(g[ny][nx])
                if len(mcols) == 0:
                    return "an object has no adjacent marker"
                if len(mcols) > 1:
                    return "an object touches markers of >1 colour (ambiguous)"
    return None


def pc_border_seed(g):
    H, W = len(g), len(g[0]); bg = mode(g)
    border = [(r, c) for r in range(H) for c in range(W)
              if g[r][c] != bg and (r in (0, H - 1) or c in (0, W - 1))]
    if len(border) != 1:
        return f"expected exactly 1 border seed, found {len(border)}"
    return None


def pc_fence(g):
    bg = mode(g)
    if bg == 8:
        return "background is the fence colour 8"
    if any(v == 8 for row in g for v in row):
        return "fence colour 8 already present in input (ambiguous)"
    if not any(v != bg for row in g for v in row):
        return "no shape to fence"
    return None


def pc_flip_h(g):
    if g == [row[::-1] for row in g]:
        return "input is already left-right symmetric (flip is a no-op)"
    return None


def pc_flip_v(g):
    if g == g[::-1]:
        return "input is already top-bottom symmetric (flip is a no-op)"
    return None


def pc_draw_bbox(g):
    bg = mode(g)
    cells = [(r, c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] != bg]
    if not cells:
        return "no object"
    if len({g[r][c] for r, c in cells}) != 1:
        return "object has more than one colour"
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    if r0 == r1 and c0 == c1:
        return "degenerate bbox (single cell)"
    perim_bg = any(g[r0][c] == bg or g[r1][c] == bg for c in range(c0, c1 + 1)) \
        or any(g[r][c0] == bg or g[r][c1] == bg for r in range(r0, r1 + 1))
    if not perim_bg:
        return "bbox perimeter already complete (frame adds nothing)"
    return None


def pc_nonsquare(g):
    return "input is square (rotate would not change size)" if len(g) == len(g[0]) else None


def adv(rows):  # convenience
    return rows


CONFIG = {
    # micro (same-size)
    "ray_to_edge":            {"precond": pc_ray_edge,
                               "adv": [[[0, 0, 0], [0, 0, 0], [0, 3, 0]],            # 2 markers? (none on edge) -> degenerate
                                       [[3, 0, 0, 3], [0]*4, [0]*4, [0]*4]]},        # two edge markers
    "ray_until_blocker":      {"precond": pc_ray_edge, "precond_task": pt_ray_blocker,
                               "adv": [[[3, 0, 0], [0, 0, 0], [0, 0, 0]],            # source, no blocker
                                       [[0, 3, 0, 3, 0]]]},                          # 2 edge markers, 1xN
    "ray_diag_to_edge":       {"precond": pc_ray_corner, "adv": [[[0, 0], [0, 0]]]},
    "ray_diag_until_blocker": {"precond": pc_ray_corner, "adv": [[[0, 0], [0, 0]]]},  # no corner -> StopIteration
    "complete_line":          {"precond": pc_complete_line,
                               "adv": [[[3, 0, 0, 0, 0], [0]*5, [0, 0, 0, 0, 3]]]},  # non-collinear -> HANG risk
    "extract_largest_recolor": {"precond": pc_extract_largest,
                               "adv": [[[3, 3, 0, 4], [0, 0, 0, 0], [3, 3, 0, 0]]]},  # blob tie + marker
    "component_4conn":        {"precond": _pc_components(False),
                               "adv": [[[3, 0, 4], [0, 0, 0]]]},
    "component_8conn":        {"precond": _pc_components(True),
                               "adv": [[[3, 0, 4], [0, 0, 0]]]},
    "periodic_extension":     {"precond": pc_periodic_ext, "adv": [[[3, 4, 5, 6, 7]]]},
    "periodic_repair":        {"precond": pc_periodic_repair, "uses_bg": False, "adv": [[[0, 0], [0, 0]]]},
    "boundary_mask":          {"adv": [[[3]*7 for _ in range(7)]]},                  # shape > bg (the bug)
    "u_cup_fill":             {},
    "fill_enclosed":          {},
    "sandwich_fill":          {},
    "symmetry_complete_vertical":   {},
    "symmetry_complete_horizontal": {},
    "gravity_water":          {},
    "drop_to_floor":          {},
    "cross_from_seed":        {"precond": pc_single_seed, "adv": [[[2, 0, 0], [0, 0, 0], [0, 0, 0]]]},
    "star_from_seed":         {"precond": pc_single_seed, "adv": [[[2, 0, 0], [0, 0, 0], [0, 0, 0]]]},
    "flood_from_seed":        {"precond": pc_single_seed, "adv": [[[5, 5, 5], [5, 2, 5], [5, 5, 5]]]},
    "flood_from_seed_8":      {"precond": pc_single_seed, "adv": [[[5, 5, 5], [5, 2, 5], [5, 5, 5]]]},
    "move_to_marker":         {"precond": pc_single_seed, "adv": [[[3, 3, 0, 0], [0, 0, 0, 4]]]},
    "copy_to_markers":        {"precond": pc_copy_markers, "adv": [[[3, 3, 0, 0, 4], [3, 0, 0, 0, 0]]]},
    "recolor_by_marker":      {"precond": pc_recolor_marker, "adv": [[[5, 5, 0], [0, 0, 0]]]},
    "ball_roll":              {"precond": pc_border_seed, "adv": [[[2, 0, 0], [0, 5, 0], [0, 0, 0]]]},
    "maze_runner":            {"precond": pc_border_seed, "adv": [[[2, 0, 0], [0, 5, 0], [0, 0, 0]]]},
    "fence_8conn":            {"precond": pc_fence, "adv": [[[3, 3, 0], [0, 0, 0]]]},
    "fence_4conn":            {"precond": pc_fence, "adv": [[[3, 3, 0], [0, 0, 0]]]},
    "flip_horizontal":        {"precond": pc_flip_h, "uses_bg": False},
    "flip_vertical":          {"precond": pc_flip_v, "uses_bg": False},
    "draw_bbox":              {"precond": pc_draw_bbox},
    # micro_diff
    "crop_to_bbox":           {"diff": True, "adv": [[[0, 0], [0, 0]]]},             # no content -> controlled
    "scale_2x":               {"diff": True, "uses_bg": False},
    "rotate_90":              {"diff": True, "uses_bg": False, "precond": pc_nonsquare},
}

UNIVERSAL_ADV = [[[0]], [[0]*5 for _ in range(5)], [[5]*5 for _ in range(5)], [[0, 3, 0, 3, 0]]]

_ADV_RUNNER = r'''
import json, sys
exec(open(sys.argv[1]).read(), (ns := {}))
g = json.load(open(sys.argv[2])); fn = ns["solve"]
def rect(x):
    return (isinstance(x, list) and len(x) > 0 and all(isinstance(r, list) for r in x)
            and len({len(r) for r in x}) == 1 and len(x[0]) > 0
            and all(isinstance(v, int) for r in x for v in r))
try:
    o1 = fn([r[:] for r in g]); o1 = o1.tolist() if hasattr(o1, "tolist") else o1
    o2 = fn([r[:] for r in g]); o2 = o2.tolist() if hasattr(o2, "tolist") else o2
    if not rect(o1): print("MALFORMED")
    elif o1 != o2:   print("NONDET")
    else:            print("OK")
except Exception as e:
    print("RAISED:" + type(e).__name__)
'''


_GEN_RUNNER = r'''
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("m", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
batch = int(sys.argv[2]); tiers = [0, 1, 2]
out = [m.generate(seed=10000 + i, difficulty=tiers[i % 3]) for i in range(batch)]
json.dump(out, open(sys.argv[3], "w"))
'''


def gen_batch(gen_path, batch, timeout):
    """Generate a fresh batch in a SUBPROCESS so a hanging/slow generator is
    reported (GENERATOR TIMEOUT) instead of stalling the validator itself —
    the exact failure mode the extract_largest_recolor hang exposed."""
    rf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); rf.write(_GEN_RUNNER); rf.close()
    of = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); of.close()
    try:
        r = subprocess.run([sys.executable, rf.name, str(gen_path), str(batch), of.name],
                           capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            last = (r.stderr.strip().splitlines() or ["?"])[-1][:70]
            return [], f"GENERATOR ERROR ({last})"
        return json.load(open(of.name)), None
    except subprocess.TimeoutExpired:
        return [], f"GENERATOR TIMEOUT (>{timeout}s for {batch} tasks)"
    finally:
        os.unlink(rf.name); os.unlink(of.name)


def run_adv(solver_path, grid, timeout=5):
    rf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); rf.write(_ADV_RUNNER); rf.close()
    gf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(grid, gf); gf.close()
    try:
        r = subprocess.run([sys.executable, rf.name, str(solver_path), gf.name],
                           capture_output=True, text=True, timeout=timeout)
        line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "MALFORMED"
        return line
    except subprocess.TimeoutExpired:
        return "HANG"
    finally:
        os.unlink(rf.name); os.unlink(gf.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="micro")
    ap.add_argument("--batch", type=int, default=150, help="fresh tasks per family for precondition audit")
    ap.add_argument("--gen-timeout", type=int, default=30, help="seconds allowed for a family's batch generation")
    a = ap.parse_args()
    ROOT = P2 / a.dir
    GEN, SOLV = ROOT / "generators", ROOT / "solvers"
    fams = sorted(p.stem for p in GEN.glob("*.py"))
    print(f"contract validator — dir={a.dir}, {len(fams)} families, batch={a.batch}\n")

    bad_families = 0
    for fam in fams:
        cfg = CONFIG.get(fam, {})
        uses_bg = cfg.get("uses_bg", True)
        is_diff = cfg.get("diff", False)
        precond = cfg.get("precond")
        precond_task = cfg.get("precond_task")
        solver = SOLV / f"{fam}.py"

        # ---- (4) precondition / property audit over a fresh batch ----
        # Generation runs in a timeout-guarded subprocess: a hanging generator is
        # reported, never stalls the validator.
        viol = Counter()
        tasks, gen_err = gen_batch(GEN / f"{fam}.py", a.batch, a.gen_timeout)
        if gen_err:
            viol[gen_err] += 1
        for task in tasks:
            if precond_task:
                v = precond_task(task)
                if v:
                    viol[v] += 1
            for p in pairs(task):
                gi, go = p["input"], p["output"]
                if not is_rect_int(gi) or not is_rect_int(go):
                    viol["non-rectangular grid"] += 1; continue
                same = len(gi) == len(go) and len(gi[0]) == len(go[0])
                if is_diff and same:
                    viol["expected diff-size, got same-size"] += 1
                if not is_diff and not same:
                    viol["expected same-size, got diff-size"] += 1
                if uses_bg and not bg_unique(gi):
                    viol["background not the unique mode"] += 1
                if precond:
                    v = precond(gi)
                    if v:
                        viol[v] += 1

        # ---- (5) adversarial probes ----
        adv_inputs = UNIVERSAL_ADV + cfg.get("adv", [])
        adv_bad = []
        for grid in adv_inputs:
            res = run_adv(solver, grid)
            if res.startswith("HANG") or res.startswith("MALFORMED") or res.startswith("NONDET"):
                adv_bad.append((res, grid))

        ok = (not viol) and (not adv_bad)
        bad_families += (not ok)
        status = "OK " if ok else "XX "
        print(f"{status}{fam:24s} precond_violations={sum(viol.values()):4d}  adversarial_unsafe={len(adv_bad)}")
        for msg, n in viol.items():
            print(f"      precond: {msg}  (x{n})")
        for res, grid in adv_bad:
            print(f"      ADVERSARIAL {res}  on {grid}")

    print(f"\n{'ALL FAMILIES PASS CONTRACT' if not bad_families else f'{bad_families} FAMILIES FAIL CONTRACT'}")
    sys.exit(1 if bad_families else 0)


if __name__ == "__main__":
    main()
