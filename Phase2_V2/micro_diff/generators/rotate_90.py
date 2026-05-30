"""Diff-size micro family: rotate_90 (rotate the whole grid 90 deg clockwise).

Output[i][j] = input[H-1-j][i]; output dimensions are W x H (the input's
dimensions swapped), so this is a SIZE-CHANGING geometry transform — it lives in
the diff-size class. Pure gather, no new colours.

Inputs are non-square (H != W) so the rotation always changes the dimensions.

Tiers: 0 small non-square | 1 + varied colours | 2 + varied size.
"""
import random

FAMILY = "rotate_90"


def canonical_solver() -> str:
    return '''def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": W, "w": H}                       # dims swap


def apply_T(g, T):
    H = len(g)
    return [[g[H - 1 - j][i] for j in range(T["w"])] for i in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
'''


def family_prompt_hint() -> str:
    return "Rotate the whole grid 90 degrees clockwise (dimensions swap)."


def _instance(rng, difficulty):
    if difficulty == 0:
        H, W = 3, 4; palette = [0, 2]
    elif difficulty == 1:
        H, W = rng.sample([3, 4, 5, 6], 2); palette = [0] + rng.sample(range(1, 10), k=rng.randint(1, 3))
    else:
        H, W = rng.sample([3, 4, 5, 6, 7], 2); palette = [0] + rng.sample(range(1, 10), k=rng.randint(1, 4))

    inp = [[rng.choice(palette) for _ in range(W)] for _ in range(H)]
    out = [[inp[H - 1 - j][i] for j in range(H)] for i in range(W)]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
