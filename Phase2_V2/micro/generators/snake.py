"""Micro-primitive family: snake.

Several same-colour seed cells (3 or 4) sit at arbitrary positions on the grid.
Rule: connect them in (row, col)-sorted order with 8-CONNECTED chebyshev-style
paths. Each consecutive pair (p_i, p_{i+1}) is connected by a path that takes
diagonal steps first (until aligned with p_{i+1} on one axis) then axis-aligned
steps to reach p_{i+1}. The path cells take the seed colour.

8-conn distinguishes this from manhattan_path / complete_line / connect_centroids,
all of which only emit axis-aligned segments.

Tiers: 0 fixed 11x11, 3 seeds, bg 0, colour 4 | 1 + colour/bg, 3-4 seeds
       | 2 + varied size, 4 seeds.
"""
import random

FAMILY = "snake"


def canonical_solver() -> str:
    return '''from collections import Counter


def _path_8conn(p1, p2):
    """8-conn path from p1 to p2 (exclusive of p1, inclusive of p2):
    diagonal steps first, then axis-aligned for the remainder."""
    r, c = p1
    r2, c2 = p2
    dr = (r2 > r) - (r2 < r)
    dc = (c2 > c) - (c2 < c)
    path = []
    while r != r2 and c != c2:
        r += dr; c += dc
        path.append((r, c))
    while r != r2:
        r += dr
        path.append((r, c))
    while c != c2:
        c += dc
        path.append((r, c))
    return path


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    seeds = sorted((r, c) for r in range(H) for c in range(W) if g[r][c] != bg)
    if len(seeds) < 2:
        return {}
    col = g[seeds[0][0]][seeds[0][1]]
    if any(g[r][c] != col for r, c in seeds):
        return {}
    seeds_set = set(seeds)
    T = {}
    for i in range(len(seeds) - 1):
        for cell in _path_8conn(seeds[i], seeds[i + 1]):
            if cell not in seeds_set and cell not in T:
                T[cell] = col
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
    return ("Connect the same-colour seeds in (row, col) order with 8-conn "
            "chebyshev paths: diagonals first, then axis-aligned to reach.")


def _path_8conn(p1, p2):
    r, c = p1
    r2, c2 = p2
    dr = (r2 > r) - (r2 < r)
    dc = (c2 > c) - (c2 < c)
    path = []
    while r != r2 and c != c2:
        r += dr; c += dc
        path.append((r, c))
    while r != r2:
        r += dr
        path.append((r, c))
    while c != c2:
        c += dc
        path.append((r, c))
    return path


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

    for _ in range(50):
        positions = set()
        while len(positions) < n_seeds:
            positions.add((rng.randint(0, H - 1), rng.randint(0, W - 1)))
        seeds = sorted(positions)
        break

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in seeds:
        inp[y][x] = col

    out = [row[:] for row in inp]
    seeds_set = set(seeds)
    for i in range(len(seeds) - 1):
        for cell in _path_8conn(seeds[i], seeds[i + 1]):
            if cell not in seeds_set:
                out[cell[0]][cell[1]] = col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
