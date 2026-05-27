"""Micro-primitive family: flip_vertical (mirror the WHOLE grid top<->bottom).

The output is the input reflected across the horizontal axis: output[r][c] =
input[H-1-r][c]. Whole-grid geometry transform (distinct from
symmetry_complete_*). Same size.

Tiers: 0 6x6, bg 0, one colour | 1 + colour/bg | 2 + varied size, multi-colour.
"""
import random

FAMILY = "flip_vertical"


def canonical_solver() -> str:
    return '''def infer_T(g):
    H, W = len(g), len(g[0])
    T = {}
    for r in range(H):
        for c in range(W):
            mr = H - 1 - r
            if g[r][c] != g[mr][c]:
                T[(r, c)] = g[mr][c]
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
    return "Mirror the whole grid top-to-bottom."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(5, 11); W = rng.randint(5, 11)
    if difficulty == 0:
        bg, palette = 0, [3]
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = [rng.choice([c for c in range(1, 10) if c != bg])]
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = rng.sample([c for c in range(0, 10) if c != bg], k=rng.randint(1, 3))

    for _ in range(40):
        inp = [[bg] * W for _ in range(H)]
        n = rng.randint(max(3, H * W // 6), max(4, H * W // 3))
        for (r, c) in rng.sample([(r, c) for r in range(H) for c in range(W)], min(n, H * W)):
            inp[r][c] = rng.choice(palette)
        out = inp[::-1]
        if out != inp:                       # must be asymmetric, else flip is a no-op
            return {"input": inp, "output": [row[:] for row in out]}
    inp = [[bg] * W for _ in range(H)]; inp[0][0] = palette[0]
    return {"input": inp, "output": [row[:] for row in inp[::-1]]}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
