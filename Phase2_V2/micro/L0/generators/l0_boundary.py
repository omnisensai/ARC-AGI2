"""L0 family: l0_boundary — mark the 4-boundary of the non-bg cells.

Atom exercised: boundary_of(nonbg_cells(g), conn=4).
Output: blank canvas with MARK=1 at every non-bg cell that has at least one
4-neighbour OUTSIDE the non-bg set (grid edges count as outside).
Background contract: bg = most-common.
"""
import random

FAMILY = "l0_boundary"
MARK = 1


def canonical_solver() -> str:
    return '''from collections import Counter


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    cells = {(r, c) for r in range(H) for c in range(W) if g[r][c] != bv}
    T = {}
    for (r, c) in cells:
        for (nr, nc) in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in cells:
                T[(r, c)] = 1                # MARK — this cell is on the 4-boundary
                break
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
    return "Mark the 4-connected boundary of the non-background cells (1 = boundary, 0 = bg or interior)."


def _grow_blob(rng, H, W, size):
    cells = {(rng.randint(1, H - 2), rng.randint(1, W - 2))}
    for _ in range(size * 60):
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 1 <= ny < H - 1 and 1 <= nx < W - 1 and (ny, nx) not in cells:
            cells.add((ny, nx))
    return cells


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(8, 12); W = rng.randint(8, 12)
    palette = [c for c in range(10) if c != MARK]
    if difficulty == 0:
        bg_v, fg_v = 0, 3
    else:
        bg_v = rng.choice(palette)
        fg_v = rng.choice([c for c in palette if c != bg_v])

    size = rng.randint(5, min(12, H * W // 3))
    blob = _grow_blob(rng, H, W, size)
    if len(blob) < 4:
        return _instance(rng, difficulty)

    inp = [[bg_v] * W for _ in range(H)]
    for (y, x) in blob:
        inp[y][x] = fg_v

    out = [row[:] for row in inp]                    # apply_T = copy input + overwrite
    for (r, c) in blob:
        for (nr, nc) in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if not (0 <= nr < H and 0 <= nc < W) or (nr, nc) not in blob:
                out[r][c] = MARK
                break
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
