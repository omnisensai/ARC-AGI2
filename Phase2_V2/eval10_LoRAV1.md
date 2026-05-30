
========== 0607ce86 a0  [wrong_training] ==========

from collections import Counter


def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Find the noise color (anything that appears more than a quarter of the total
    # cells, since header rows and columns are uniform).
    counts = Counter()
    for row in input_grid:
        for v in row:
            counts[v] += 1
    noise = max(counts, key=lambda k: counts[k])

    # Identify horizontal lines (rows where > half cells are same non-noise color)
    h_lines = set()
    for r in range(H):
        cnt = Counter(input_grid[r])
        for col, c in cnt.items():
            if col != noise and c > W // 2:
                h_lines.add(r)
                break

    # Identify vertical lines (cols where > half cells are same non-noise color)
    v_lines = set()
    for c in range(W):
        cnt = Counter(input_grid[r][c] for r in range(H))
        for col, c in cnt.items():
            if col != noise and c > H // 2:
                v_lines.add(c)

    # Build output: replace everything that isn't a line cell with 0
    out = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if r in h_lines or c in v_lines:
                out[r][c] = input_grid[r][c]
            else:
                out[r][c] = 0
    return out


========== 0607ce86 a1  [wrong_training] ==========

from collections import Counter


def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Find the noise color (anything that appears more than a few times)
    counts = Counter()
    for row in input_grid:
        for v in row:
            counts[v] += 1
    noise = counts.most_common(1)[0][0]

    # Find grid cell template positions: places where the noise doesn't dominate
    # (i.e., one color dominates the cell).
    cells = []  # list of (r0, c0, r1, c1, center, template_color)
    center_color = {}
    for r in range(H - 1):
        for c in range(W - 1):
            colors = Counter()
            for dr in range(2):
                for dc in range(2):
                    colors[input_grid[r + dr][c + dc]] += 1
            if colors.most_common(1)[0][1] >= 2:
                r0, c0 = r, c
                r1, c1 = r + 1, c + 1
                cr, cc = (r0 + r1) / 2, (c0 + c1) / 2
                cells.append((r0, c0, r1, c1, (cr, cc), colors.most_common(1)[0][0]))
                center_color[(r0, c0)] = cells[-1][5]

    # Build output: all zeros (noise removed), then add back grid lines and cells
    out = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if r == 0 or r == H - 1 or c == 0 or c == W - 1:
                out[r][c] = 0

    for (r0, c0), color in center_color.items():
        cr, cc = (r0 + (r0 + 1)) / 2, (c0 + (c0 + 1)) / 2
        out[int(cr)][int(cc)] = color

    for (r0, c0, r1, c1, center, templ_color) in cells:
        cr, cc = center
        for dr in range(2):
            for dc in range(2):
                rr, cc2 = r0 + dr, c0 + dc
                if 0 <= rr < H and 0 <= cc2 < W:
                    out[rr][cc2] = templ_color

        for dr in range(3):
            for dc in range(3):
                if dr == 1 and dc == 1:
                    continue
                rr, cc2 = r0 + dr, c0 + dc
                if 0 <= rr < H and 0 <= cc2 < W:
                    out[rr][cc2] = noise

        for dr in range(2):
            for dc in range(2):
                rr, cc2 = r1 - dr, c1 - dc
                if 0 <= rr < H and 0 <= cc2 < W:
                    out[rr][cc2] = templ_color

    return out


========== 08ed6ac7 a0  [exec_error] ==========

def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [row[:] for row in input_grid]
    col_cells = {}
    for c in range(w):
        cells = [r for r in range(h) if input_grid[r][c] == 5]
        if cells:
            col_cells[c] = cells
    colors = {}
    idx = 1
    while col_cells:
        min_len = min(len(v) for v in col_cells.values())
        cols = [k for k, v in col_cells.items() if len(v) == min_len]
        col = cols[0]
        vals = sorted(col_cells[col][:min_len])
        for i, v in enumerate(vals):
            colors[(col, v)] = idx + i
        for c in cols:
            del col_cells[c][:min_len]
        idx += min_len
    for c, cells in col_cells.items():
        for v in cells:
            out[v][c] = colors.get((c, v), 4)
    return out


========== 08ed6ac7 a1  [wrong_training] ==========

def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [row[:] for row in input_grid]
    col_cells = {}
    for c in range(w):
        cells = [r for r in range(h) if input_grid[r][c] == 5]
        if cells:
            col_cells[c] = cells
    colors = {}
    for c, cells in col_cells.items():
        if len(cells) == 1:
            colors[c] = 1
        elif len(cells) == 2:
            colors[c] = 2
        else:
            colors[c] = 4
    diagonal_offset = -h + 1
    for c, cells in col_cells.items():
        color = colors[c]
        for r in cells:
            dc = diagonal_offset + r
            for cc in cells:
                dr = diagonal_offset + cc
                if 0 <= dr < h and 0 <= dc < w:
                    if out[dr][dc] == 0:
                        out[dr][dc] = color
    return out


========== 0f63c0b9 a0  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Find background color (assume it's 0)
    bg = 0

    # Find connected components of non-bg cells (4-connectivity)
    visited = [[False] * W for _ in range(H)]
    objects = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg and not visited[r][c]:
                color = input_grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if visited[rr][cc]:
                        continue
                    if input_grid[rr][cc] != color:
                        continue
                    visited[rr][cc] = True
                    cells.append((rr, cc))
                    stack.extend([(rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)])
                objects.append((color, cells))

    # Build output grid
    output = [[bg] * W for _ in range(H)]

    for color, cells in objects:
        corner = None
        edge_cells = []
        interior_cells = []
        for (r, c) in cells:
            ns = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            n_non_bg = sum(1 for (rr, cc) in ns if 0 <= rr < H and 0 <= cc < W and input_grid[rr][cc] != bg)
            if n_non_bg == 1:
                corner = (r, c)
            elif n_non_bg == 2:
                edge_cells.append((r, c))
            else:
                interior_cells.append((r, c))

        # Draw arms from corner to edges (inclusive end)
        cr, cc = corner
        edge_cells.sort(key=lambda x: (x[0] - cr, x[1] - cc))
        previous_edge = None
        for er, ec in edge_cells:
            if previous_edge is not None and (er, ec) != previous_edge:
                # Draw horizontal arm from previous_edge to (cr+1, ec)
                for rr in range(previous_edge[0], cr + 1):
                    if 0 <= rr < H and 0 <= ec < W:
                        output[rr][ec] = color
                # Draw vertical arm from previous_edge to (er, cc+1)
                for cc_ in range(previous_edge[1], ec + 1):
                    if 0 <= er < H and 0 <= cc_ < W:
                        output[er][cc_] = color
            previous_edge = (er, ec)
            # Draw horizontal at er from ec to W-1
            for cc_ in range(ec, W):
                if 0 <= er < H and 0 <= cc_ < W:
                    output[er][cc_] = color
            # Draw vertical at ec from er to H-1
            for rr in range(er, H):
                if 0 <= rr < H and 0 <= ec < W:
                    output[rr][ec] = color

        # Mark interior cells
        for (ir, ic) in interior_cells:
            output[ir][ic] = color

    return output

root@e3241538a7a6:/workspace/ARC-AGI2# 

========== 0f63c0b9 a1  [wrong_training] ==========

def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [[0] * w for _ in range(h)]
    # Find the 2 marker and draw vertical lines at its columns for both colors
    col2 = -1
    for r in range(h):
        for c in range(w):
            v = input_grid[r][c]
            if v == 2:
                col2 = c
            elif v == 8:
                out[r][c] = 8
            elif v == 3:
                out[r][c] = 3
    for r in range(h):
        out[r][col2] = 2
    row7 = -1
    for r in range(h):
        for c in range(w):
            v = input_grid[r][c]
            if v == 7:
                row7 = r
            elif v == 1:
                cc = c
                top = r
                bottom = h - 1 - top
                for rr in [top, bottom]:
                    out[rr][cc] = 1
    if row7 >= 0:
        out[row7][col2] = 7
    return out


========== 103eff5b a0  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]

    # Find bounding box of all 8s
    eight_cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    rmin = min(r for r, c in eight_cells)
    rmax = max(r for r, c in eight_cells)
    cmin = min(c for r, c in eight_cells)
    cmax = max(c for r, c in eight_cells)

    # Identify non-8 colored boundary cells (the frame colors)
    frame_colors = {}
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            v = input_grid[r][c]
            if v != 8:
                frame_colors[(r, c)] = v

    # Identify corners (cells with at least one non-zero adjacent cell of a different color)
    corners = []
    corner_colors = {}
    for (r, c), color in frame_colors.items():
        adj = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        neighbors_color = {p: input_grid[p[0]][p[1]] for p in adj if 0 <= p[0] < H and 0 <= p[1] < W}
        non_zero = [p for p, v in neighbors_color.items() if v != 0]
        if non_zero:
            corners.append((r, c))
            corner_colors[(r, c)] = color

    # Determine orientation: horizontal or vertical
    # Horizontal: all corners on one row (and frame_colors have col spanning bbox)
    # Vertical: all corners on one column (and frame_colors have row spanning bbox)
    rows_of_corners = set(r for r, c in corners)
    cols_of_corners = set(c for r, c in corners)
    if len(rows_of_corners) == 1:
        # Horizontal orientation
        hr = next(iter(rows_of_corners))
        # Determine which end (near: closer to the inside gap, far: opposite)
        # Inside gap row is between rmin and rmax of 8s
        inside_row = (rmin + rmax) // 2
        # Near end: inside_row - hr (negative if inside_row closer to hr)
        near_end = (inside_row < hr) - (inside_row > hr)
        if near_end == 0:
            near_end = (inside_row >= hr) - (inside_row < hr)
        # Order corners from near to far
        sorted_corners = sorted(corners, key=lambda c: (hr - c[0]) * near_end)
        # Color pair: left (near) is A, right (far) is B
        A = corner_colors[sorted_corners[0]]
        B = corner_colors[sorted_corners[-1]]
        # Fill between inside_row and max(rmin, hr-1) inclusive
        # Actually: rows inside_row .. min(rmax, hr+1) inclusive
        row_start = max(rmin, hr - 1)
        row_end = min(rmax, hr + 1)
        for r in range(row_start, row_end + 1):
            for c in range(cmin, cmax + 1):
                out[r][c] = A if (r - hr) * near_end < 0 else B
    elif len(cols_of_corners) == 1:
        hc = next(iter(cols_of_corners))
        inside_col = (cmin + cmax) // 2
        near_end = (inside_col - hc) < 0
        sorted_corners = sorted(corners, key=lambda c: (hc - c[1]) * near_end)
        A = corner_colors[sorted_corners[0]]
        B = corner_colors[sorted_corners[-1]]
        col_start = max(cmin, hc - 1)
        col_end = min(cmax, hc + 1)
        for r in range(rmin, rmax + 1):
            for c in range(col_start, col_end + 1):
                out[r][c] = A if (c - hc) * near_end < 0 else B

    return out


========== 103eff5b a1  [exec_error] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    # Find bounding box of all 8s
    eights = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 8]
    rmin = min(eights,key=lambda x:x[0])[0]
    rmax = max(eights,key=lambda x:x[0])[0]
    cmin = min(eights,key=lambda x:x[1])[1]
    cmax = max(eights,key=lambda x:x[1])[1]

    # Identify shapes: they are colored cells outside the 8-border
    # Find colors in input_grid
    colors = set()
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0 and v != 8:
                colors.add(v)

    # Collect cells for each color
    color_cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in colors:
                color_cells.setdefault(v, []).append((r, c))

    # Determine which color is the "interior" by checking which color has
    # cells inside the 8-border (between rmin+1 and rmax-1, cmin+1 and cmax-1)
    interior_color = None
    for col in color_cells:
        for (rr, cc) in color_cells[col]:
            if rmin < rr < rmax and cmin < cc < cmax:
                interior_color = col
                break
        if interior_color is not None:
            break

    # Interior color stays; convert it to 2
    two_cells = [(r, c) for (r, c) in color_cells[interior_color] if r < rmin or r > rmax or c < cmin or c > cmax]
    four_cells = [(r, c) for (r, c) in color_cells[interior_color] if rmin <= r <= rmax and cmin <= c <= cmax]
    if four_cells:
        corner_rmin = min(four_cells, key=lambda x: x[0])[0]
        corner_rmax = max(four_cells, key=lambda x: x[0])[0]
        corner_cmin = min(four_cells, key=lambda x: x[1])[1]
        corner_cmax = max(four_cells, key=lambda x: x[1])[1]

        # Determine which corner has the 4
        four_corner = None
        for (r, c) in four_cells:
            if r == corner_rmin and c == corner_cmin:
                four_corner = 'TL'
                break
            elif r == corner_rmin and c == corner_cmax:
                four_corner = 'TR'
                break
            elif r == corner_rmax and c == corner_cmin:
                four_corner = 'BL'
                break
            elif r == corner_rmax and c == corner_cmax:
                four_corner = 'BR'
                break

        on_edge = set(four_cells)

        if four_corner == 'TL':
            three_side = [cell for cell in color_cells[3] if cell[1] == cmin]
            four_side = [cell for cell in color_cells[4] if cell[0] == rmin]
            opposite_color = 1
        elif four_corner == 'TR':
            three_side = [cell for cell in color_cells[3] if cell[1] == cmax]
            four_side = [cell for cell in color_cells[4] if cell[0] == rmin]
            opposite_color = 1
        elif four_corner == 'BL':
            three_side = [cell for cell in color_cells[3] if cell[1] == cmin]
            four_side = [cell for cell in color_cells[4] if cell[0] == rmax]
            opposite_color = 4
        elif four_corner == 'BR':
            three_side = [cell for cell in color_cells[3] if cell[1] == cmax]
            four_side = [cell for cell in color_cells[4] if cell[0] == rmax]
            opposite_color = 4

        # Extend 3 side to full row at cmin/cmax
        if four_corner in ['TL', 'TR']:
            three_row_ext = [(corner_rmin, cc) for cc in range(cmin, cmax + 1)]
        else:
            three_row_ext = [(corner_rmax, cc) for cc in range(cmin, cmax + 1)]
        if four_corner in ['TL', 'BL']:
            three_col_ext = [(rr, corner_cmin) for rr in range(rmin, rmax + 1)]
        else:
            three_col_ext = [(rr, corner_cmax) for rr in range(rmin, rmax + 1)]

        # Extend 4 side
        if four_corner in ['TL', 'TR']:
            four_row_ext = [(corner_r, cmax) for corner_r in range(rmin, rmax + 1)]
        else:
            four_row_ext = [(corner_r, cmin) for corner_r in range(rmin, rmax + 1)]
        if four_corner in ['BL', 'BR']:
            four_col_ext = [(rmax, cc) for cc in range(cmin, cmax + 1)]
        else:
            four_col_ext = [(rmin, cc) for cc in range(cmin, cmax + 1)]

        # Draw 2 between the extended lines (exclusive)
        two_rows = set()
        two_cols = set()
        if four_corner in ['TL', 'TR']:
            for rr in range(corner_rmin + 1, corner_rmin + 6):
                if 0 <= rr < H:
                    two_rows.add(rr)
        else:
            for rr in range(corner_rmax - 1, corner_rmax - 6, -1):
                if 0 <= rr < H:
                    two_rows.add(rr)
        if four_corner in ['TL', 'BL']:
            for cc in range(corner_cmin + 1, corner_cmin + 6):
                if 0 <= cc < W:
                    two_cols.add(cc)
        else:
            for cc in range(corner_cmax - 1, corner_cmax - 6, -1):
                if 0 <= cc < W:
                    two_cols.add(cc)

        two_cells = []
        for rr in two_rows:
            for cc in range(W):
                two_cells.append((rr, cc))
        for cc in two_cols:
            for rr in range(H):
                two_cells.append((rr, cc))

        # Keep original interior cells
        for (r, c) in color_cells[interior_color]:
            if r < rmin or r > rmax or c < cmin or c > cmax:
                two_cells.append((r, c))

        # New opposite cells: keep original opposite cells, extend diagonally
        # Determine direction
        if four_corner == 'TL':
            opp_dr = 1
            opp dc = 1
        elif four_corner == 'TR':
            opp_dr = 1
            opp_dc = -1
        elif four_corner == 'BL':
            opp_dr = -1
            opp_dc = 1
        elif four_corner == 'BR':
            opp_dr = -1
            opp_dc = -1

        # From each cell in original opposite side, go 6 steps in (opposite_corner direction)
        new_opposite = set()
        for (r, c) in opposite_side:
            for i in range(1, 7):
                nr, nc = r + opp_dr * i, c + opp_dc * i
                if 0 <= nr < H and 0 <= nc < W:
                    new_opposite.add((nr, nc))

        # Keep original 2 cells + new 2 cells
        output = [row[:] for row in input_grid]
        for (r, c) in two_cells:
            if 0 <= r < H and 0 <= c < W:
                output[r][c] = 2
        for (r, c) in new_opposite:
            if 0 <= r < H and 0 <= c < W:
                output[r][c] = opposite_color

        return output
    else:
        return [row[:] for row in input_grid]


