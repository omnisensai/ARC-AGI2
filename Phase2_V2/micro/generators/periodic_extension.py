"""Micro-primitive family: periodic_extension.

In each active row, a few same-colour cells sit at periodic positions (a
contiguous run, so the gap = period). The pattern is extended: every position
congruent to the phase (mod period) in that row is filled with the colour.

Teaches period / phase / gcd spacing along a line.

Tiers: 0 one row, bg 0, period 2-3 | 1 + colour/bg, period 2-4 | 2 multiple rows,
        varied size.
"""
import random
from math import gcd

FAMILY = "periodic_extension"


def canonical_solver() -> str:
    return '''from collections import Counter
from math import gcd


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        pts = [c for c in range(W) if g[r][c] != bg]
        if len(pts) < 2:
            continue
        col = g[r][pts[0]]
        p = 0
        for i in range(len(pts) - 1):
            p = gcd(p, pts[i + 1] - pts[i])
        if p < 1:
            continue
        phase = pts[0] % p
        for c in range(W):
            if c % p == phase and g[r][c] == bg:
                T[(r, c)] = col
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
    return "Extend each row's periodic dots across the whole row."


def _fill_row(rng, W, difficulty):
    """Return (color, period, phase, present_cols) for one active row."""
    pmax = 3 if difficulty == 0 else 4
    p = rng.randint(2, pmax)
    phase = rng.randint(0, p - 1)
    positions = [c for c in range(W) if c % p == phase]
    if len(positions) < 3:
        return None
    # place a contiguous run of >=2 periodic positions (gaps all == p -> gcd p)
    run = rng.randint(2, min(len(positions), 4))
    start = rng.randint(0, len(positions) - run)
    present = positions[start:start + run]
    return p, phase, present, positions


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(8, 14); W = rng.randint(8, 14)
    bg = 0 if difficulty == 0 else rng.choice([0, 0, rng.randint(0, 9)])
    n_rows = 1 if difficulty <= 1 else rng.randint(1, 3)
    rows = rng.sample(range(H), k=min(n_rows, H))
    palette = [c for c in range(1, 10) if c != bg]

    inp = [[bg] * W for _ in range(H)]
    out = [[bg] * W for _ in range(H)]
    for r in rows:
        res = _fill_row(rng, W, difficulty)
        if res is None:
            continue
        p, phase, present, positions = res
        color = rng.choice(palette)
        for c in present:
            inp[r][c] = color
        for c in positions:
            out[r][c] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
