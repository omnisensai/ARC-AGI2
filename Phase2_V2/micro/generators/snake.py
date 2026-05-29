"""Micro-primitive family: snake.

Several same-colour seed cells (3 or 4) sit at arbitrary positions on the grid.
Rule: connect them in (row, col)-sorted order with axis-aligned Manhattan
L-paths. Each consecutive pair (p_i, p_{i+1}) is connected by going horizontally
first to p_{i+1}'s column, then vertically to p_{i+1}'s row. The path cells
take the seed colour.

Equivalent to applying manhattan_path to consecutive seed pairs in sorted
order. Produces a "snake-like" polyline through the seeds.

Tiers: 0 fixed 11x11, 3 seeds, bg 0, colour 4 | 1 + colour/bg, 3-4 seeds
       | 2 + varied size, 4 seeds.
"""
import random

FAMILY = "snake"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seeds = sorted((r, c) for r in range(H) for c in range(W) if g[r][c] != bg)
    if len(seeds) < 2:
        return {}
    col = g[seeds[0][0]][seeds[0][1]]
    if any(g[r][c] != col for r, c in seeds):
        return {}
    T = {}
    for i in range(len(seeds) - 1):
        r1, c1 = seeds[i]; r2, c2 = seeds[i + 1]
        # horizontal then vertical from (r1, c1) to (r2, c2)
        step_c = 1 if c2 > c1 else (-1 if c2 < c1 else 0)
        if step_c:
            for c in range(c1 + step_c, c2 + step_c, step_c):
                if (r1, c) not in set(seeds) and (r1, c) not in T:
                    T[(r1, c)] = col
                elif (r1, c) in set(seeds):
                    pass  # already this colour
        step_r = 1 if r2 > r1 else (-1 if r2 < r1 else 0)
        if step_r:
            for r in range(r1 + step_r, r2 + step_r, step_r):
                if (r, c2) not in set(seeds) and (r, c2) not in T:
                    T[(r, c2)] = col
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
    return ("Connect the same-colour seeds in (row, col) order with L-shaped "
            "axis-aligned paths (horizontal then vertical) through the seeds.")


def _instance(rng, difficulty):
    if difficulty == 0:
        H = W = 11
        n_seeds = 3
        bg, col = 0, 4
    elif difficulty == 1:
        H = W = 11
        n_seeds = rng.randint(3, 4)
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])
    else:
        H = rng.randint(11, 14); W = rng.randint(11, 14)
        n_seeds = 4
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])

    # Place seeds at random positions (all distinct).
    for _ in range(50):
        positions = set()
        while len(positions) < n_seeds:
            positions.add((rng.randint(0, H - 1), rng.randint(0, W - 1)))
        seeds = sorted(positions)
        # Avoid two seeds at the same row AND same col (impossible by uniqueness),
        # but also require that the polyline visits all seeds without collapsing
        # (consecutive seeds must differ in at least one coord -> always true).
        break

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in seeds:
        inp[y][x] = col

    out = [row[:] for row in inp]
    seeds_set = set(seeds)
    for i in range(len(seeds) - 1):
        r1, c1 = seeds[i]; r2, c2 = seeds[i + 1]
        step_c = 1 if c2 > c1 else (-1 if c2 < c1 else 0)
        if step_c:
            for c in range(c1 + step_c, c2 + step_c, step_c):
                if (r1, c) not in seeds_set:
                    out[r1][c] = col
        step_r = 1 if r2 > r1 else (-1 if r2 < r1 else 0)
        if step_r:
            for r in range(r1 + step_r, r2 + step_r, step_r):
                if (r, c2) not in seeds_set:
                    out[r][c2] = col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
