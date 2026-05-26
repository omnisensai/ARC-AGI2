"""Canonical solver for ARC puzzle 98c475bf.

Rule
----
The grid has a one-cell border frame (color = the four corners) down columns 0
and W-1.  Inside, two kinds of single-colored objects appear:

  * a "drawn glyph": one color forming a full horizontal line spanning the
    interior columns (1..W-2) plus a small fixed decoration above/below it;
  * one or more "markers": a color present as exactly two cells, one against the
    left interior column (col 1) and one against the right interior column
    (col W-2), sitting on a single row R.

Transformation:
  * every marker is replaced by that color's full glyph (line + decoration),
    drawn with its horizontal line on the marker's row R;
  * the pre-existing drawn glyph is erased (its cells become background 0).

Each color owns a fixed glyph shape (a "consensus template" invariant across the
whole task), expressed as offsets (dr, c): dr = row offset from the line row,
c = absolute interior column.  infer_T selects the template per marker color and
positions it; apply_T overwrites only the masked cells.
"""

# Per-color glyph templates: color -> frozenset of (row_offset_from_line, abs_col).
# Line row offset is 0; interior columns run 1..W-2 (==18 for the 20-wide grids).
GLYPH_TEMPLATES = {
    1: {(-1, 14), (-1, 16), (1, 14), (1, 16)} | {(0, c) for c in range(1, 19)},
    2: {(-2, 6), (-2, 8), (-1, 7), (1, 7), (2, 6), (2, 8)} | {(0, c) for c in range(1, 19)},
    3: {(-2, 5), (-1, 4), (-1, 6), (1, 4), (1, 6), (2, 5)}
       | {(0, c) for c in range(1, 19) if c not in (4, 5, 6)},
    6: {(-2, 2), (-2, 3), (-2, 4), (-1, 2), (-1, 4), (1, 2), (1, 4),
        (2, 2), (2, 4), (3, 2), (3, 3), (3, 4)}
       | {(0, c) for c in range(1, 19) if c != 3},
    7: {(-2, 13), (-2, 15), (-1, 13), (-1, 15), (1, 13), (1, 15),
        (2, 13), (2, 15)} | {(0, c) for c in range(1, 19)},
}


def infer_T(input_grid):
    """Compute the latent transformation mask {(r, c): new_color}."""
    H = len(input_grid)
    W = len(input_grid[0])
    border = input_grid[0][0]

    # Collect interior cells per color (exclude the border frame in cols 0/W-1).
    cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == 0:
                continue
            if c in (0, W - 1) and v == border:
                continue
            cells.setdefault(v, []).append((r, c))

    T = {}

    for color, cs in cells.items():
        if len(cs) == 2:
            # Candidate marker pair: two cells against both interior edges,
            # on the same row, with a known glyph template.
            rows = {r for r, _ in cs}
            cols = {c for _, c in cs}
            if (len(rows) == 1 and cols == {1, W - 2}
                    and color in GLYPH_TEMPLATES):
                line_row = next(iter(rows))
                for dr, c in GLYPH_TEMPLATES[color]:
                    rr = line_row + dr
                    if 0 <= rr < H and 0 <= c < W:
                        T[(rr, c)] = color
        else:
            # The pre-existing drawn glyph: erase every one of its cells.
            for (r, c) in cs:
                T[(r, c)] = 0

    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
