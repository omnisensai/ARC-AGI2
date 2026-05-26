"""Micro-primitive family: periodic_repair.

A doubly-periodic tiled pattern (colours 1-9, period pr x pc) has some cells
punched out to holes (colour 0). Each hole is restored to the value its residue
class (r % pr, c % pc) should hold, recovered by consensus from the surviving
cells. Teaches template inference / consensus / noise removal.

The generator guarantees every residue class keeps >=1 survivor, so every hole
is recoverable.

Tiers: 0 period 2x2, bg holes | 1 period up to 3x3, more colours | 2 varied size/reps.
"""
import random

FAMILY = "periodic_repair"


def canonical_solver() -> str:
    return '''def infer_T(g):
    H, W = len(g), len(g[0])

    def consistent(pr, pc):
        seen = {}
        for r in range(H):
            for c in range(W):
                v = g[r][c]
                if v == 0:
                    continue
                k = (r % pr, c % pc)
                if k in seen and seen[k] != v:
                    return False
                seen[k] = v
        return True

    pr = pc = None
    for a in range(1, H + 1):
        done = False
        for b in range(1, W + 1):
            if consistent(a, b):
                pr, pc = a, b; done = True; break
        if done:
            break
    template = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != 0:
                template[(r % pr, c % pc)] = g[r][c]
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0:
                k = (r % pr, c % pc)
                if k in template:
                    T[(r, c)] = template[k]
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
    return "Repair the holes (0) using the repeating tile's consensus value."


def _instance(rng, difficulty):
    if difficulty == 0:
        pr = pc = 2; reps_r = rng.randint(3, 4); reps_c = rng.randint(3, 4); npal = 2
    elif difficulty == 1:
        pr = rng.choice([2, 3]); pc = rng.choice([2, 3]); reps_r = rng.randint(2, 4); reps_c = rng.randint(2, 4); npal = 3
    else:
        pr = rng.choice([2, 3]); pc = rng.choice([2, 3, 4]); reps_r = rng.randint(2, 4); reps_c = rng.randint(2, 4); npal = rng.randint(2, 4)

    H, W = pr * reps_r, pc * reps_c
    palette = rng.sample(range(1, 10), k=npal)
    tile = [[rng.choice(palette) for _ in range(pc)] for _ in range(pr)]
    full = [[tile[r % pr][c % pc] for c in range(W)] for r in range(H)]
    out = [row[:] for row in full]
    inp = [row[:] for row in full]

    kept = {(r % pr, c % pc): reps_r * reps_c for r in range(pr) for c in range(pc)}
    cells = [(r, c) for r in range(H) for c in range(W)]
    rng.shuffle(cells)
    target_holes = int(0.15 * H * W)
    holed = 0
    for (r, c) in cells:
        if holed >= target_holes:
            break
        k = (r % pr, c % pc)
        if kept[k] > 1:                 # keep >=1 survivor per class
            inp[r][c] = 0; kept[k] -= 1; holed += 1
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
