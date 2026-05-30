"""Micro-primitive family: magnet_pair.

Two same-colour single-cell objects share a row OR a column. They slide toward
each other along that axis until they are adjacent. Final positions: the
midpoint of the original pair and the next cell (so they end up touching at
the centre of the line they originally spanned).

Asymmetric edge case: if the original gap is odd, the left/top cell ends at
floor((p1+p2)/2) and the right/bottom cell ends at floor((p1+p2)/2)+1.
This is fully determined by the two positions, so the rule has a single
canonical answer per input.

Tiers: 0 fixed 10x10, bg 0 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "magnet_pair"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if len(nz) != 2:
        return {}
    (r1, c1), (r2, c2) = sorted(nz)
    col = g[r1][c1]
    if g[r2][c2] != col:
        return {}
    T = {}
    if r1 == r2 and c2 - c1 >= 2:
        new_c1 = (c1 + c2) // 2; new_c2 = new_c1 + 1
        if c1 != new_c1: T[(r1, c1)] = bg
        if c2 != new_c2: T[(r2, c2)] = bg
        T[(r1, new_c1)] = col; T[(r2, new_c2)] = col
    elif c1 == c2 and r2 - r1 >= 2:
        new_r1 = (r1 + r2) // 2; new_r2 = new_r1 + 1
        if r1 != new_r1: T[(r1, c1)] = bg
        if r2 != new_r2: T[(r2, c2)] = bg
        T[(new_r1, c1)] = col; T[(new_r2, c2)] = col
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
    return "The two same-colour cells slide toward each other along their shared axis until they touch."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(9, 13); W = rng.randint(9, 13)

    if difficulty == 0:
        bg, col = 0, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])

    horizontal = rng.choice([True, False])
    if horizontal:
        r = rng.randint(0, H - 1)
        c1 = rng.randint(0, W - 4); c2 = rng.randint(c1 + 2, W - 1)
        p1, p2 = (r, c1), (r, c2)
    else:
        c = rng.randint(0, W - 1)
        r1 = rng.randint(0, H - 4); r2 = rng.randint(r1 + 2, H - 1)
        p1, p2 = (r1, c), (r2, c)

    inp = [[bg] * W for _ in range(H)]
    inp[p1[0]][p1[1]] = col; inp[p2[0]][p2[1]] = col
    out = [row[:] for row in inp]
    if horizontal:
        r = p1[0]; c1, c2 = p1[1], p2[1]
        new_c1 = (c1 + c2) // 2; new_c2 = new_c1 + 1
        out[r][c1] = bg; out[r][c2] = bg
        out[r][new_c1] = col; out[r][new_c2] = col
    else:
        c = p1[1]; r1, r2 = p1[0], p2[0]
        new_r1 = (r1 + r2) // 2; new_r2 = new_r1 + 1
        out[r1][c] = bg; out[r2][c] = bg
        out[new_r1][c] = col; out[new_r2][c] = col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
