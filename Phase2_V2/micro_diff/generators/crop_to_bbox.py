"""Diff-size micro family: crop_to_bbox.

Output = the tight bounding box of the non-background content (cropped out of a
larger grid). Output dimensions differ from the input — geometry is inferred
from the input content (the bbox).

Diff-size contract (gather style):
    def solve(g):
        T = infer_T(g)        # output geometry: crop window (r0, c0, h, w)
        return apply_T(g, T)  # build a fresh h x w grid, gather from g

apply_T constructs the output rather than overwriting a copy of the input — the
per-cell '.'/digit diff-map does not apply when sizes differ.

Tiers: 0 fixed-ish, bg 0 | 1 + colour/bg | 2 + varied size/position.
"""
import random

FAMILY = "crop_to_bbox"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bg]
    r0 = min(r for r, c in cells); r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells); c1 = max(c for r, c in cells)
    return {"r0": r0, "c0": c0, "h": r1 - r0 + 1, "w": c1 - c0 + 1}


def apply_T(g, T):
    return [[g[T["r0"] + r][T["c0"] + c] for c in range(T["w"])]
            for r in range(T["h"])]


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
'''


def family_prompt_hint() -> str:
    return "Crop the grid to the bounding box of the non-background content."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12
    else:
        H = rng.randint(10, 16); W = rng.randint(10, 16)
    if difficulty == 0:
        bg, palette = 0, [3]
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = [rng.choice([c for c in range(1, 10) if c != bg])]
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); palette = rng.sample([c for c in range(0, 10) if c != bg], k=rng.randint(1, 3))

    sh = rng.randint(2, H - 2); sw = rng.randint(2, W - 2)   # strictly smaller -> diff-size
    r0 = rng.randint(0, H - sh); c0 = rng.randint(0, W - sw)
    inp = [[bg] * W for _ in range(H)]
    # force the 4 window corners so the bbox is exactly the window
    for (r, c) in ((r0, c0), (r0, c0 + sw - 1), (r0 + sh - 1, c0), (r0 + sh - 1, c0 + sw - 1)):
        inp[r][c] = rng.choice(palette)
    # random interior content
    for r in range(r0, r0 + sh):
        for c in range(c0, c0 + sw):
            if rng.random() < 0.4:
                inp[r][c] = rng.choice(palette)
    out = [[inp[r0 + r][c0 + c] for c in range(sw)] for r in range(sh)]
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
