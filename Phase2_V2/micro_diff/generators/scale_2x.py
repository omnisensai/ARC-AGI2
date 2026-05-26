"""Diff-size micro family: scale_2x.

Output = the input upscaled 2x in each dimension (every cell becomes a 2x2
block). Output dimensions = 2H x 2W. Geometry is a rule (x2) learned from the
pairs; content is a gather: output[r][c] = input[r//2][c//2].

Diff-size contract (gather style):
    def solve(g):
        T = infer_T(g)        # output geometry: (h, w) = (2H, 2W)
        return apply_T(g, T)  # build fresh h x w grid, gather from g

Tiers: 0 small fixed-ish grid | 1 + varied colours | 2 + varied size.
"""
import random

FAMILY = "scale_2x"


def canonical_solver() -> str:
    return '''def infer_T(g):
    H, W = len(g), len(g[0])
    return {"h": 2 * H, "w": 2 * W}


def apply_T(g, T):
    return [[g[r // 2][c // 2] for c in range(T["w"])] for r in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
'''


def family_prompt_hint() -> str:
    return "Upscale the grid 2x: every cell becomes a 2x2 block."


def _instance(rng, difficulty):
    if difficulty == 0:
        H = W = 3; palette = [0, 2]
    elif difficulty == 1:
        H = W = rng.randint(3, 5); palette = [0] + rng.sample(range(1, 10), k=rng.randint(1, 3))
    else:
        H = rng.randint(3, 7); W = rng.randint(3, 7); palette = [0] + rng.sample(range(1, 10), k=rng.randint(1, 4))

    inp = [[rng.choice(palette) for _ in range(W)] for _ in range(H)]
    out = [[inp[r // 2][c // 2] for c in range(2 * W)] for r in range(2 * H)]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
