"""Micro-primitive family: fill_enclosed_marker.

A closed outline (one colour) sits on a background; a single isolated marker
cell (a DIFFERENT colour) sits elsewhere on the bg. The cells enclosed by the
outline — bg cells unreachable from the grid border by a 4-connected flood —
are filled with the MARKER colour (not the outline colour).

This is the natural marker-color generalisation of fill_enclosed. Same
detection idiom (border flood => "outside"; complement on bg => "inside"),
but the fill colour is provided by a separate marker cell rather than the
outline's own colour.

Tiers: 0 rect outline, bg 0 | 1 + colour/bg | 2 irregular blob outline.
"""
import random

FAMILY = "fill_enclosed_marker"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    # marker = rarest non-bg colour (a single isolated cell)
    marker_col = min(counts, key=lambda k: counts[k])
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
    T = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg and (r, c) not in outside:
                T[(r, c)] = marker_col
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
    return "Fill the enclosed cells with the marker colour (not the outline colour)."


def _solid_blob(rng, H, W):
    r0 = rng.randint(1, H - 5); r1 = rng.randint(r0 + 2, H - 3)
    c0 = rng.randint(1, W - 5); c1 = rng.randint(c0 + 2, W - 3)
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
        H = W = 9
    else:
        H = rng.randint(10, 13); W = rng.randint(10, 13)

    if difficulty == 0:
        bg, outline_col, marker_col = 0, 3, 2
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        outline_col, marker_col = rng.sample(avail, 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        outline_col, marker_col = rng.sample(avail, 2)

    if difficulty < 2:
        r0 = rng.randint(0, H - 5); r1 = rng.randint(r0 + 2, H - 2)
        c0 = rng.randint(0, W - 5); c1 = rng.randint(c0 + 2, W - 2)
        blob = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    else:
        blob = _solid_blob(rng, H, W)

    def nb4(y, x):
        return [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    outline = {(y, x) for (y, x) in blob
               if any((ny, nx) not in blob for (ny, nx) in nb4(y, x))}
    interior = blob - outline
    if not interior:
        return _instance(rng, difficulty)

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in outline:
        inp[y][x] = outline_col

    # place ONE marker cell on bg, outside the outline's bbox
    bbox_r0 = min(r for r, c in outline); bbox_r1 = max(r for r, c in outline)
    bbox_c0 = min(c for r, c in outline); bbox_c1 = max(c for r, c in outline)
    candidates = [(r, c) for r in range(H) for c in range(W)
                  if inp[r][c] == bg
                  and not (bbox_r0 - 1 <= r <= bbox_r1 + 1 and bbox_c0 - 1 <= c <= bbox_c1 + 1)]
    if not candidates:
        return _instance(rng, difficulty)
    mr, mc = rng.choice(candidates)
    inp[mr][mc] = marker_col

    out = [row[:] for row in inp]
    for (y, x) in interior:
        out[y][x] = marker_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
