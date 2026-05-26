"""Micro-primitive family: mirror (left->right reflection).

A shape occupies the left half of the grid; the right half is empty. The output
completes the grid to be left-right symmetric: each empty cell whose horizontal
mirror is filled takes the mirror's colour.

Teaches axis reflection / copy mask. (Vertical centre axis for the reference
family; horizontal/other axes are a later extension.)

Tiers: 0 6x6, bg 0, one colour | 1 + colour/bg | 2 + varied size, multi-colour shape.
"""
import random

FAMILY = "mirror"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            mc = W - 1 - c
            if g[r][c] == bg and g[r][mc] != bg:
                T[(r, c)] = g[r][mc]
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
    return "Reflect the left-half shape across the vertical centre into the empty right half."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(6, 12); W = rng.choice([w for w in range(6, 13) if w % 2 == 0])

    if difficulty == 0:
        bg, palette = 0, [2]
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = [rng.choice([c for c in range(1, 10) if c != bg])]
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = rng.sample([c for c in range(0, 10) if c != bg], k=rng.randint(1, 3))

    half = W // 2
    inp = [[bg] * W for _ in range(H)]
    # draw a random shape strictly in the left half
    n_cells = rng.randint(max(2, (H * half) // 5), max(3, (H * half) // 3))
    cells = rng.sample([(r, c) for r in range(H) for c in range(half)], k=min(n_cells, H * half))
    for (r, c) in cells:
        inp[r][c] = rng.choice(palette)

    out = [row[:] for row in inp]
    for r in range(H):
        for c in range(W):
            mc = W - 1 - c
            if out[r][c] == bg and inp[r][mc] != bg:
                out[r][c] = inp[r][mc]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
