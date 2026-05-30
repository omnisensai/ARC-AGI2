"""Micro-primitive family: draw_bbox (frame the object's bounding box).

The object is a set of same-colour cells; the output draws the rectangle outline
of their bounding box (the four edges at min/max row/col) in the object's colour.
Background cells on that perimeter become the object colour; object cells stay.
Same size.

Tiers: 0 8x8, bg 0, colour 3 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "draw_bbox"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    col = g[cells[0][0]][cells[0][1]]
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    T = {}
    for c in range(c0, c1 + 1):
        if g[r0][c] == bg: T[(r0, c)] = col
        if g[r1][c] == bg: T[(r1, c)] = col
    for r in range(r0, r1 + 1):
        if g[r][c0] == bg: T[(r, c0)] = col
        if g[r][c1] == bg: T[(r, c1)] = col
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
    return "Draw the rectangle outline of the object's bounding box, in the object's colour."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13)
    if difficulty == 0:
        bg, color = 0, 3
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    for _ in range(40):
        r0 = rng.randint(0, H - 3); r1 = rng.randint(r0 + 2, H - 1)
        c0 = rng.randint(0, W - 3); c1 = rng.randint(c0 + 2, W - 1)
        inp = [[bg] * W for _ in range(H)]
        # cells touching each bbox edge so the bbox is exactly this rectangle
        inp[r0][rng.randint(c0, c1)] = color
        inp[r1][rng.randint(c0, c1)] = color
        inp[rng.randint(r0, r1)][c0] = color
        inp[rng.randint(r0, r1)][c1] = color
        for _ in range(rng.randint(0, 3)):                  # a few interior cells
            inp[rng.randint(r0, r1)][rng.randint(c0, c1)] = color
        # perimeter must add at least one cell (some perimeter cell is still bg)
        perim_bg = any(inp[r0][c] == bg or inp[r1][c] == bg for c in range(c0, c1 + 1)) \
            or any(inp[r][c0] == bg or inp[r][c1] == bg for r in range(r0, r1 + 1))
        if not perim_bg:
            continue
        out = [row[:] for row in inp]
        for c in range(c0, c1 + 1):
            out[r0][c] = color; out[r1][c] = color
        for r in range(r0, r1 + 1):
            out[r][c0] = color; out[r][c1] = color
        return {"input": inp, "output": out}
    inp = [[bg] * W for _ in range(H)]; inp[1][1] = color; inp[3][3] = color
    out = [row[:] for row in inp]
    for c in range(1, 4):
        out[1][c] = color; out[3][c] = color
    for r in range(1, 4):
        out[r][1] = color; out[r][3] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
