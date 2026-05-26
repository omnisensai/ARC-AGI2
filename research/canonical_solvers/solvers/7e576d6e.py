"""Canonical latent-T solver for ARC puzzle 7e576d6e.

Rule: the grid contains a stack of parallel "wall" lines (full rows OR full
columns of a single wall color), each wall pierced by a 3-cell "gate" of a
distinct gate color. Two isolated marker cells (a third color) sit on the two
extreme sides of the wall stack. A snake of the marker color is drawn that
starts at one marker, threads through the CENTER of every gate in order, and
ends at the other marker. Between walls the snake runs at distance 1 from the
wall on its approach side, then crosses straight through the gate center.

infer_T computes the snake as a dict mask {(r,c): marker_color}; apply_T copies
the input and paints those cells.
"""

from collections import Counter


def _classify(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    cnt = Counter(v for row in input_grid for v in row)
    bg = cnt.most_common(1)[0][0]
    nonbg = [c for c, _ in cnt.most_common() if c != bg]
    wall_color = nonbg[0]  # most common non-background color forms the walls

    def row_is_wall(r):
        return sum(1 for v in input_grid[r] if v == wall_color) >= W // 2

    def col_is_wall(c):
        return sum(1 for r in range(H) if input_grid[r][c] == wall_color) >= H // 2

    wall_rows = [r for r in range(H) if row_is_wall(r)]
    wall_cols = [c for c in range(W) if col_is_wall(c)]
    horizontal = len(wall_rows) >= len(wall_cols)
    return bg, wall_color, wall_rows, wall_cols, horizontal


def _find_markers(input_grid, bg, wall_color, gate_color):
    H, W = len(input_grid), len(input_grid[0])
    markers = []
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg and v != wall_color and v != gate_color:
                markers.append((r, c))
    return markers


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg, wall_color, wall_rows, wall_cols, horizontal = _classify(input_grid)

    T = {}  # latent mask: {(r, c): new_color}

    def hline(r, c0, c1, color):
        for c in range(min(c0, c1), max(c0, c1) + 1):
            if input_grid[r][c] == bg:
                T[(r, c)] = color

    def vline(c, r0, r1, color):
        for r in range(min(r0, r1), max(r0, r1) + 1):
            if input_grid[r][c] == bg:
                T[(r, c)] = color

    if horizontal:
        walls = sorted(wall_rows)
        gate_cells, gate_colors = {}, Counter()
        for wr in walls:
            cols = [c for c in range(W) if input_grid[wr][c] != wall_color]
            for c in cols:
                gate_colors[input_grid[wr][c]] += 1
            gate_cells[wr] = sorted(cols)
        gate_color = gate_colors.most_common(1)[0][0] if gate_colors else None
        markers = _find_markers(input_grid, bg, wall_color, gate_color)
        marker_color = input_grid[markers[0][0]][markers[0][1]]
        gate_center = {wr: cs[len(cs) // 2] for wr, cs in gate_cells.items()}

        markers.sort()  # smaller row = start (before first wall)
        m_start, m_end = markers[0], markers[-1]
        cr, cc = m_start
        for wr in walls:
            gc = gate_center[wr]
            approach = wr - 1 if cr < wr else wr + 1
            vline(cc, cr, approach, marker_color)
            hline(approach, cc, gc, marker_color)
            T[(wr, gc)] = marker_color  # cross gate center
            cc, cr = gc, wr
        vline(cc, cr, m_end[0], marker_color)
        hline(m_end[0], cc, m_end[1], marker_color)
    else:
        walls = sorted(wall_cols)
        gate_cells, gate_colors = {}, Counter()
        for wc in walls:
            rows = [r for r in range(H) if input_grid[r][wc] != wall_color]
            for r in rows:
                gate_colors[input_grid[r][wc]] += 1
            gate_cells[wc] = sorted(rows)
        gate_color = gate_colors.most_common(1)[0][0] if gate_colors else None
        markers = _find_markers(input_grid, bg, wall_color, gate_color)
        marker_color = input_grid[markers[0][0]][markers[0][1]]
        gate_center = {wc: rs[len(rs) // 2] for wc, rs in gate_cells.items()}

        markers.sort(key=lambda p: p[1])  # smaller col = start
        m_start, m_end = markers[0], markers[-1]
        cr, cc = m_start
        for wc in walls:
            gr = gate_center[wc]
            approach = wc - 1 if cc < wc else wc + 1
            hline(cr, cc, approach, marker_color)
            vline(approach, cr, gr, marker_color)
            T[(gr, wc)] = marker_color  # cross gate center
            cc, cr = wc, gr
        hline(cr, cc, m_end[1], marker_color)
        vline(m_end[1], cr, m_end[0], marker_color)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
