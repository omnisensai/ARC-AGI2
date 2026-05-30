"""Micro-primitive family: fill_enclosed (any enclosing outline, not just rects).

A closed outline (one colour) sits on a background; the cells it encloses —
background cells unreachable from the grid border by a 4-connected flood — are
filled with the outline's colour. Teaches inside/outside via flood fill.

The solver floods from the border (4-connected), so it already handles ANY
closed shape; tier 2 therefore uses irregular blobs (a solid blob's 4-boundary
is the outline, its strict interior is what gets filled), not only rectangles.
This makes connectivity explicit: a 4-connected outline blocks the 4-connected
outside flood, so the interior stays enclosed.

Output built directly from the rule, independent of the solver.

Tiers: 0 rectangle, bg 0, colour 3 | 1 + colour/bg | 2 irregular blob outline.
"""
import random

FAMILY = "fill_enclosed"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    outside = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and g[r][c] == bg and (r, c) not in outside:
                outside.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and g[nr][nc] == bg and (nr, nc) not in outside:
                outside.add((nr, nc)); q.append((nr, nc))
    fill = next(g[r][c] for r in range(H) for c in range(W) if g[r][c] != bg)
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and (r, c) not in outside:
                T[(r, c)] = fill
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
    return "Fill the cells enclosed by the closed outline with its colour."


def _solid_blob(rng, H, W):
    """A solid 4-connected blob containing a base rectangle (so its strict
    interior is non-empty), optionally grown with bumps for an irregular shape."""
    r0 = rng.randint(1, H - 4); r1 = rng.randint(r0 + 2, H - 2)
    c0 = rng.randint(1, W - 4); c1 = rng.randint(c0 + 2, W - 2)
    blob = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    for _ in range(rng.randint(0, (r1 - r0 + c1 - c0))):
        y, x = rng.choice(tuple(blob))
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W:
            blob.add((ny, nx))
    return blob


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 8
    else:
        H = rng.randint(9, 13); W = rng.randint(9, 13)

    if difficulty == 0:
        bg, color = 0, 3
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(1, 10) if c != bg])
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)]); color = rng.choice([c for c in range(0, 10) if c != bg])

    if difficulty < 2:                              # plain rectangle outline
        r0 = rng.randint(0, H - 4); r1 = rng.randint(r0 + 2, H - 1)
        c0 = rng.randint(0, W - 4); c1 = rng.randint(c0 + 2, W - 1)
        blob = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    else:                                           # irregular blob outline
        blob = _solid_blob(rng, H, W)

    # the outline = blob cells with a 4-neighbour outside the blob;
    # the interior = the rest (what the flood fill must recover).
    def nb4(y, x):
        return [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    outline = {(y, x) for (y, x) in blob
               if any((ny, nx) not in blob for (ny, nx) in nb4(y, x))}
    interior = blob - outline
    if not interior:
        return _instance(rng, difficulty)           # degenerate (too thin)

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in outline:
        inp[y][x] = color
    out = [row[:] for row in inp]
    for (y, x) in interior:
        out[y][x] = color
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
