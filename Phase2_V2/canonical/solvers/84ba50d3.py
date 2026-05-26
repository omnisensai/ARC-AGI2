from collections import Counter


def infer_T(input_grid):
    """Infer the transformation from the input alone.

    Structure: a full horizontal wall (one solid non-background row) plus several
    1-color objects sitting above it. Each object falls straight down (gravity)
    toward the wall, keeping its exact shape and columns:

      * An object that has a "head" (any row of width >= 2, e.g. a bar/foot) is
        too wide to fit through the wall, so it rests with that head row just
        above the wall (head row -> wall_row - 1). A width-1 stem hanging below
        the head pokes through the wall (showing the object color on the wall).
      * A pure straight line / dot (every row width 1) has no head, so it passes
        straight through the wall and drops to the floor (bottom edge). Where it
        passes through the wall it punches a hole (the wall cell -> background).

    Returns (stamp, holes, bg, wall_row, wall_color):
        stamp  : {(r,c): color} cells the fallen objects occupy.
        holes  : set of columns where the wall cell becomes background.
    """
    H = len(input_grid)
    W = len(input_grid[0])

    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    # The wall: a row that is entirely a single non-background color.
    wall_row = None
    wall_color = None
    for r in range(H):
        vals = set(input_grid[r])
        if len(vals) == 1 and bg not in vals:
            wall_row = r
            wall_color = next(iter(vals))
            break

    stamp = {}
    holes = set()
    if wall_row is None:
        return (stamp, holes, bg, wall_row, wall_color)

    # The moving object color (anything that is not background and not the wall).
    obj_color = None
    for v in counts:
        if v != bg and v != wall_color:
            obj_color = v
            break
    if obj_color is None:
        return (stamp, holes, bg, wall_row, wall_color)

    # Connected components (8-connectivity) of the object color.
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == obj_color and (r, c) not in seen:
                st = [(r, c)]
                cells = []
                while st:
                    rr, cc = st.pop()
                    if (rr, cc) in seen or not (0 <= rr < H and 0 <= cc < W):
                        continue
                    if input_grid[rr][cc] != obj_color:
                        continue
                    seen.add((rr, cc))
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                st.append((rr + dr, cc + dc))
                comps.append(cells)

    for cells in comps:
        rows_width = Counter(r for r, _ in cells)
        max_width = max(rows_width.values())
        bottom = max(r for r, _ in cells)

        if max_width == 1:
            # No head: drop to the floor.
            shift = (H - 1) - bottom
        else:
            # Rest the (topmost) widest row just above the wall.
            head = min(r for r in rows_width if rows_width[r] == max_width)
            shift = (wall_row - 1) - head

        # Stamp the fallen object.
        landed_by_col = {}
        for (r, c) in cells:
            nr = r + shift
            stamp[(nr, c)] = obj_color
            landed_by_col.setdefault(c, []).append(nr)

        # A column that drops entirely below the wall (no landed cell on the
        # wall row) punches a hole in the wall.
        for c, lrows in landed_by_col.items():
            if min(lrows) > wall_row and wall_row not in lrows:
                holes.add(c)

    return (stamp, holes, bg, wall_row, wall_color)


def apply_T(input_grid, info):
    stamp, holes, bg, wall_row, wall_color = info
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]

    # Clear everything to background, restore the wall, then stamp.
    if wall_row is not None:
        for r in range(H):
            for c in range(W):
                if r == wall_row:
                    out[r][c] = wall_color
                elif out[r][c] != bg:
                    out[r][c] = bg

    for (r, c), v in stamp.items():
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = v

    if wall_row is not None:
        for c in holes:
            if 0 <= c < W:
                out[wall_row][c] = bg

    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
