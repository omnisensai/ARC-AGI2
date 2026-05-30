"""Micro-primitive family: manhattan_path.

Two same-colour cells (endpoints), NOT collinear in any axis. Draw an L-shaped
axis-aligned path connecting them. The path canonical form: from the top-left
endpoint, go horizontally to align with the other's column, then vertically
to reach it. (Sorting the endpoints by (row, col) makes the corner choice
deterministic.) Path cells take the endpoint colour.

Complement to complete_line / sandwich_fill which require collinearity.

Tiers: 0 fixed 10x10, bg 0, colour 2 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "manhattan_path"


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    nz = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != bg]
    if len(nz) != 2:
        return {}
    (r1, c1, _), (r2, c2, _) = nz
    col = nz[0][2]
    if r1 == r2 or c1 == c2:
        return {}  # collinear -> not this family's rule
    # Sort endpoints: A = (smaller row, tiebreak smaller col)
    if (r1, c1) > (r2, c2):
        r1, c1, r2, c2 = r2, c2, r1, c1
    # L: horizontal from (r1, c1) -> (r1, c2), then vertical to (r2, c2).
    T = {}
    step_c = 1 if c2 > c1 else -1
    for c in range(c1 + step_c, c2 + step_c, step_c):
        T[(r1, c)] = col
    step_r = 1 if r2 > r1 else -1
    for r in range(r1 + step_r, r2 + step_r, step_r):
        T[(r, c2)] = col
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
    return "Draw an L-shaped path (horizontal then vertical) between the two same-colour cells."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 10
    else:
        H = rng.randint(8, 13); W = rng.randint(8, 13)

    if difficulty == 0:
        bg, col = 0, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        col = rng.choice([c for c in range(10) if c != bg])

    # Pick two non-collinear endpoints
    for _ in range(50):
        r1 = rng.randint(0, H - 1); c1 = rng.randint(0, W - 1)
        r2 = rng.randint(0, H - 1); c2 = rng.randint(0, W - 1)
        if r1 != r2 and c1 != c2:
            break
    else:
        return _instance(rng, difficulty)

    inp = [[bg] * W for _ in range(H)]
    inp[r1][c1] = col; inp[r2][c2] = col

    out = [row[:] for row in inp]
    # Same logic as solver to build the canonical path.
    a, b = sorted([(r1, c1), (r2, c2)])
    (ar, ac), (br, bc) = a, b
    step_c = 1 if bc > ac else -1
    for c in range(ac + step_c, bc + step_c, step_c):
        out[ar][c] = col
    step_r = 1 if br > ar else -1
    for r in range(ar + step_r, br + step_r, step_r):
        out[r][bc] = col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
