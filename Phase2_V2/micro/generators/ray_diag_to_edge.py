"""Micro-primitive family: ray_diag_to_edge.

A marker at a grid CORNER shoots a diagonal ray of its colour inward, away from
that corner, until it leaves the grid. Diagonal counterpart of ray_to_edge
(edge marker -> perpendicular ray; corner marker -> diagonal ray). The corner
uniquely fixes the diagonal direction, so it is inferable from the input alone.

Tiers: 0 top-left corner, 6x6, bg 0, colour 2 | 1 any corner, varied colour/bg
        2 varied size, any corner.
"""
import random

FAMILY = "ray_diag_to_edge"


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
    while 0 <= rr < H and 0 <= cc < W:
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
    return "A corner marker shoots a diagonal ray of its colour inward to the edge."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(5, 12); W = rng.randint(5, 12)

    if difficulty == 0:
        bg, color = 0, 2; corner = (0, 0)
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(1, 10) if c != bg])
        corner = rng.choice([(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(0, 10) if c != bg])
        corner = rng.choice([(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)])

    r, c = corner
    dr = 1 if r == 0 else -1
    dc = 1 if c == 0 else -1
    grid = [[bg] * W for _ in range(H)]
    grid[r][c] = color
    inp = [row[:] for row in grid]
    rr, cc = r + dr, c + dc
    while 0 <= rr < H and 0 <= cc < W:
        grid[rr][cc] = color
        rr += dr; cc += dc
    return {"input": inp, "output": grid}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
