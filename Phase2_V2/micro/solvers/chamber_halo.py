from collections import Counter, deque


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
