"""Micro-primitive family: fence_4conn (orthogonal-only fence — rounded corners).

A shape (an irregular blob of colour C) is fenced, but only background cells
4-adjacent to the shape (orthogonal only) are painted the fence colour. The
diagonal-corner cells are NOT fenced, so the fence is OPEN at every convex
corner (rounded). The fence colour is named by a single seed/marker pixel.

Matched pair with fence_8conn: the 8-connected fence also paints the diagonal
corners, closing the ring into a square. This is the exact 4-vs-8 distinction
where corner-rounding bugs live.

Tiers: 0 fixed-ish, bg 0, shape 3, fence 4 | 1 + colour/bg | 2 + varied size/shape.
"""
import random

FAMILY = "fence_4conn"
NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def canonical_solver() -> str:
    return '''from collections import Counter

NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    F = min(nz, key=lambda k: nz[k])          # fence colour = rarest non-bg (seed marker)
    C = max(nz, key=lambda k: nz[k])          # shape colour = most common non-bg
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and g[r + dr][c + dc] == C
                                     for dr, dc in NB):
                T[(r, c)] = F
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
    return "Fence the shape: paint only the cells 4-adjacent to it (no diagonals) the marker colour — open corners."


def _blob(rng, H, W, size):
    cells = {(rng.randint(2, H - 3), rng.randint(2, W - 3))}
    for _ in range(size * 60):
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 2 <= ny < H - 2 and 2 <= nx < W - 2 and (ny, nx) not in cells:
            cells.add((ny, nx))
    return cells


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(10, 15); W = rng.randint(10, 15)
    if difficulty == 0:
        bg, C, F = 0, 3, 4; size = 6
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, F = rng.sample([c for c in range(1, 10) if c != bg], 2); size = rng.randint(5, 9)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); C, F = rng.sample([c for c in range(0, 10) if c != bg], 2); size = rng.randint(5, 12)

    for _ in range(60):
        blob = _blob(rng, H, W, size)
        if len(blob) < 4:
            continue
        forbid = {(y + dy, x + dx) for (y, x) in blob for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)}
        free = [(r, c) for r in range(H) for c in range(W) if (r, c) not in forbid]
        if not free:
            continue
        mr, mc = rng.choice(free)
        inp = [[bg] * W for _ in range(H)]
        for (y, x) in blob:
            inp[y][x] = C
        inp[mr][mc] = F
        out = [row[:] for row in inp]
        for r in range(H):
            for c in range(W):
                if inp[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and inp[r + dr][c + dc] == C
                                           for dr, dc in NB):
                    out[r][c] = F
        return {"input": inp, "output": out}
    bg, C, F = 0, 3, 4
    inp = [[bg] * W for _ in range(H)]
    for (y, x) in ((3, 3), (3, 4), (4, 3), (4, 4)):
        inp[y][x] = C
    inp[0][0] = F
    out = [row[:] for row in inp]
    for r in range(H):
        for c in range(W):
            if inp[r][c] == bg and any(0 <= r + dr < H and 0 <= c + dc < W and inp[r + dr][c + dc] == C for dr, dc in NB):
                out[r][c] = F
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