========== 137f0df0 a0  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    # Find rows that are all zero - separators
    sep_rows = [r for r in range(H) if all(input_grid[r][c] == 0 for c in range(W))]
    # Separators divide into groups: between rows sep_rows[i] and sep_rows[i+1]
    groups = []
    cur = []
    for r in range(H):
        if r in sep_rows:
            if cur:
                groups.append(cur)
                cur = []
        else:
            cur.append(r)
    if cur:
        groups.append(cur)
    # For each group, find the 5-ranges (contiguous 5s)
    for r in range(H):
        if out[r]:
            continue
        runs = [(c, c + input_grid[r].count(5, c, W)) for c in range(W) if input_grid[r].count(5, c, W) > 0]
        if not runs:
            continue
        # Inspect the group's structure
        if len(groups[-1]) == 2:
            # Two consecutive non-sep rows with 5-runs -> horizontal bars between them
            top, bot = groups[-1][0], groups[-1][1]
            for c1, c2 in runs:
                for c in range(c1, c2 + 1):
                    out[top][c] = 2
                    out[bot][c] = 2
        elif len(groups[-1]) > 2:
            # More than 2 non-sep rows -> box frames around each pair of rows
            # Frame rows: top+1, top+2, bot-2, bot-1
            top, bot = groups[-1][0], groups[-1][-1]
            for rr in [top + 1, top + 2, bot - 2, bot - 1]:
                if 0 <= rr < H:
                    for c1, c2 in runs:
                        for c in range(c1, c2 + 1):
                            out[rr][c] = 2
            # Fill interior with 1 between pairs
            for rr in range(top + 2, bot):
                if 0 <= rr < H:
                    for c1, c2 in runs:
                        for c in range(c1, c2 + 1):
                            out[rr][c] = 1
    return out


