"""Micro-primitive family: snap_to_outline.

Input has TWO non-bg objects of different colours:
  - a SOLID rectangle (colour C_solid)
  - a HOLLOW rectangle outline (colour C_outline) whose interior is the same
    dimensions as the solid rectangle (so the solid would fit inside)

Rule: the solid rectangle "snaps" inside the outline — its cells move to fill
the outline's interior. Output: original solid cells -> bg; outline cells stay;
outline interior cells -> C_solid.

A "puzzle / shape-fitting" primitive: piece matches cavity, piece teleports in.

Tiers: 0 fixed 11x11 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "snap_to_outline"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def _components_by_colour(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True; q.append((ny, nx))
            comps.append((col, cells))
    return comps


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    if len(comps) != 2:
        return {}
    solid = hollow = None
    for col, cells in comps:
        rmin = min(r for r, _ in cells); rmax = max(r for r, _ in cells)
        cmin = min(c for _, c in cells); cmax = max(c for _, c in cells)
        bbox_size = (rmax - rmin + 1) * (cmax - cmin + 1)
        if len(cells) == bbox_size:
            solid = (col, cells, (rmin, rmax, cmin, cmax))
        else:
            # hollow: cells lie on the bbox boundary only
            boundary = {(r, c) for r in (rmin, rmax) for c in range(cmin, cmax + 1)} \
                     | {(r, c) for c in (cmin, cmax) for r in range(rmin, rmax + 1)}
            if set(cells) == boundary:
                hollow = (col, cells, (rmin, rmax, cmin, cmax))
    if solid is None or hollow is None:
        return {}

    _, solid_cells, (sr0, sr1, sc0, sc1) = solid
    sol_h = sr1 - sr0 + 1; sol_w = sc1 - sc0 + 1
    solid_col = solid[0]
    _, _, (hr0, hr1, hc0, hc1) = hollow
    hollow_inner_h = hr1 - hr0 - 1; hollow_inner_w = hc1 - hc0 - 1
    if (sol_h, sol_w) != (hollow_inner_h, hollow_inner_w):
        return {}

    T = {}
    for (y, x) in solid_cells:
        T[(y, x)] = bg
    for r in range(hr0 + 1, hr1):
        for c in range(hc0 + 1, hc1):
            T[(r, c)] = solid_col
    return T


def apply_T(g, T):
    out = [row[:] for row in g]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
'''


def family_prompt_hint() -> str:
    return "Move the solid block into the matching hollow outline (it fits exactly)."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(11, 14); W = rng.randint(11, 14)

    if difficulty == 0:
        bg, solid_col, hollow_col = 0, 2, 4
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        solid_col, hollow_col = rng.sample(avail, 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        solid_col, hollow_col = rng.sample(avail, 2)

    # Solid block dims: at least 1x1, max 3x3
    sol_h = rng.randint(1, 3); sol_w = rng.randint(1, 3)
    # Hollow outline interior is sol_h x sol_w, so outline bbox is (sol_h+2) x (sol_w+2)
    out_h = sol_h + 2; out_w = sol_w + 2

    # Place solid and outline non-overlapping with margin between bboxes
    for _ in range(80):
        sr0 = rng.randint(0, H - sol_h); sc0 = rng.randint(0, W - sol_w)
        hr0 = rng.randint(0, H - out_h); hc0 = rng.randint(0, W - out_w)
        sr1 = sr0 + sol_h - 1; sc1 = sc0 + sol_w - 1
        hr1 = hr0 + out_h - 1; hc1 = hc0 + out_w - 1
        # bbox margin: at least 1 cell of bg between the two bboxes
        if (sr1 + 1 < hr0 or hr1 + 1 < sr0 or
            sc1 + 1 < hc0 or hc1 + 1 < sc0):
            break
    else:
        return _instance(rng, difficulty)

    inp = [[bg] * W for _ in range(H)]
    for r in range(sr0, sr0 + sol_h):
        for c in range(sc0, sc0 + sol_w):
            inp[r][c] = solid_col
    # Hollow rectangle outline (boundary only)
    for r in range(hr0, hr1 + 1):
        inp[r][hc0] = hollow_col; inp[r][hc1] = hollow_col
    for c in range(hc0, hc1 + 1):
        inp[hr0][c] = hollow_col; inp[hr1][c] = hollow_col

    out = [row[:] for row in inp]
    for r in range(sr0, sr0 + sol_h):
        for c in range(sc0, sc0 + sol_w):
            out[r][c] = bg
    for r in range(hr0 + 1, hr1):
        for c in range(hc0 + 1, hc1):
            out[r][c] = solid_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
