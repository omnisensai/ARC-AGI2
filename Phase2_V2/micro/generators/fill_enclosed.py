"""Micro-primitive family: fill_enclosed.

A hollow rectangle outline (one colour) sits on a background. The cells enclosed
by it — background cells unreachable from the grid border — are filled with the
outline's colour. Teaches inside/outside via flood fill.

Output built directly from the rule, independent of the solver.

Tiers: 0 fixed-ish 8x8, bg 0, colour 3 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "fill_enclosed"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    outside = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and g[r][c] == bg and (r, c) not in outside:
                outside.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in outside:
                outside.add((nr, nc)); q.append((nr, nc))
    fill = next(g[r][c] for r in range(H) for c in range(W) if g[r][c] != bg)
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and (r, c) not in outside:
                T[(r, c)] = fill
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
    return "Fill the cells enclosed by the rectangle outline with its colour."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(7, 12); W = rng.randint(7, 12)

    if difficulty == 0:
        bg, color = 0, 3
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    r0 = rng.randint(0, H - 4); r1 = rng.randint(r0 + 2, H - 1)
    c0 = rng.randint(0, W - 4); c1 = rng.randint(c0 + 2, W - 1)
    inp = [[bg] * W for _ in range(H)]
    for c in range(c0, c1 + 1):
        inp[r0][c] = color; inp[r1][c] = color
    for r in range(r0, r1 + 1):
        inp[r][c0] = color; inp[r][c1] = color
    out = [row[:] for row in inp]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
