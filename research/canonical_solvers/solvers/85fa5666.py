def _find_blocks(g):
    """Locate every 2x2 block of color 2. Return their top-left corners."""
    H, W = len(g), len(g[0])
    seen = set()
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (g[r][c] == 2 and g[r][c + 1] == 2 and
                    g[r + 1][c] == 2 and g[r + 1][c + 1] == 2):
                if (r, c) in seen:
                    continue
                for dr in range(2):
                    for dc in range(2):
                        seen.add((r + dr, c + dc))
                blocks.append((r, c))
    return blocks


def infer_T(input_grid):
    """
    Each object is a 2x2 block of color 2 surrounded by four diagonal corner
    markers (the four cells touching the block's corners). The transformation:

      1. The four corner colors rotate one step CLOCKWISE around the block
         (new TL = old BL, new TR = old TL, new BR = old TR, new BL = old BR).
      2. From each corner cell a diagonal ray of its NEW color shoots OUTWARD
         (away from the block centre): TL up-left, TR up-right, BL down-left,
         BR down-right.
      3. A ray runs until it leaves the grid or hits another 2x2 block. It is
         also terminated when it merges with a foreign corner of its own colour
         (the cell is orthogonally adjacent to a same-colour corner of another
         block) provided the ray would otherwise keep going into the interior
         (the cell two steps further along the diagonal is still on the grid).

    The mask T maps each overwritten cell -> new colour.
    """
    H, W = len(input_grid), len(input_grid[0])
    blocks = _find_blocks(input_grid)

    block_cells = set()
    for (r, c) in blocks:
        for dr in range(2):
            for dc in range(2):
                block_cells.add((r + dr, c + dc))

    def cell_color(p):
        rr, cc = p
        if 0 <= rr < H and 0 <= cc < W:
            return input_grid[rr][cc]
        return 0

    # Corner position + its NEW (rotated) colour + the owning block index.
    all_corners = []          # list of (pos, new_color, block_index)
    rotated = []              # per-block: (new_color_map, ray_dir_map)
    for bi, (r, c) in enumerate(blocks):
        TL = (r - 1, c - 1)
        TR = (r - 1, c + 2)
        BL = (r + 2, c - 1)
        BR = (r + 2, c + 2)
        new_color = {
            TL: cell_color(BL),   # clockwise rotation of the corner colours
            TR: cell_color(TL),
            BR: cell_color(TR),
            BL: cell_color(BR),
        }
        ray_dir = {TL: (-1, -1), TR: (-1, 1), BL: (1, -1), BR: (1, 1)}
        rotated.append((new_color, ray_dir))
        for cp in (TL, TR, BL, BR):
            all_corners.append((cp, new_color[cp], bi))

    T = {}
    for bi, (r, c) in enumerate(blocks):
        new_color, ray_dir = rotated[bi]
        for corner, (dr, dc) in ray_dir.items():
            color = new_color[corner]
            rr, cc = corner
            while 0 <= rr < H and 0 <= cc < W:
                if (rr, cc) in block_cells:
                    break
                T[(rr, cc)] = color

                # Stop if this cell merges with a same-colour corner of a
                # different block and the ray would otherwise drive on into the
                # interior (two cells ahead is still inside the grid).
                stop = False
                ahead2 = (rr + 2 * dr, cc + 2 * dc)
                ahead2_in = 0 <= ahead2[0] < H and 0 <= ahead2[1] < W
                if ahead2_in:
                    for (cp, ccol, cbi) in all_corners:
                        if cbi == bi or ccol != color:
                            continue
                        if abs(rr - cp[0]) + abs(cc - cp[1]) == 1:
                            stop = True
                            break
                if stop:
                    break
                rr += dr
                cc += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
