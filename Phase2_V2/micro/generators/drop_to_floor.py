"""Micro-primitive family: drop_to_floor (rigid object falls straight down).

A single rigid object (a connected blob of one colour) slides straight down,
shape preserved, until its lowest cell rests on the floor. Distinct from
gravity_water (whose cells fall and stack independently) — here the object moves
as one piece. Teaches object extraction + coordinate translation as a write mask.

(Renamed from rotate_translate: the reference is purely a downward rigid drop,
so the name now states exactly that. Direction/rotation variants are separate
families.)

Tiers: 0 small blob, bg 0, colour 5 | 1 + colour/bg | 2 + varied size/shape.
"""
import random

FAMILY = "drop_to_floor"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    if not cells:
        return {}
    delta = (H - 1) - max(r for r, c in cells)
    T = {}
    for (r, c) in cells:
        T[(r, c)] = bg                       # erase old position
    for (r, c) in cells:
        T[(r + delta, c)] = g[r][c]          # draw at new position (overrides erase)
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
    return "Drop the whole object straight down until it rests on the floor."


def _blob(rng, max_h, max_w):
    h = rng.randint(2, max_h); w = rng.randint(2, max_w)
    cells = {(0, 0)}; cur = (0, 0)
    for _ in range(h * w):
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nr, nc = cur[0] + dr, cur[1] + dc
        if 0 <= nr < h and 0 <= nc < w:
            cells.add((nr, nc)); cur = (nr, nc)
    return cells


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 9; max_h = max_w = 3
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13); max_h = max_w = 4
    if difficulty == 0:
        bg, color = 0, 5
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    rel = _blob(rng, max_h, max_w)
    oh = max(r for r, c in rel) + 1; ow = max(c for r, c in rel) + 1
    r0 = rng.randint(0, max(0, H - oh - 1))
    c0 = rng.randint(0, W - ow)
    inp = [[bg] * W for _ in range(H)]
    for (r, c) in rel:
        inp[r0 + r][c0 + c] = color
    cells = [(r0 + r, c0 + c) for (r, c) in rel]
    delta = (H - 1) - max(r for r, c in cells)
    out = [[bg] * W for _ in range(H)]
    for (r, c) in cells:
        out[r + delta][c] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
