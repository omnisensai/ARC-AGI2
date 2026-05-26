"""Micro-primitive family: boundary_mask.

A solid filled shape is hollowed to its 1-cell outline: every interior cell
(one whose four orthogonal neighbours are all part of the shape) becomes
background; the boundary stays. Teaches contour / interior-vs-edge.

Tiers: 0 solid rectangle, bg 0, colour 3 | 1 + colour/bg | 2 + varied size,
        L / plus shapes.
"""
import random

FAMILY = "boundary_mask"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg:
                interior = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < H and 0 <= nc < W and g[nr][nc] != bg):
                        interior = False
                        break
                if interior:
                    T[(r, c)] = bg
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
    return "Hollow the shape: keep its outline, erase the interior."


def _rect(grid, r0, r1, c0, c1, color):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = color


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 9
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13)
    if difficulty == 0:
        bg, color, shape = 0, 3, "rect"
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg]); shape = "rect"
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg]); shape = rng.choice(["rect", "L", "plus"])

    inp = [[bg] * W for _ in range(H)]
    # cap the shape so the background stays the majority colour (solver uses most_common as bg)
    rh = rng.randint(3, min(5, H - 1)); rw = rng.randint(3, min(5, W - 1))
    r0 = rng.randint(0, H - rh); r1 = r0 + rh - 1
    c0 = rng.randint(0, W - rw); c1 = c0 + rw - 1
    if shape == "rect":
        _rect(inp, r0, r1, c0, c1, color)
    elif shape == "L":
        _rect(inp, r0, r1, c0, c1, color)
        # bite out a corner block
        br = rng.randint(r0 + 1, r1); bc = rng.randint(c0 + 1, c1)
        _rect(inp, br, r1, bc, c1, bg)
        if all(inp[r][c] == bg for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
            _rect(inp, r0, r1, c0, c1, color)  # safety: if fully erased, restore rect
    else:  # plus
        mr = (r0 + r1) // 2; mc = (c0 + c1) // 2
        for c in range(c0, c1 + 1):
            inp[mr][c] = color
        for r in range(r0, r1 + 1):
            inp[r][mc] = color

    out = [row[:] for row in inp]
    for r in range(H):
        for c in range(W):
            if inp[r][c] != bg:
                if all(0 <= r + dr < H and 0 <= c + dc < W and inp[r + dr][c + dc] != bg
                       for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out[r][c] = bg
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
