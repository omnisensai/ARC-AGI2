"""Micro-primitive family: ray_diag_until_blocker.

A corner marker shoots a diagonal ray of its colour inward, but STOPS one cell
before an interior blocker (a non-background cell of a different colour). With no
blocker, the ray runs to the edge. Diagonal counterpart of ray_until_blocker.

The marker is the corner cell; the blocker is strictly interior, so they are
never confused.

Tiers: 0 top-left corner, blocker present, bg 0 | 1 + colour/bg | 2 + any corner
        / size, sometimes no blocker.
"""
import random

FAMILY = "ray_diag_until_blocker"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    dirs = {(0, 0): (1, 1), (0, W - 1): (1, -1),
            (H - 1, 0): (-1, 1), (H - 1, W - 1): (-1, -1)}
    r, c = next((p for p in dirs if g[p[0]][p[1]] != bg))
    col = g[r][c]
    dr, dc = dirs[(r, c)]
    T = {}
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W and g[rr][cc] == bg:
        T[(rr, cc)] = col
        rr += dr
        cc += dc
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
    return "A corner marker shoots a diagonal ray inward, stopping just before any blocker."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(6, 12); W = rng.randint(6, 12)

    if difficulty == 0:
        bg, color = 0, 2; corner = (0, 0); has_blocker = True
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(1, 10) if c != bg])
        corner = rng.choice([(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]); has_blocker = True
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(0, 10) if c != bg])
        corner = rng.choice([(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]); has_blocker = rng.random() < 0.7
    blk = rng.choice([c for c in range(0, 10) if c not in (bg, color)])

    r, c = corner
    dr = 1 if r == 0 else -1
    dc = 1 if c == 0 else -1
    grid = [[bg] * W for _ in range(H)]
    grid[r][c] = color

    path = []
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W:
        path.append((rr, cc)); rr += dr; cc += dc
    interior = [p for p in path if 0 < p[0] < H - 1 and 0 < p[1] < W - 1]

    blocker_at = None
    if has_blocker and interior:
        blocker_at = rng.choice(interior)
        grid[blocker_at[0]][blocker_at[1]] = blk

    inp = [row[:] for row in grid]
    out = [row[:] for row in grid]
    for p in path:
        if p == blocker_at:
            break
        out[p[0]][p[1]] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
