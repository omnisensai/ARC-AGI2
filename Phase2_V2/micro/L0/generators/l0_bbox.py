"""L0 family: l0_bbox — mark the bounding-box perimeter of the non-bg cells.

Atom exercised: bbox(nonbg_cells(g)).
Output: blank canvas (0s) with MARK=1 along the 4 edges of the bbox
(top row, bottom row, left col, right col of the bbox — INCLUDING the corners).
Background contract: bg = most-common.
"""
import random

FAMILY = "l0_bbox"
MARK = 1


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] != bv]
    T = {}
    if not cells:
        return T
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs); c0, c1 = min(cs), max(cs)
    for c in range(c0, c1 + 1):
        T[(r0, c)] = 1; T[(r1, c)] = 1        # top + bottom edges
    for r in range(r0, r1 + 1):
        T[(r, c0)] = 1; T[(r, c1)] = 1        # left + right edges
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
    return "Mark the perimeter of the non-background cells' bounding box on a blank canvas."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(7, 12); W = rng.randint(7, 12)
    palette = [c for c in range(10) if c != MARK]
    if difficulty == 0:
        bg_v, fg_v = 0, 3
    else:
        bg_v = rng.choice(palette)
        fg_v = rng.choice([c for c in palette if c != bg_v])

    # pick a bbox; ensure non-trivial dims so the perimeter is meaningful
    r0 = rng.randint(0, H - 3); r1 = rng.randint(r0 + 2, H - 1)
    c0 = rng.randint(0, W - 3); c1 = rng.randint(c0 + 2, W - 1)

    inp = [[bg_v] * W for _ in range(H)]
    # force the bbox to be exactly this rectangle: a cell on each of its 4 edges
    inp[r0][rng.randint(c0, c1)] = fg_v
    inp[r1][rng.randint(c0, c1)] = fg_v
    inp[rng.randint(r0, r1)][c0] = fg_v
    inp[rng.randint(r0, r1)][c1] = fg_v
    # plus some optional interior cells
    for _ in range(rng.randint(0, 3)):
        inp[rng.randint(r0, r1)][rng.randint(c0, c1)] = fg_v

    out = [row[:] for row in inp]                    # apply_T = copy input + overwrite
    for c in range(c0, c1 + 1):
        out[r0][c] = MARK; out[r1][c] = MARK
    for r in range(r0, r1 + 1):
        out[r][c0] = MARK; out[r][c1] = MARK
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
