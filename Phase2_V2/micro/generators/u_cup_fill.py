"""Micro-primitive family: u_cup_fill.

An open container — two vertical walls + a bottom bar, open at the top (a "U" /
cup) — is filled to the rim with the MARKER colour (a single isolated cell of a
distinct colour placed elsewhere in the grid). Distinct from fill_enclosed:
the cup is OPEN at the top, so a flood-from-outside would leak in.

The fill colour MUST differ from the cup colour — filling with the cup's own
colour would collapse the U-cup into a solid filled rectangle, destroying its
shape identity. The marker cell is the substrate's standard way to carry a
"target colour" parameter.

Tiers: 0 fixed-ish 8x8, bg 0 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "u_cup_fill"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != bg]
    # marker = rarest non-bg colour (a single isolated cell)
    counts = Counter(v for _, _, v in nz)
    marker_col = min(counts, key=lambda k: counts[k])
    cup_cells = [(r, c) for r, c, v in nz if v != marker_col]
    if not cup_cells:
        return {}
    cup_col = next(v for _, _, v in nz if v != marker_col)
    top = min(r for r, c in cup_cells); bottom = max(r for r, c in cup_cells)
    left = min(c for r, c in cup_cells); right = max(c for r, c in cup_cells)
    T = {}
    for r in range(top, bottom):              # above the floor row
        for c in range(left + 1, right):      # between the walls
            if g[r][c] == bg:
                T[(r, c)] = marker_col
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
    return "Fill the open cup (two walls + floor) to the rim with the marker colour."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(8, 12); W = rng.randint(8, 12)
    if difficulty == 0:
        bg, cup_col, marker_col = 0, 4, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        cup_col, marker_col = rng.sample(avail, 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        cup_col, marker_col = rng.sample(avail, 2)

    # place cup with at least 2 cells of margin on the right/bottom for the marker
    left = rng.randint(0, W - 5); right = rng.randint(left + 2, W - 2)
    top = rng.randint(0, H - 5); bottom = rng.randint(top + 2, H - 2)
    inp = [[bg] * W for _ in range(H)]
    for r in range(top, bottom + 1):
        inp[r][left] = cup_col; inp[r][right] = cup_col   # walls
    for c in range(left, right + 1):
        inp[bottom][c] = cup_col                           # floor (open top)
    # place ONE marker cell on bg, well outside the cup bbox
    candidates = [(r, c) for r in range(H) for c in range(W)
                  if inp[r][c] == bg
                  and not (top - 1 <= r <= bottom + 1 and left - 1 <= c <= right + 1)]
    if not candidates:
        candidates = [(r, c) for r in range(H) for c in range(W) if inp[r][c] == bg]
    mr, mc = rng.choice(candidates)
    inp[mr][mc] = marker_col
    out = [row[:] for row in inp]
    for r in range(top, bottom):
        for c in range(left + 1, right):
            if out[r][c] == bg:
                out[r][c] = marker_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
