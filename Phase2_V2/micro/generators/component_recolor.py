"""Micro-primitive family: component_recolor (keep-largest).

Several disjoint single-colour blobs sit on a background. The largest connected
component is kept; every smaller component is erased to background. Teaches
connected components + size selection.

Output built directly from the rule, independent of the solver. The generator
guarantees one strictly-largest blob and ≥1 cell of separation between blobs.

Tiers: 0 bg 0, colour 2, 3 blobs | 1 + colour/bg | 2 + varied size/count.
"""
import random

FAMILY = "component_recolor"


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
    if not comps:
        return {}
    largest = max(comps, key=len)
    T = {}
    for cells in comps:
        if cells is largest:
            continue
        for (y, x) in cells:
            T[(y, x)] = bg
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
    return "Keep the largest connected blob; erase the smaller ones to background."


def _place(rng, grid, H, W, h, w, color, occ):
    """Try to place an h×w rectangle of `color` with a 1-cell halo clear of occ."""
    for _ in range(50):
        r = rng.randint(0, H - h); c = rng.randint(0, W - w)
        halo = {(rr, cc) for rr in range(r - 1, r + h + 1) for cc in range(c - 1, c + w + 1)}
        if halo & occ:
            continue
        for rr in range(r, r + h):
            for cc in range(c, c + w):
                grid[rr][cc] = color; occ.add((rr, cc))
        occ |= {(rr, cc) for rr in range(r, r + h) for cc in range(c, c + w)}
        return True
    return False


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(9, 14); W = rng.randint(9, 14)

    if difficulty == 0:
        bg, color, n_small = 0, 2, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg]); n_small = 2
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg]); n_small = rng.randint(2, 3)

    grid = [[bg] * W for _ in range(H)]
    occ = set()
    # one strictly-largest blob
    bh, bw = rng.choice([(2, 3), (3, 2), (3, 3)])
    _place(rng, grid, H, W, bh, bw, color, occ)
    big_area = bh * bw
    # smaller blobs, each strictly smaller than the big one
    for _ in range(n_small):
        for _ in range(20):
            sh, sw = rng.choice([(1, 1), (1, 2), (2, 1)])
            if sh * sw < big_area:
                break
        _place(rng, grid, H, W, sh, sw, color, occ)

    inp = [row[:] for row in grid]
    # output: keep only the largest component
    from collections import deque
    seen = [[False] * W for _ in range(H)]; comps = []
    for r in range(H):
        for c in range(W):
            if inp[r][c] != bg and not seen[r][c]:
                cells = []; q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and inp[ny][nx] == color:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(cells)
    largest = max(comps, key=len)
    out = [[bg] * W for _ in range(H)]
    for (y, x) in largest:
        out[y][x] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
