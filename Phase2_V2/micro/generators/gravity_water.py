"""Micro-primitive family: gravity_water.

Loose coloured cells fall straight down and settle at the bottom of their
column (stacking, order preserved). Teaches state transition / simulation /
movement mask (old cells -> bg, new cells -> colour).

Tiers: 0 single colour, bg 0 | 1 + colour/bg | 2 + varied size, multiple colours.
"""
import random

FAMILY = "gravity_water"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for c in range(W):
        col_vals = [g[r][c] for r in range(H)]
        items = [v for v in col_vals if v != bg]
        new = [bg] * (H - len(items)) + items
        for r in range(H):
            if new[r] != col_vals[r]:
                T[(r, c)] = new[r]
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
    return "Every loose cell falls down and stacks at the bottom of its column."


def _settle(col_vals, bg, H):
    items = [v for v in col_vals if v != bg]
    return [bg] * (H - len(items)) + items


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 9
    else:
        H = rng.randint(7, 12); W = rng.randint(7, 12)
    if difficulty == 0:
        bg, palette = 0, [2]
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = [rng.choice([c for c in range(1, 10) if c != bg])]
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = rng.sample([c for c in range(0, 10) if c != bg], k=rng.randint(1, 3))

    inp = [[bg] * W for _ in range(H)]
    n = rng.randint(max(3, H * W // 8), max(4, H * W // 4))
    spots = rng.sample([(r, c) for r in range(H) for c in range(W)], k=min(n, H * W))
    for (r, c) in spots:
        inp[r][c] = rng.choice(palette)

    out = [[bg] * W for _ in range(H)]
    for c in range(W):
        settled = _settle([inp[r][c] for r in range(H)], bg, H)
        for r in range(H):
            out[r][c] = settled[r]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
