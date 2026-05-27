"""Micro-primitive family: symmetry_complete (reflect across V or H axis).

A shape occupies one half of the grid (left OR top); the opposite half is empty.
The output completes the grid to be mirror-symmetric across the centre axis:
each empty cell whose reflection is filled takes the reflection's colour. The
solver infers WHICH axis from which half is empty.

(Generalises the old `mirror`, which only did the vertical/left->right axis.
Vertical and horizontal are one mechanic — axis reflection — so they are one
family, the way sandwich_fill covers H/V/diagonal.)

Tiers: 0 6x6 vertical, bg 0, one colour | 1 + colour/bg | 2 vertical OR
        horizontal, varied size, multi-colour.
"""
import random

FAMILY = "symmetry_complete"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    right_empty = all(g[r][c] == bg for r in range(H) for c in range(W - W // 2, W))
    T = {}
    if right_empty:                              # vertical axis (left -> right)
        for r in range(H):
            for c in range(W):
                mc = W - 1 - c
                if g[r][c] == bg and g[r][mc] != bg:
                    T[(r, c)] = g[r][mc]
    else:                                        # horizontal axis (top -> bottom)
        for r in range(H):
            for c in range(W):
                mr = H - 1 - r
                if g[r][c] == bg and g[mr][c] != bg:
                    T[(r, c)] = g[mr][c]
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
    return "Complete the grid to be mirror-symmetric across its centre axis."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 6; axis = "V"
    else:
        axis = rng.choice(["V", "H"])
        H = rng.choice([h for h in range(6, 13) if h % 2 == 0])
        W = rng.choice([w for w in range(6, 13) if w % 2 == 0])

    if difficulty == 0:
        bg, palette = 0, [2]
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = [rng.choice([c for c in range(1, 10) if c != bg])]
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = rng.sample([c for c in range(0, 10) if c != bg], k=rng.randint(1, 3))

    inp = [[bg] * W for _ in range(H)]
    if axis == "V":
        half = W // 2
        src = [(r, c) for r in range(H) for c in range(half)]
    else:
        half = H // 2
        src = [(r, c) for r in range(half) for c in range(W)]
    n_cells = rng.randint(max(2, len(src) // 5), max(3, len(src) // 3))
    cells = rng.sample(src, k=min(n_cells, len(src)))
    # ensure the source half spans the full OTHER dimension so axis detection
    # (which half is empty) is unambiguous
    if axis == "V":
        if not any(r >= H - H // 2 for r, c in cells):
            cells.append((H - 1, rng.randrange(half)))
        if not any(r < H // 2 for r, c in cells):
            cells.append((0, rng.randrange(half)))
    else:
        if not any(c >= W - W // 2 for r, c in cells):
            cells.append((rng.randrange(half), W - 1))
        if not any(c < W // 2 for r, c in cells):
            cells.append((rng.randrange(half), 0))
    for (r, c) in cells:
        inp[r][c] = rng.choice(palette)

    out = [row[:] for row in inp]
    for r in range(H):
        for c in range(W):
            if axis == "V":
                mr, mc = r, W - 1 - c
            else:
                mr, mc = H - 1 - r, c
            if out[r][c] == bg and inp[mr][mc] != bg:
                out[r][c] = inp[mr][mc]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
