"""L0 family: l0_components_4 — label each 4-connected non-bg component.

Atom exercised: find_components(g, conn=4).
Output: blank canvas; each 4-connected non-bg component is recoloured to a
unique label (1, 2, 3, ...) in canonical order (sorted by min_row, then min_col
of the component). Background contract: bg = most-common.
Input cells use a single colour C chosen from a palette that EXCLUDES labels
(1..max_components_per_tier), so labels are distinguishable from input colours.
"""
import random

FAMILY = "l0_components_4"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    bv = Counter(v for row in g for v in row).most_common(1)[0][0]
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bv and not seen[r][c]:
                color = g[r][c]; comp = set(); q = deque([(r, c)]); seen[r][c] = True
                while q:
                    y, x = q.popleft(); comp.add((y, x))
                    for (ny, nx) in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == color:
                            seen[ny][nx] = True; q.append((ny, nx))
                comps.append(comp)
    comps.sort(key=lambda s: (min(r for r, _ in s), min(c for _, c in s)))
    T = {}
    for label, comp in enumerate(comps, start=1):
        for (r, c) in comp:
            T[(r, c)] = label
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
    return "Label each 4-connected non-bg component (1, 2, 3, …) in row-major order."


def _grow_blob(rng, H, W, size, taken, max_attempts=None):
    """Bounded blob growth — never spins (returns smaller if it can't reach size)."""
    free = [(r, c) for r in range(H) for c in range(W) if (r, c) not in taken]
    if not free:
        return set()
    start = rng.choice(free)
    cells = {start}
    attempts = max_attempts or (size * 60)
    for _ in range(attempts):
        if len(cells) >= size:
            break
        y, x = rng.choice(tuple(cells))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W and (ny, nx) not in cells and (ny, nx) not in taken:
            cells.add((ny, nx))
    return cells


def _instance(rng, difficulty):
    if difficulty == 0:
        H = W = 8; n_blobs = 2
    elif difficulty == 1:
        H = W = 9; n_blobs = rng.randint(2, 3)
    else:
        H = rng.randint(8, 12); W = rng.randint(8, 12); n_blobs = rng.randint(2, 4)

    palette = [c for c in range(10) if c not in range(1, n_blobs + 2)]  # labels 1..n reserved
    bg_v = 0 if difficulty == 0 else rng.choice(palette)
    fg_v = rng.choice([c for c in palette if c != bg_v])

    # place n_blobs as separate 4-connected components, with a 1-cell halo so
    # they don't accidentally merge.
    inp = [[bg_v] * W for _ in range(H)]
    taken = set()
    blobs = []
    for _ in range(n_blobs):
        size = rng.randint(2, 5)
        blob = _grow_blob(rng, H, W, size, taken)
        if not blob:
            continue
        blobs.append(blob)
        for (y, x) in blob:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    taken.add((y + dy, x + dx))
    if len(blobs) < 2:
        return _instance(rng, difficulty)

    for blob in blobs:
        for (y, x) in blob:
            inp[y][x] = fg_v

    # canonical order: sort blobs by (min_row, min_col), label 1..N
    blobs.sort(key=lambda s: (min(r for r, _ in s), min(c for _, c in s)))
    out = [row[:] for row in inp]                    # apply_T = copy input + overwrite
    for label, blob in enumerate(blobs, start=1):
        for (y, x) in blob:
            out[y][x] = label
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
