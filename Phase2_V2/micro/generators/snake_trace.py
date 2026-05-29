"""Micro-primitive family: snake_trace.

A closed irregular wall (a 4-connected closed outline of some shape, drawn in
colour C_wall) sits on the grid. A single seed cell (colour C_snake) sits on
bg, 4-adjacent to one of the wall cells, on the EXTERIOR side of the wall.

Rule: the snake traces the wall. Trail = all EXTERIOR bg cells (cells
reachable from the grid border by a 4-conn flood that treats wall cells as
blockers) that are 4-adjacent to at least one wall cell. Those cells take
the snake's colour.

Distinct from fill_enclosed_marker (which fills the INTERIOR with the marker
colour) — here the painted layer is the OUTER halo around the wall.

Tiers: 0 fixed 12x12 rect wall | 1 + colour/bg | 2 irregular wall + varied size.
"""
import random

FAMILY = "snake_trace"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    if len(counts) < 2:
        return {}
    # Snake = the rarest non-bg colour (single seed cell).
    snake_col = min(counts, key=lambda k: counts[k])
    wall_col = next(c for c in counts if c != snake_col)

    wall = {(r, c) for r in range(H) for c in range(W) if g[r][c] == wall_col}
    if not wall:
        return {}

    # Exterior = cells reachable from grid border via 4-conn flood, treating
    # wall cells as blockers. (Snake seed cell is non-bg too -> treat as
    # non-blocker by skipping the wall check when expanding into it; but its
    # cell isn't bg so we exclude it from exterior set computation.)
    exterior = set(); q = deque()
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and (r, c) not in wall:
                if (r, c) not in exterior:
                    exterior.add((r, c)); q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in wall and (nr, nc) not in exterior:
                exterior.add((nr, nc)); q.append((nr, nc))

    T = {}
    for (r, c) in exterior:
        # already-coloured cells (the snake seed) stay; we still write T but
        # the value equals their existing colour.
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in wall:
                if g[r][c] == bg:
                    T[(r, c)] = snake_col
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
    return ("The snake (single seed cell) traces the outer wall: every "
            "exterior bg cell adjacent to a wall cell takes the snake colour.")


def _shape_blob(rng, max_dim):
    """4-connected blob with non-empty interior + closed boundary."""
    for _ in range(40):
        h = rng.randint(3, max_dim); w = rng.randint(3, max_dim)
        cells = {(r, c) for r in range(h) for c in range(w)}
        # Optional bumps that extend the bounding box but preserve a closed
        # boundary. Bumps that extend FULL ROWS or FULL COLUMNS (one new row
        # of 2+ cells along an existing edge) keep the boundary 4-connected.
        if rng.random() < 0.6:
            side = rng.choice(["top", "bottom", "left", "right"])
            if side == "top":
                length = rng.randint(2, max(2, w - 1))
                start = rng.randint(0, w - length)
                for c in range(start, start + length):
                    cells.add((-1, c))
            elif side == "bottom":
                length = rng.randint(2, max(2, w - 1))
                start = rng.randint(0, w - length)
                for c in range(start, start + length):
                    cells.add((h, c))
            elif side == "left":
                length = rng.randint(2, max(2, h - 1))
                start = rng.randint(0, h - length)
                for r in range(start, start + length):
                    cells.add((r, -1))
            else:
                length = rng.randint(2, max(2, h - 1))
                start = rng.randint(0, h - length)
                for r in range(start, start + length):
                    cells.add((r, w))
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        cells = {(r - mr, c - mc) for r, c in cells}
        # Verify closed boundary: render boundary cells and check that
        # interior cells (computed via flood from a synthetic "outside") are
        # unreachable from the bounding-box border.
        boundary = {(y, x) for (y, x) in cells
                    if any((y + dy, x + dx) not in cells
                           for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        interior = cells - boundary
        if not interior:
            continue
        return frozenset(cells), frozenset(boundary)
    # Fallback: simple 4x4 rectangle
    cells = frozenset((r, c) for r in range(4) for c in range(4))
    boundary = frozenset((y, x) for (y, x) in cells
                         if y in (0, 3) or x in (0, 3))
    return cells, boundary


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12
    else:
        H = rng.randint(12, 15); W = rng.randint(12, 15)

    if difficulty == 0:
        bg, wall_col, snake_col = 0, 4, 2
        # rectangle wall (smallest interesting case)
        h = w = 4
        cells = frozenset((r, c) for r in range(h) for c in range(w))
        boundary = frozenset((y, x) for (y, x) in cells
                             if y in (0, h - 1) or x in (0, w - 1))
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, snake_col = rng.sample(avail, 2)
        h = rng.randint(4, 6); w = rng.randint(4, 6)
        cells = frozenset((r, c) for r in range(h) for c in range(w))
        boundary = frozenset((y, x) for (y, x) in cells
                             if y in (0, h - 1) or x in (0, w - 1))
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, snake_col = rng.sample(avail, 2)
        cells, boundary = _shape_blob(rng, 5)

    # Place wall with margin 2 (so the exterior halo fits on all sides).
    sh = max(r for r, _ in boundary) + 1; sw = max(c for _, c in boundary) + 1
    if H - sh < 3 or W - sw < 3:
        return _instance(rng, difficulty)
    r0 = rng.randint(2, H - sh - 2); c0 = rng.randint(2, W - sw - 2)
    wall_cells = {(r0 + y, c0 + x) for (y, x) in boundary}

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in wall_cells:
        inp[y][x] = wall_col

    # Exterior bg cells 4-adjacent to wall (compute by flood from border).
    exterior = set(); q = []
    for r in range(H):
        for c in range(W):
            if (r in (0, H - 1) or c in (0, W - 1)) and (r, c) not in wall_cells:
                if (r, c) not in exterior:
                    exterior.add((r, c)); q.append((r, c))
    while q:
        r, c = q.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in wall_cells and (nr, nc) not in exterior:
                exterior.add((nr, nc)); q.append((nr, nc))
    halo = [(r, c) for (r, c) in exterior
            if any((r + dy, c + dx) in wall_cells for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    if not halo:
        return _instance(rng, difficulty)

    seed_pos = rng.choice(halo)
    inp[seed_pos[0]][seed_pos[1]] = snake_col

    out = [row[:] for row in inp]
    for (r, c) in halo:
        if out[r][c] == bg:
            out[r][c] = snake_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
