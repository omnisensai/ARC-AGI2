"""Canonical solver for ARC puzzle 66ac4c3b.

Rule
----
The grid contains two parallel "anchor" lines, each a row or column of
evenly-spaced single-color markers. One line (the TEMPLATE anchor) has a
connected shape attached to one side, drawn in the SHAPE color; the markers of
this anchor are a distinct MARKER color that appears nowhere else. The other
line (the TARGET anchor) is bare and is itself drawn in the SHAPE color.

The transformation reflects the attached shape across the target anchor (to the
opposite side from where it sits on the template anchor), and paints those
reflected cells with the MARKER color. Everything else is left unchanged.
"""

from collections import Counter


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def _find_anchor_lines(grid, bg):
    """Return lines of >=3 evenly-spaced single-color markers.

    Each entry: {'orient': 'row'|'col', 'idx', 'color', 'pos': sorted offsets}.
    """
    H, W = len(grid), len(grid[0])
    lines = []
    for c in range(W):
        cells = [(r, grid[r][c]) for r in range(H) if grid[r][c] != bg]
        if len(cells) < 3 or len(set(v for _, v in cells)) != 1:
            continue
        rows = sorted(r for r, _ in cells)
        diffs = set(rows[i + 1] - rows[i] for i in range(len(rows) - 1))
        if len(diffs) == 1 and next(iter(diffs)) >= 2:
            lines.append({'orient': 'col', 'idx': c,
                          'color': cells[0][1], 'pos': rows})
    for r in range(H):
        cells = [(c, grid[r][c]) for c in range(W) if grid[r][c] != bg]
        if len(cells) < 3 or len(set(v for _, v in cells)) != 1:
            continue
        cols = sorted(c for c, _ in cells)
        diffs = set(cols[i + 1] - cols[i] for i in range(len(cols) - 1))
        if len(diffs) == 1 and next(iter(diffs)) >= 2:
            lines.append({'orient': 'row', 'idx': r,
                          'color': cells[0][1], 'pos': cols})
    return lines


def infer_T(input_grid):
    """Compute the latent mask: {(r, c): new_color} for cells to overwrite."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)
    lines = _find_anchor_lines(input_grid, bg)
    if len(lines) != 2:
        return {}

    counts = Counter(v for row in input_grid for v in row)
    # Template anchor: its color (the MARKER color) appears exactly as many
    # times as there are markers (no shape drawn in it). Target anchor's color
    # is the SHAPE color and appears more often (shape + bare markers).
    a, b = lines
    a_only = counts[a['color']] == len(a['pos'])
    b_only = counts[b['color']] == len(b['pos'])
    if a_only and not b_only:
        template, target = a, b
    elif b_only and not a_only:
        template, target = b, a
    else:
        return {}

    marker_color = template['color']
    shape_color = target['color']

    # Collect shape cells: cells of the shape color that are not the bare
    # target-anchor markers themselves.
    target_cells = set()
    if target['orient'] == 'col':
        for r in target['pos']:
            target_cells.add((r, target['idx']))
    else:
        for c in target['pos']:
            target_cells.add((target['idx'], c))

    shape_cells = [(r, c) for r in range(H) for c in range(W)
                   if input_grid[r][c] == shape_color and (r, c) not in target_cells]

    # Reflect each shape cell across the target anchor, mirroring the offset.
    T = {}
    if template['orient'] == 'col':
        t_idx, g_idx = template['idx'], target['idx']
        for r, c in shape_cells:
            nc = g_idx - (c - t_idx)
            if 0 <= nc < W:
                T[(r, nc)] = marker_color
    else:  # 'row'
        t_idx, g_idx = template['idx'], target['idx']
        for r, c in shape_cells:
            nr = g_idx - (r - t_idx)
            if 0 <= nr < H:
                T[(nr, c)] = marker_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
