"""L0 family: l0_corners — mark the four grid corners.

Atom exercised: corner_cells(H, W).
Output: blank canvas (0s) with MARK=1 at (0,0), (0,W-1), (H-1,0), (H-1,W-1).
No input dependency on content — the corners are pure positional metadata.
"""
import random

FAMILY = "l0_corners"
MARK = 1


def canonical_solver() -> str:
    return '''def infer_T(g):
    H, W = len(g), len(g[0])
    T = {}
    for (r, c) in [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]:
        T[(r, c)] = 1                       # MARK
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
    return "Mark the four corner cells of the grid (1 at corners, 0 elsewhere)."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = rng.randint(4, 7)
    else:
        H = rng.randint(4, 12); W = rng.randint(4, 12)
    palette = [c for c in range(10) if c != MARK]
    bg_v = 0 if difficulty == 0 else rng.choice(palette)

    inp = [[bg_v] * W for _ in range(H)]
    # add a few decoy non-bg cells (NOT at the corners) so the input isn't trivial
    if difficulty >= 1:
        decoys = rng.randint(0, max(0, (H * W) // 6))
        non_corners = [(r, c) for r in range(H) for c in range(W)
                       if (r, c) not in {(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)}]
        for (r, c) in rng.sample(non_corners, min(decoys, len(non_corners))):
            inp[r][c] = rng.choice([x for x in palette if x != bg_v])

    out = [row[:] for row in inp]                    # apply_T = copy input + overwrite
    for (r, c) in [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]:
        out[r][c] = MARK
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
