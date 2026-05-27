"""Micro-primitive family: copy_to_markers.

One prototype object (a connected blob of colour C) and several marker pixels
(colour M) sit on the background. The prototype is replicated at every marker —
each marker becomes the bounding-box top-left of a copy. The prototype stays.
The markers are the seeds that name where to stamp. Teaches prototype +
replication / anchoring at multiple targets.

Tiers: 0 fixed-ish, bg 0 | 1 + colour/bg | 2 + varied size/count.
"""
import random

FAMILY = "copy_to_markers"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    proto = max(comps, key=len)                       # prototype = largest component
    C = g[proto[0][0]][proto[0][1]]
    pr0 = min(r for r, c in proto); pc0 = min(c for r, c in proto)
    offs = [(r - pr0, c - pc0) for (r, c) in proto]
    markers = [cells[0] for cells in comps if len(cells) == 1 and g[cells[0][0]][cells[0][1]] != C]
    T = {}
    for (mr, mc) in markers:
        for (dr, dc) in offs:
            nr, nc = mr + dr, mc + dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = C
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
    return "Stamp a copy of the prototype object at every marker pixel."


def _blob(rng, max_h, max_w):
    target = rng.randint(3, max(3, (max_h * max_w) // 2))    # >= 3 cells, so the
    cells = {(0, 0)}                                         # prototype never ties with single-cell markers
    for _ in range(target * 60):
        if len(cells) >= target:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < max_h and 0 <= nx < max_w and (ny, nx) not in cells:
            cells.add((ny, nx))
    mnr = min(r for r, c in cells); mnc = min(c for r, c in cells)
    return {(r - mnr, c - mnc) for (r, c) in cells}


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12; mh = mw = 3
    else:
        H = rng.randint(11, 16); W = rng.randint(11, 16); mh = mw = 3
    if difficulty == 0:
        bg, C, M = 0, 3, 4; n_mark = 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, M = rng.sample([c for c in range(1, 10) if c != bg], 2); n_mark = rng.randint(2, 3)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, M = rng.sample([c for c in range(0, 10) if c != bg], 2); n_mark = rng.randint(2, 4)

    rel = _blob(rng, mh, mw)
    oh = max(r for r, c in rel) + 1; ow = max(c for r, c in rel) + 1

    def footprint(r0, c0):
        return {(r0 + r + dr, c0 + c + dc) for (r, c) in rel for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

    for _ in range(80):
        inp = [[bg] * W for _ in range(H)]
        used = set()
        pr0 = rng.randint(0, H - oh); pc0 = rng.randint(0, W - ow)     # prototype location
        proto = {(pr0 + r, pc0 + c) for (r, c) in rel}
        used |= footprint(pr0, pc0)
        markers = []
        ok = True
        for _m in range(n_mark):
            placed = False
            for _try in range(40):
                mr = rng.randint(0, H - oh); mc = rng.randint(0, W - ow)
                fp = footprint(mr, mc) | {(mr + r, mc + c) for (r, c) in rel}
                if not (fp & used):
                    markers.append((mr, mc)); used |= fp; placed = True; break
            if not placed:
                ok = False; break
        if not ok or len(markers) < 2:
            continue
        for (r, c) in proto:
            inp[r][c] = C
        for (mr, mc) in markers:
            inp[mr][mc] = M
        out = [row[:] for row in inp]
        for (mr, mc) in markers:
            for (r, c) in rel:
                out[mr + r][mc + c] = C
        return {"input": inp, "output": out}
    # fallback: prototype + 2 well-separated markers on a clean grid
    inp = [[bg] * W for _ in range(H)]
    for (r, c) in rel:
        inp[r][c] = C
    m1 = (H - oh, 0); m2 = (H - oh, W - ow)
    inp[m1[0]][m1[1]] = M; inp[m2[0]][m2[1]] = M
    out = [row[:] for row in inp]
    for (mr, mc) in (m1, m2):
        for (r, c) in rel:
            out[mr + r][mc + c] = C
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
