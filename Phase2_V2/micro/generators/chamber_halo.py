"""Micro-primitive family: chamber_halo.

K solid rectangular WALLS (colour C_wall) sit on the grid. A single SEED cell
(colour C_seed, rare isolated cell) sits in one of the bg-connected regions
(the seed's "chamber"). The chamber = bg cells reachable from the seed by a
4-conn flood that treats wall cells as blockers; the seed cell itself counts
as in-chamber.

Rule:
  - Every cell in the seed's chamber that is 8-ADJACENT to a wall OR to the
    grid border is painted with the SEED colour (so the seed itself stays its
    colour, and a 1-cell-thick halo lights up around every wall and along the
    grid border inside the chamber). 8-conn is key — it correctly wraps the
    halo around corners and concave wall geometry (the canonical "LLM bodges
    this" failure mode).
  - Walls that are 4-adjacent to the seed's chamber are KEPT.
  - Walls NOT 4-adjacent to the seed's chamber are ERASED to bg.
  - Bg cells outside the seed's chamber stay bg (unchanged).

This captures the recurring ARC pattern: a "snake" (seed) inside an uneven
chamber traces every wall and border around it via 8-conn depth-0 cells.
Equivalent to chebyshev_room_erosion_fill's depth-0 layer (the boundary).

Tiers: 0 fixed 11x11, 1 wall | 1 + colour/bg, 2-3 walls | 2 + varied size,
       3-4 walls (some isolated from the chamber, getting erased).
"""
import random

FAMILY = "chamber_halo"


def canonical_solver() -> str:
    return '''from collections import Counter, deque


def infer_T(g):
    H, W = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]
    counts = Counter(v for row in g for v in row if v != bg)
    if len(counts) < 2:
        return {}
    # Seed = single isolated cell (count == 1); wall = the other (multi-cell).
    singletons = [c for c, n in counts.items() if n == 1]
    if len(singletons) != 1:
        return {}
    seed_col = singletons[0]
    wall_col = next(c for c in counts if c != seed_col)

    seed_pos = next((r, c) for r in range(H) for c in range(W) if g[r][c] == seed_col)
    wall_cells = {(r, c) for r in range(H) for c in range(W) if g[r][c] == wall_col}

    # Flood from seed through bg cells (and seed cell itself), blocked by walls.
    chamber = {seed_pos}; q = deque([seed_pos])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in chamber and (nr, nc) not in wall_cells:
                chamber.add((nr, nc)); q.append((nr, nc))

    T = {}
    # Halo: chamber cells 8-adjacent to wall or grid border take the seed colour.
    for (r, c) in chamber:
        if (r, c) == seed_pos:
            continue
        on_border = (r in (0, H - 1) or c in (0, W - 1))
        near_wall = any((r + dy, c + dx) in wall_cells
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dy, dx) != (0, 0))
        if on_border or near_wall:
            T[(r, c)] = seed_col

    # Erase walls not 4-adjacent to the chamber.
    for (r, c) in wall_cells:
        adj_chamber = any((r + dy, c + dx) in chamber
                          for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if not adj_chamber:
            T[(r, c)] = bg
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
    return ("Find the seed's chamber. Paint a 1-cell-thick halo (in the seed's "
            "colour, 8-conn so it wraps corners) on every wall/border the "
            "chamber touches. Erase any walls outside the chamber.")


def _place_rect(rng, H, W, max_h, max_w, occupied, margin=1):
    """Place a solid h x w rectangle, ENFORCING at least 2 cells total (so the
    wall is unambiguously distinct from the single-cell seed by component size)."""
    for _ in range(60):
        h = rng.randint(1, max_h); w = rng.randint(1, max_w)
        if h * w < 2:
            continue
        r0 = rng.randint(0, H - h); c0 = rng.randint(0, W - w)
        cells = {(r0 + r, c0 + c) for r in range(h) for c in range(w)}
        halo = {(y + dy, x + dx) for (y, x) in cells
                for dy in range(-margin, margin + 1)
                for dx in range(-margin, margin + 1)}
        if not (halo & occupied):
            return cells
    return None


def _instance(rng, difficulty):
    if difficulty == 0:
        H = W = 11; n_walls = 1
        bg, wall_col, seed_col = 8, 1, 6
    elif difficulty == 1:
        H = W = 12; n_walls = rng.randint(2, 3)
        bg = rng.choice([0, 8, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, seed_col = rng.sample(avail, 2)
    else:
        H = rng.randint(12, 16); W = rng.randint(12, 16); n_walls = rng.randint(3, 4)
        bg = rng.choice([0, 8, rng.randint(0, 9)])
        avail = [c for c in range(10) if c != bg]
        wall_col, seed_col = rng.sample(avail, 2)

    occupied = set(); wall_cells = set()
    for _ in range(n_walls):
        rect = _place_rect(rng, H, W, max_h=max(2, H // 4), max_w=max(2, W // 4),
                           occupied=occupied)
        if rect is None:
            continue
        wall_cells |= rect
        occupied |= {(y + dy, x + dx) for (y, x) in rect
                     for dy in (-1, 0, 1) for dx in (-1, 0, 1)}

    if not wall_cells:
        return _instance(rng, difficulty)

    # Build chambers.
    bg_cells = [(r, c) for r in range(H) for c in range(W) if (r, c) not in wall_cells]
    visited = set(); regions = []
    for cell in bg_cells:
        if cell in visited:
            continue
        region = {cell}; q = [cell]
        while q:
            r, c = q.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if (0 <= nb[0] < H and 0 <= nb[1] < W and
                    nb not in wall_cells and nb not in region):
                    region.add(nb); q.append(nb)
        visited |= region
        regions.append(region)

    regions.sort(key=len, reverse=True)
    chamber = regions[0]
    if len(chamber) < 4:
        return _instance(rng, difficulty)
    seed_pos = rng.choice(list(chamber))

    inp = [[bg] * W for _ in range(H)]
    for (y, x) in wall_cells:
        inp[y][x] = wall_col
    inp[seed_pos[0]][seed_pos[1]] = seed_col

    out = [row[:] for row in inp]
    for (r, c) in chamber:
        if (r, c) == seed_pos:
            continue
        on_border = (r in (0, H - 1) or c in (0, W - 1))
        near_wall = any((r + dy, c + dx) in wall_cells
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dy, dx) != (0, 0))
        if on_border or near_wall:
            out[r][c] = seed_col
    for (r, c) in wall_cells:
        adj_chamber = any((r + dy, c + dx) in chamber
                          for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if not adj_chamber:
            out[r][c] = bg
    return {"input": inp, "output": out}


def generate(seed, difficulty):
    rng = random.Random(seed)
    n_train = rng.randint(3, 4)
    pairs = [_instance(rng, difficulty) for _ in range(n_train + 1)]
    return {"family": FAMILY, "seed": seed, "difficulty": difficulty,
            "params": {"n_train": n_train}, "train": pairs[:-1], "test": pairs[-1:]}
