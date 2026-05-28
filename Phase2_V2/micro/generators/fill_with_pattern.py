"""Micro-primitive family: fill_with_pattern.

A closed outline (one colour C1) + a single isolated marker cell elsewhere
(colour C2). The cavity's interior (bg cells unreachable from the border by a
4-conn flood) is filled with a checkerboard pattern of C1/C2: parity
((r + c) % 2) decides which colour each interior cell gets. The top-left
interior cell takes C1 (so the checkerboard "starts" from the outline colour).

This is the "pattern" complement to fill_enclosed_marker (which fills solid
with the marker colour); here the fill is a 2-colour structured pattern.

Tiers: 0 fixed 11x11, bg 0 | 1 + colour/bg | 2 + varied size.
"""
import random

FAMILY = "fill_with_pattern"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    # marker = rarest non-bg colour; outline = the other non-bg colour
    if len(counts) < 2:
        return {}
    marker_col = min(counts, key=lambda k: counts[k])
    outline_col = next(c for c in counts if c != marker_col)

    # Border flood -> "outside"
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
    interior = [(r, c) for r in range(H) for c in range(W)
                if g[r][c] == bg and (r, c) not in outside]
    if not interior:
        return {}
    # Anchor parity: top-left interior cell becomes outline_col.
    r0 = min(r for r, c in interior); c0 = min(c for r, c in interior if r == r0)
    anchor_parity = (r0 + c0) % 2
    T = {}
    for (r, c) in interior:
        T[(r, c)] = outline_col if (r + c) % 2 == anchor_parity else marker_col
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
    return "Fill the enclosed cells with a checkerboard of the outline and marker colours."


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 11
    else:
        H = rng.randint(11, 14); W = rng.randint(11, 14)

    if difficulty == 0:
        bg, outline_col, marker_col = 0, 3, 8
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        outline_col, marker_col = rng.sample(avail, 2)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        outline_col, marker_col = rng.sample(avail, 2)

    # Rectangle outline with non-empty interior.
    r0 = rng.randint(0, H - 6); r1 = rng.randint(r0 + 3, H - 3)
    c0 = rng.randint(0, W - 6); c1 = rng.randint(c0 + 3, W - 3)
    inp = [[bg] * W for _ in range(H)]
    for r in range(r0, r1 + 1):
        inp[r][c0] = outline_col; inp[r][c1] = outline_col
    for c in range(c0, c1 + 1):
        inp[r0][c] = outline_col; inp[r1][c] = outline_col

    # Marker cell on bg, outside the outline bbox.
    candidates = [(r, c) for r in range(H) for c in range(W)
                  if inp[r][c] == bg
                  and not (r0 - 1 <= r <= r1 + 1 and c0 - 1 <= c <= c1 + 1)]
    if not candidates:
        return _instance(rng, difficulty)
    mr, mc = rng.choice(candidates)
    inp[mr][mc] = marker_col

    out = [row[:] for row in inp]
    interior_anchor = (r0 + 1, c0 + 1)
    anchor_parity = sum(interior_anchor) % 2
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = outline_col if (r + c) % 2 == anchor_parity else marker_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
