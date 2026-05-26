"""Micro-primitive family: u_cup_fill.

An open container — two vertical walls + a bottom bar, open at the top (a "U" /
cup) — is filled to the rim with its own colour. Distinct from fill_enclosed:
the cup is OPEN at the top, so a flood-from-outside would leak in; the fill is
the cup's bounding interior above the floor.

Tiers: 0 fixed-ish 8x8, bg 0, colour 4 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "u_cup_fill"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    col = g[cells[0][0]][cells[0][1]]
    top = min(r for r, c in cells); bottom = max(r for r, c in cells)
    left = min(c for r, c in cells); right = max(c for r, c in cells)
    T = {}
    for r in range(top, bottom):              # above the floor row
        for c in range(left + 1, right):      # between the walls
            if g[r][c] == bg:
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
    return "Fill the open cup (two walls + floor) to the rim with its colour."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(7, 12); W = rng.randint(7, 12)
    if difficulty == 0:
        bg, color = 0, 4
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    left = rng.randint(0, W - 4); right = rng.randint(left + 2, W - 1)
    top = rng.randint(0, H - 4); bottom = rng.randint(top + 2, H - 1)
    inp = [[bg] * W for _ in range(H)]
    for r in range(top, bottom + 1):
        inp[r][left] = color; inp[r][right] = color    # walls
    for c in range(left, right + 1):
        inp[bottom][c] = color                          # floor (open top)
    out = [row[:] for row in inp]
    for r in range(top, bottom):
        for c in range(left + 1, right):
            out[r][c] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