========== 137f0df0 a1  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    # Find rows that have 0-lines (not all 0) (horizontal and vertical)
    h_lines_rows = [r for r in range(H) if any(input_grid[r][c] == 0 for c in range(W)) and any(input_grid[r][c] != 0 for c in range(W))]
    v_lines_cols = [c for c in range(W) if any(input_grid[r][c] == 0 for r in range(H)) and any(input_grid[r][c] != 0 for r in range(H))]
    # Mark cells behind each horizontal line-row with 2
    for r in h_lines_rows:
        for c in range(W):
            if input_grid[r][c] == 5:
                out[r][c] = 2
    # Mark cells behind each vertical line-col with 2
    for c in v_lines_cols:
        for r in range(H):
            if input_grid[r][c] == 5:
                out[r][c] = 2
    # A cell is "behind" a line if it hasn't been painted yet AND it's on the side away from the grid edge
    # Actually we need to fill 1s and 2s where 5s aren't present behind each line
    # Clean pass: fill any 0 in a line-row or line-col with the line's color if it hasn't overridden to 2
    for r in h_lines_rows:
        for c in range(W):
            if out[r][c] == 0:
                # column of this row: are there any 5s? Last uncrossed 5 wins
                last_5_c = None
                for cc in range(c+1, W):
                    if input_grid[r][cc] == 5:
                        last_5_c = cc
                if last_5_c is not None and last_5_c != c:
                    out[r][c] = 1
                else:
                    out[r][c] = 2
    for c in v_lines_cols:
        for r in range(H):
            if out[r][c] == 0:
                last_5_r = None
                for rr in range(r+1, H):
                    if input_grid[rr][c] == 5:
                        last_5_r = rr
                if last_5_r is not None and last_5_r != r:
                    out[r][c] = 1
                else:
                    out[r][c] = 2
    return out

