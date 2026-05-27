"""Micro-primitive family: flood_from_seed (4-connected).

A single seed cell floods the open (background) region it sits in, recolouring
every background cell 4-connected to it into the seed's colour. Walls (a second
colour) block the flood. This is the seed-as-trigger mechanic (waterfall / maze
flood) with 4-connectivity.

Matched pair with flood_from_seed_8: SAME setup, 8-connectivity — the two differ
exactly where the open region pinches to a diagonal, which is the distinction
models most often get wrong.

Tiers: 0 fixed-ish, bg 0, wall 5, seed 2 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "flood_from_seed"
CONN8 = False


def canonical_solver() -> str:
    return '''from collections import Counter, deque

NB = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = Counter(v for row in g for v in row if v != bg)
    S = min(nz, key=lambda k: nz[k])              # seed = rarest non-bg (single cell)
    sr, sc = next((r, c) for r in range(H) for c in range(W) if g[r][c] == S)
    seen = set(); q = deque()
    for dr, dc in NB:
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg:
            seen.add((nr, nc)); q.append((nr, nc))
    while q:
        r, c = q.popleft()
        for dr, dc in NB:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append((nr, nc))
    return {(r, c): S for (r, c) in seen}


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
    return "The seed floods the open region it sits in (4-connected); walls block it."


def _flood(grid, sr, sc, bg, conn8, H, W):
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if conn8:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = set(); stack = []
    for dr, dc in nb:
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == bg:
            seen.add((nr, nc)); stack.append((nr, nc))
    while stack:
        r, c = stack.pop()
        for dr, dc in nb:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and grid[nr][nc] == bg and (nr, nc) not in seen:
                seen.add((nr, nc)); stack.append((nr, nc))
    return seen


def _instance(rng, difficulty, conn8=CONN8):
    if difficulty <= 1:
        H = W = 9
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13)
    if difficulty == 0:
        bg, wall, seed = 0, 5, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        wall, seed = rng.sample([c for c in range(1, 10) if c != bg], 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        wall, seed = rng.sample([c for c in range(0, 10) if c != bg], 2)

    for _ in range(50):
        grid = [[bg] * W for _ in range(H)]
        n_walls = int(0.22 * H * W)
        for (r, c) in rng.sample([(r, c) for r in range(H) for c in range(W)], n_walls):
            grid[r][c] = wall
        opens = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == bg]
        if not opens:
            continue
        sr, sc = rng.choice(opens)
        reach = _flood(grid, sr, sc, bg, conn8, H, W)
        if reach:                                  # seed must actually flood something
            grid[sr][sc] = seed
            out = [row[:] for row in grid]
            for (r, c) in reach:
                out[r][c] = seed
            return {"input": grid, "output": out}
    # fallback: trivial open grid
    grid = [[bg] * W for _ in range(H)]
    grid[0][0] = seed
    out = [[seed] * W for _ in range(H)]
    return {"input": grid, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
