from collections import Counter


def _bg(grid):
    """Most common color = background."""
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


def _parts(grid, bg):
    """Locate the bordered pattern block in the top-left.

    The block region is the bounding box of all non-background cells.  Its
    right column and bottom row are a solid 'border' color; the remaining
    upper-left rectangle is the pattern 'content'.
    Returns (border_color, content_grid) or None if no block is present.
    """
    H, W = len(grid), len(grid[0])
    cells = [(r, c) for r in range(H) for c in range(W) if grid[r][c] != bg]
    if not cells:
        return None
    r0 = min(r for r, c in cells)
    r1 = max(r for r, c in cells)
    c0 = min(c for r, c in cells)
    c1 = max(c for r, c in cells)
    region = [[grid[r][c] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]
    rh, rw = len(region), len(region[0])
    if rh < 2 or rw < 2:
        return None
    border = region[-1][-1]
    content = [[region[r][c] for c in range(rw - 1)] for r in range(rh - 1)]
    return border, content


def infer_T(input_grid):
    """Infer the latent transformation: a full-grid template (2D color grid).

    Build a fractal from the pattern: for each content cell (R,C), if it holds
    the foreground color place the content as a sub-block, otherwise place the
    content with its foreground recolored to the border color.  The resulting
    (ch*ch) x (cw*cw) fractal is then tiled periodically across the input dims.
    """
    H, W = len(input_grid), len(input_grid[0])
    bg = _bg(input_grid)
    parts = _parts(input_grid, bg)
    if parts is None:
        return [[None] * W for _ in range(H)]
    border, content = parts
    ch, cw = len(content), len(content[0])

    fg_vals = [v for row in content for v in row if v != bg]
    if not fg_vals:
        return [[None] * W for _ in range(H)]
    fgcolor = Counter(fg_vals).most_common(1)[0][0]

    recolored = [[border if content[r][c] == fgcolor else content[r][c]
                  for c in range(cw)] for r in range(ch)]

    fh, fw = ch * ch, cw * cw
    fractal = [[0] * fw for _ in range(fh)]
    for R in range(ch):
        for C in range(cw):
            block = content if content[R][C] == fgcolor else recolored
            for r in range(ch):
                for c in range(cw):
                    fractal[R * ch + r][C * cw + c] = block[r][c]

    # Latent template: fractal tiled periodically over the full grid.
    T = [[fractal[r % fh][c % fw] for c in range(W)] for r in range(H)]
    return T


def apply_T(input_grid, T):
    """Copy input, overwrite each cell wherever the template specifies a color."""
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None:
                out[r][c] = T[r][c]
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
