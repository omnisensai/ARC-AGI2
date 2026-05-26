def _find_blocks(grid):
    """Find 2x2 blocks of color 2; return list of (top_row, left_col)."""
    H, W = len(grid), len(grid[0])
    blocks = []
    for r in range(H - 1):
        for c in range(W - 1):
            if (grid[r][c] == 2 and grid[r][c + 1] == 2 and
                    grid[r + 1][c] == 2 and grid[r + 1][c + 1] == 2):
                blocks.append((r, c))
    return blocks


def infer_T(input_grid):
    """Latent mask dict {(r,c): color}.

    Each 2x2 block of 2s has four diagonal corner markers, one cell
    outside each block corner. The corner colors rotate clockwise (each
    position receives the value of its counter-clockwise neighbour), and a
    diagonal ray of the new corner colour is drawn outward (away from the
    block) until it leaves the grid or meets a non-background cell.
    """
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    blocks = _find_blocks(input_grid)
    for (tr, lc) in blocks:
        br_row, rc = tr + 1, lc + 1
        # corner positions: just outside the 2x2 diagonally
        tl = (tr - 1, lc - 1)
        trc = (tr - 1, rc + 1)
        bl = (br_row + 1, lc - 1)
        brc = (br_row + 1, rc + 1)
        corners = [tl, trc, brc, bl]          # clockwise from top-left
        # diagonal outward directions for each corner
        dirs = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        # current colours at corner positions
        old = [input_grid[r][c] if 0 <= r < H and 0 <= c < W else 0
               for (r, c) in corners]
        # clockwise rotation: position i gets value from counter-clockwise
        # neighbour (i-1)
        new = [old[(i - 1) % 4] for i in range(4)]
        for i, (cr, cc) in enumerate(corners):
            color = new[i]
            if not (0 <= cr < H and 0 <= cc < W):
                continue
            T[(cr, cc)] = color
            # draw ray outward
            dr, dc = dirs[i]
            rr, cc2 = cr + dr, cc + dc
            while 0 <= rr < H and 0 <= cc2 < W and input_grid[rr][cc2] == 0:
                T[(rr, cc2)] = color
                rr += dr
                cc2 += dc
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
