"""Micro-primitive family: star_from_seed (8-armed star).

A single seed cell radiates straight rays in all 8 directions (the 4 orthogonal
AND the 4 diagonals) out to the grid edges, forming a star/asterisk of the
seed's colour. The seed is the trigger; the arms are drawn from it.

Matched pair with cross_from_seed: SAME idea with only 4 arms. Teaching the
4- vs 8-direction radiation contrast is the point of the pair.

Tiers: 0 fixed-ish, bg 0, seed 2 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "star_from_seed"
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def canonical_solver() -> str:
    return '''from collections import Counter

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    sr, sc = cells[0]; S = g[sr][sc]
    T = {}
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while 0 <= r < H and 0 <= c < W:
            if g[r][c] == bg:
                T[(r, c)] = S
            r += dr; c += dc
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
    return "The seed radiates 8 straight arms (orthogonal + diagonal) to the edges — a star."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 9
    else:
        H = rng.randint(7, 13); W = rng.randint(7, 13)
    if difficulty == 0:
        bg, color = 0, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    sr = rng.randint(1, H - 2); sc = rng.randint(1, W - 2)
    inp = [[bg] * W for _ in range(H)]
    inp[sr][sc] = color
    out = [row[:] for row in inp]
    for dr, dc in DIRS:
        r, c = sr + dr, sc + dc
        while 0 <= r < H and 0 <= c < W:
            out[r][c] = color
            r += dr; c += dc
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