root@e3241538a7a6:/workspace/ARC-AGI2# 


========== 1c56ad9f a0  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Find bounding box of non-zero cells
    rs, cs = [], []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != 0:
                rs.append(r)
                cs.append(c)
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    # Color
    c = input_grid[r0][c0]
    # Inner cells (r0+1..r1-1, c0+1..c1-1) should be 0
    for r in range(r0 + 1, r1):
        for c2 in range(c0 + 1, c1):
            input_grid[r][c2] = 0
    # Build output: zeros outside box, color filling the inner (H-1)x(W-1) matrix
    out = [[0] * W for _ in range(H)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = c
    return out


========== 1c56ad9f a1  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Find the bounding rectangle of the filled cells (non-zero)
    rs = [r for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    cs = [c for r in range(H) for c in range(W) if input_grid[r][c] != 0]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    color = input_grid[r0][c0]

    # Build output: same bounding box, rest of that region cleared to 0,
    # leaving the border in place and filling the inside with checkerboard of 0s and color.
    out = [[0] * W for _ in range(H)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r == r0 or r == r1 or c == c0 or c == c1:
                out[r][c] = color
            else:
                # checkerboard: interior cells alternate 0 and color depending on parity
                # Use XOR: if (r+c) is odd -> 0, even -> color
                if (r + c) % 2 == 0:
                    out[r][c] = color
                # else 0
    return out


========== 1e81d6f9 a0  [wrong_training] ==========

def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    # Find the 4x4 grid of 5s
    rs, cs = None, None
    for r in range(h - 3):
        for c in range(w - 3):
            ok = True
            for dr in range(4):
                for dc in range(4):
                    if input_grid[r + dr][c + dc] != 5:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                rs, cs = r, c
                break
        if rs is not None:
            break
    out = [row[:] for row in input_grid]
    for r in range(rs, rs + 4):
        for c in range(cs, cs + 4):
            if input_grid[r][c] == 5:
                out[r][c] = 0
    return out


========== 1e81d6f9 a1  [wrong_training] ==========

def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    # Find the 4x4 region of 5s
    r0 = c0 = -1
    for r in range(h - 3):
        for c in range(w - 3):
            ok = True
            for dr in range(4):
                for dc in range(4):
                    if input_grid[r + dr][c + dc] != 5:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                r0, c0 = r, c
                break
        if r0 != -1:
            break
    out = [row[:] for row in input_grid]
    for r in range(r0, r0 + 4):
        for c in range(c0, c0 + 4):
            out[r][c] = 0
    return out


========== 2546ccf6 a0  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Find separator rows (all 6s)
    sep_rows = [r for r in range(H) if all(input_grid[r][c] == 6 for c in range(W))]
    # Bands are between separators
    bands = []
    for i in range(len(sep_rows) - 1):
        start = sep_rows[i] + 1
        end = sep_rows[i + 1]
        if end > start:
            bands.append((start, end))

    # For each band, find the color that appears as a column-block (non-zero, non-6,
    # contiguous run filling a whole column)
    band_info = []
    for (s, e) in bands:
        col_colors = {}
        for c in range(W):
            col_vals = input_grid[s:e + 1][0][c]
            if col_vals != 0 and col_vals != 6:
                col_color = col_vals
                break
        band_info.append((s, e, col_color))

    # Group bands by color
    color_bands = {}
    for (s, e, col) in band_info:
        color_bands.setdefault(col, []).append((s, e))

    # For each color, find maximum length among bands
    max_lengths = {}
    for col, bds in color_bands.items():
        lengths = [e - s + 1 for (s, e) in bds]
        max_lengths[col] = max(lengths)

    # Find color with greatest max length
    best_color = max(max_lengths, key=lambda col: max_lengths[col])

    # Build output: copy input, then fill entire columns of best_color from row 0
    # to row H-1 (the full height).
    output = [row[:] for row in input_grid]
    for c in range(W):
        col_vals = [input_grid[r][c] for r in range(H)]
        if all(v == best_color for v in col_vals):
            for r in range(H):
                output[r][c] = best_color
    return output

root@e3241538a7a6:/workspace/ARC-AGI2# 

========== 2546ccf6 a1  [wrong_training] ==========

def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    # Find separator rows (all 6s)
    sep_rows = [r for r in range(H) if all(input_grid[r][c] == 6 for c in range(W))]
    # Bands are between separators
    bands = []
    for i in range(len(sep_rows) - 1):
        start = sep_rows[i] + 1
        end = sep_rows[i + 1]
        if end > start:
            bands.append((start, end))

    # For each band, find the color that appears as a column-block (a contiguous
    # vertical run filling the entire band width).
    colors = []
    patterns = []  # list of (row_start, row_end_exclusive, color, n_rows)
    for (s, e) in bands:
        w = e - s + 1
        # Group consecutive columns of same non-zero value into candidates
        candidates = []
        for val in set(input_grid[r][0] for r in range(s, e + 1)):
            if val != 0:
                # Collect cols starting at column c such that for all r in [s,e], grid[r][c] == val
                valid = True
                for r in range(s, e + 1):
                    if input_grid[r][0] != val:
                        valid = False
                        break
                if valid:
                    # Verify this value fills the entire width starting at some column
                    ok = True
                    for c in range(w):
                        if all(input_grid[r][c] == val for r in range(s, e + 1)):
                            candidates.append((val, 0))  # offset c
                            break
        # For each candidate, check it's a full-column block somewhere
        # The offset is the column it starts at relative to some reference
        # We expect exactly one per band
        selected = None
        for cand in candidates:
            val, off = cand
            # Find rows where val forms a full-column block starting at off
            # i.e., for row r in [s,e], input_grid[r][off+c]==val and it fills the entire column
            # Actually we need this to hold for ALL columns from 0..w-1
            # The offset is how much to shift the "leftmost" full column
            # Let's pick the leftmost one: off=0 means full column from start
            # But since candidates are from "consecutive cols", offset 0 means leftmost pattern
            # Generalize: offset 0 => full column starting at col 0; offset 1 => full column starting at col 1; etc.
            # When offset > w, no full column block (since columns index from 0)
            if off < w:
                # Check this is a full-column block of 'val' from col off to end
                ok = True
                for r in range(s, e + 1):
                    for c in range(w):
                        if c >= off and input_grid[r][c] != val:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    selected = (val, off)
                    break
        if selected is None:
            # Fallback: take any full-column block, leftmost offset
            for cand in candidates:
                val, off = cand
                if off < w:
                    selected = (val, off)
                    break
        if selected is None:
            # No full-column blocks? Pick leftmost consecutive col run?
            for val in set(input_grid[r][0] for r in range(s, e + 1)):
                if val != 0:
                    # simple: just use the leftmost column block
                    selected = (val, 0)
                    break
        if selected is None:
            # Still none? Shouldn't happen but fallback
            selected = (0, 0)
        colors.append(selected[0])

    # The unusual color is the one that differs from the rest
    # Count occurrences of each color
    from collections import Counter
    cnt = Counter(colors)
    # The unusual color = the majority color
    unusual = cnt.most_common(1)[0][0]

    # Build output: replace every non-unusual color cell with unusual color
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != unusual:
                out[r][c] = unusual
    return out


========== 2de01db2 a0  [wrong_training] ==========

def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    # Find the column that contains 0s (the odd-one-out column)
    zero_col = None
    for c in range(cols):
        if all(input_grid[r][c] == 0 for r in range(rows)):
            zero_col = c
            break
    # Find the color in the "clean" column (non-zero, non-zero-odd)
    # The clean column is one of the remaining; it has a single color filling it.
    # Find its color by looking at any cell in that column that is non-zero
    clean_col = None
    clean_color = None
    for c in range(cols):
        if c != zero_col:
            clean_col = c
            clean_color = input_grid[0][clean_col]
            break
    # Build output: 0s in odd-one-out col, clean_color filled row-wise from clean col
    output = []
    for r in range(rows):
        row = [0] * cols
        row[zero_col] = 0
        for c in range(cols):
            if c == clean_col:
                row[c] = clean_color
            # fill odd columns with their original values (they are 7 in patterns but we don't copy)
            # actually preserve whatever pattern exists in the input clean col
            # but since clean col has one color filling it, just that color
        output.append(row)
    return output


========== 2de01db2 a1  [wrong_training] ==========

def solve(input_grid):
    rows = len(input_grid)
    cols = len(input_grid[0])
    # Find the special column (the one with mostly 0s and special colors)
    # The special column has a pattern of 7s and other colors excluding 0
    special_col = None
    for c in range(cols):
        # Count non-zero, non-0 colors in this column
        other_colors = set()
        for r in range(rows):
            v = input_grid[r][c]
            if v != 0 and v != 6:
                other_colors.add(v)
        if other_colors:
            special_col = c
            break
    # Find the color in the special column that marks the special cell row
    special_color = None
    for r in range(rows):
        v = input_grid[r][special_col]
        if v != 0 and v != 6:
            special_color = v
            break
    # Find the header row (row 0): it has the special color in columns that are NOT special_col
    header = list(input_grid[0])
    for c in range(cols):
        if c == special_col:
            continue
        # find index of special_color in header[c]
        idx = None
        for i, v in enumerate(header[c]):
            if v == special_color:
                idx = i
                break
        if idx is not None:
            # move header[c][idx] to be the special_color at row idx in column c
            val = header[c][idx]
            header[c][idx] = 0
            if input_grid[idx][c] == special_color:
                input_grid[idx][c] = 0
            header[c][idx] = special_color
    # Build output: 0s in special column, header rows shifted down
    output = []
    for r in range(rows):
        row = []
        if r == 0:
            for c in range(cols):
                row.extend(header[c])
        else:
            for c in range(cols):
                if c == special_col:
                    row.append(special_color)
                else:
                    row.extend(input_grid[r][c])
        output.append(row)
    return output

root@e3241538a7a6:/workspace/ARC-AGI2# 
