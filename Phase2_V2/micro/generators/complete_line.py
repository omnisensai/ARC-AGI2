"""Micro-primitive family: complete_line.

Two same-coloured endpoint markers, aligned on a row / column / diagonal, define
a segment. The cells strictly between them are filled with that colour. Only
background cells change.

One family, one canonical solver, many instances. Output is built directly from
the rule, independent of the solver (the gate cross-checks them).

Tiers: 0 horizontal, 6x6, bg 0, colour 2 | 1 + colour/bg, H or V | 2 + diagonal, varied size.
"""
import random

FAMILY = "complete_line"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    pts = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    (r1, c1), (r2, c2) = pts[0], pts[-1]
    col = g[r1][c1]
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    T = {}
    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        T[(r, c)] = col
        r += dr
        c += dc
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
    return "Two same-coloured endpoints define a line; fill the cells between them."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6
    else:
        H = rng.randint(6, 12); W = rng.randint(6, 12)

    if difficulty == 0:
        bg, color, orient = 0, 2, "H"
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(1, 10) if c != bg])
        orient = rng.choice(["H", "V"])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        color = rng.choice([c for c in range(0, 10) if c != bg])
        orient = rng.choice(["H", "V", "D"])

    grid = [[bg] * W for _ in range(H)]
    if orient == "H":
        r = rng.randint(0, H - 1); c1 = rng.randint(0, W - 3); c2 = rng.randint(c1 + 2, W - 1)
        p1, p2 = (r, c1), (r, c2)
    elif orient == "V":
        c = rng.randint(0, W - 1); r1 = rng.randint(0, H - 3); r2 = rng.randint(r1 + 2, H - 1)
        p1, p2 = (r1, c), (r2, c)
    else:
        sdr = rng.choice([1, -1]); sdc = rng.choice([1, -1]); L = rng.randint(2, min(H, W) - 1)
        r1 = rng.randint(0, H - 1 - L) if sdr > 0 else rng.randint(L, H - 1)
        c1 = rng.randint(0, W - 1 - L) if sdc > 0 else rng.randint(L, W - 1)
        p1, p2 = (r1, c1), (r1 + sdr * L, c1 + sdc * L)

    inp = [row[:] for row in grid]
    inp[p1[0]][p1[1]] = color; inp[p2[0]][p2[1]] = color
    out = [row[:] for row in inp]
    dr = (p2[0] > p1[0]) - (p2[0] < p1[0]); dc = (p2[1] > p1[1]) - (p2[1] < p1[1])
    r, c = p1[0] + dr, p1[1] + dc
    while (r, c) != (p2[0], p2[1]):
        out[r][c] = color; r += dr; c += dc
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
