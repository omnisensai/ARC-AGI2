"""Micro-primitive family: snap_to_outline (ghost-shape variant).

Input has two SOLID shapes of the SAME normalized cell set but different colours
(piece colour C_p, ghost colour C_g), plus a single MARKER cell of a third
colour adjacent (4-conn) to one of the two blobs. The blob adjacent to the
marker is the SOURCE; the other blob is the DESTINATION ("ghost").

Rule: source -> bg, marker -> bg, destination -> C_p (filled in source colour).

This works for rectangles AND irregular shapes (anything 4-connected). No
boundary/closure detection is needed — the rule is pure shape-match +
marker-disambiguation + recolour.

Tiers: 0 fixed 11x11 rect | 1 + colour/bg | 2 irregular blobs.
"""
import random

FAMILY = "snap_to_outline"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def _components_by_colour(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]; cells = []; q = deque([(r, c)]); seen[r][c] = True
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True; q.append((ny, nx))
            comps.append((col, cells))
    return comps


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    comps = _components_by_colour(g, bg)
    if len(comps) != 3:
        return {}
    # Marker = the singleton component (1 cell)
    marker = next((c for c in comps if len(c[1]) == 1), None)
    blobs  = [c for c in comps if len(c[1]) > 1]
    if marker is None or len(blobs) != 2:
        return {}
    # Both blobs must be the same shape
    if _normalize(blobs[0][1]) != _normalize(blobs[1][1]):
        return {}
    marker_col, marker_cells = marker
    mr, mc = marker_cells[0]
    # Source = blob with a cell 4-adjacent to the marker.
    src = None; dst = None
    for blob in blobs:
        cells = set(blob[1])
        for (y, x) in cells:
            if abs(y - mr) + abs(x - mc) == 1:
                src = blob; break
        if src is blob:
            continue
    src = src or blobs[0]
    dst = blobs[1] if src is blobs[0] else blobs[0]
    src_col, src_cells = src
    dst_col, dst_cells = dst

    T = {}
    for (y, x) in src_cells:
        T[(y, x)] = bg
    T[(mr, mc)] = bg
    for (y, x) in dst_cells:
        T[(y, x)] = src_col
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
    return ("The blob next to the marker is the source; the same-shape blob "
            "elsewhere is the destination. Source disappears, destination "
            "takes the source's colour, marker disappears.")


def _shape_rect(rng, max_dim):
    h = rng.randint(2, max_dim); w = rng.randint(2, max_dim)
    return frozenset((r, c) for r in range(h) for c in range(w))


def _shape_blob(rng, max_dim):
    """Irregular 4-connected blob. No closure needed -> bumps are fine."""
    h = rng.randint(2, max_dim); w = rng.randint(2, max_dim)
    cells = {(r, c) for r in range(h) for c in range(w)}
    for _ in range(rng.randint(1, 3)):
        cs = list(cells)
        y, x = rng.choice(cs)
        dy, dx = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        ny, nx = y + dy, x + dx
        if ny >= 0 and nx >= 0:
            cells.add((ny, nx))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _place(rng, H, W, shape_cells, occupied, margin=1):
    sh = max(r for r, _ in shape_cells) + 1
    sw = max(c for _, c in shape_cells) + 1
    if H - sh < 0 or W - sw < 0:
        return None
    for _ in range(80):
        r0 = rng.randint(0, H - sh); c0 = rng.randint(0, W - sw)
        placed = {(r0 + r, c0 + c) for (r, c) in shape_cells}
        halo = {(y + dy, x + dx) for (y, x) in placed
                for dy in range(-margin, margin + 1)
                for dx in range(-margin, margin + 1)}
        if not (halo & occupied):
            return placed
    return None


def _instance(rng, difficulty):
    if difficulty <= 1:
        H = W = 12
    else:
        H = rng.randint(12, 15); W = rng.randint(12, 15)

    if difficulty == 0:
        bg, piece_col, ghost_col, marker_col = 0, 2, 4, 7
        shape = _shape_rect(rng, 3)
    elif difficulty == 1:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        piece_col, ghost_col, marker_col = rng.sample(avail, 3)
        shape = _shape_rect(rng, 4)
    else:
        bg = rng.choice([0, 0, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        piece_col, ghost_col, marker_col = rng.sample(avail, 3)
        shape = _shape_blob(rng, 4) if rng.random() < 0.7 else _shape_rect(rng, 4)

    occupied = set()
    src_placed = _place(rng, H, W, shape, occupied, margin=2)
    if src_placed is None: return _instance(rng, difficulty)
    occupied |= {(y + dy, x + dx) for (y, x) in src_placed
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
    dst_placed = _place(rng, H, W, shape, occupied, margin=2)
    if dst_placed is None: return _instance(rng, difficulty)

    # Marker: place adjacent (4-conn) to a source cell, on bg.
    candidates = []
    for (y, x) in src_placed:
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if (0 <= ny < H and 0 <= nx < W
                and (ny, nx) not in src_placed
                and (ny, nx) not in dst_placed):
                candidates.append((ny, nx))
    if not candidates: return _instance(rng, difficulty)
    mr, mc = rng.choice(candidates)
    # Ensure marker isn't 4-adjacent to the destination too
    if any(abs(mr - y) + abs(mc - x) == 1 for (y, x) in dst_placed):
        return _instance(rng, difficulty)

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in src_placed: inp[y][x] = piece_col
    for (y, x) in dst_placed: inp[y][x] = ghost_col
    inp[mr][mc] = marker_col

    out = [row[:] for row in inp]
    for (y, x) in src_placed: out[y][x] = bg
    out[mr][mc] = bg
    for (y, x) in dst_placed: out[y][x] = piece_col
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
