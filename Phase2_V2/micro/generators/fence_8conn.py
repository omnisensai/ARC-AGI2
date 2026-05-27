"""Micro-primitive family: fence_8conn (square fence around a shape).

A shape (an irregular blob of colour C) is fenced: every background cell that is
8-adjacent to the shape (orthogonal OR diagonal) is painted the fence colour 8.
Because the diagonal-corner cells are included, the fence closes into a proper
square ring around the shape — no rounded/open corners.

The fence colour is a FIXED constant (8); the seed/marker "name the colour"
mechanic lives in its own families (recolor_by_marker, extract_largest_recolor).

Matched pair with fence_4conn: the 4-connected fence OMITS the diagonal corners
(rounded, open at the corners). This is exactly where models wrongly round
corners with 4-connectivity instead of 8 — the pair makes it explicit.

Tiers: 0 fixed-ish, bg 0, shape 3 | 1 + colour/bg | 2 + varied size/shape.
"""
import random

FAMILY = "fence_8conn"
FENCE = 8
NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def canonical_solver() -> str:
    return '''from collections import Counter

NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and g[r + dr][c + dc] != bg
                                     for dr, dc in NB):
                T[(r, c)] = 8                 # fixed fence colour, 8-connected ring
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
    return "Fence the shape: paint every cell 8-adjacent to it (incl. diagonals) colour 8 — square corners."


def _blob(rng, H, W, size):
    cells = {(rng.randint(2, H - 3), rng.randint(2, W - 3))}
    for _ in range(size * 60):
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 2 <= ny < H - 2 and 2 <= nx < W - 2 and (ny, nx) not in cells:   # keep off border so fence fits
            cells.add((ny, nx))
    return cells


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(10, 15); W = rng.randint(10, 15)
    if difficulty == 0:
        bg, C, size = 0, 3, 6
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 7)]); C = rng.choice([c for c in range(1, 8) if c != bg]); size = rng.randint(5, 9)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 7)]); C = rng.choice([c for c in range(1, 8) if c != bg]); size = rng.randint(5, 12)

    for _ in range(40):
        blob = _blob(rng, H, W, size)
        if len(blob) < 4:
            continue
        inp = [[bg] * W for _ in range(H)]
        for (y, x) in blob:
            inp[y][x] = C
        out = [row[:] for row in inp]
        for r in range(H):
            for c in range(W):
                if inp[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and inp[r + dr][c + dc] != bg
                                           for dr, dc in NB):
                    out[r][c] = FENCE
        return {"input": inp, "output": out}
    bg, C = 0, 3
    inp = [[bg] * W for _ in range(H)]
    for (y, x) in ((3, 3), (3, 4), (4, 3), (4, 4)):
        inp[y][x] = C
    out = [row[:] for row in inp]
    for r in range(H):
        for c in range(W):
            if inp[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and inp[r + dr][c + dc] != bg for dr, dc in NB):
                out[r][c] = FENCE
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
