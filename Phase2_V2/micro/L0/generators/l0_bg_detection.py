"""L0 family: l0_bg_detection — mark every non-background cell.

Atom exercised: bg(g) + nonbg_cells(g).
Output: blank canvas (0s) with MARK=1 at every cell that is non-bg in the input.
Background contract: bg = most-common colour in the input.
Mark colour: 1 (reserved; never appears in the input palette).
"""
import random

FAMILY = "l0_bg_detection"
MARK = 1


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv:
                T[(r, c)] = 1                # MARK
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
    return "Mark every non-background cell on a blank canvas (1 = non-bg, 0 = bg)."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(5, 10); W = rng.randint(5, 10)
    palette = [c for c in range(10) if c != MARK]                  # 1 is reserved for the mark
    if difficulty == 0:
        bg_v, fg_v = 0, 2
    else:
        bg_v = rng.choice(palette)
        fg_v = rng.choice([c for c in palette if c != bg_v])

    inp = [[bg_v] * W for _ in range(H)]
    n = rng.randint(max(2, (H * W) // 8), max(3, (H * W) // 3))    # keep bg as majority
    spots = rng.sample([(r, c) for r in range(H) for c in range(W)], min(n, H * W // 2))
    for (r, c) in spots:
        inp[r][c] = fg_v

    out = [row[:] for row in inp]                    # apply_T = copy input + overwrite
    for r in range(H):
        for c in range(W):
            if inp[r][c] != bg_v:
                out[r][c] = MARK
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
