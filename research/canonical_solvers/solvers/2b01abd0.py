def find_line(g):
    """Locate the full-length divider line made of color 1."""
    H, W = len(g), len(g[0])
    for r in range(H):
        if all(g[r][c] == 1 for c in range(W)):
            return ('h', r)
    for c in range(W):
        if all(g[r][c] == 1 for r in range(H)):
            return ('v', c)
    return None


def infer_T(input_grid):
    """
    Build the latent overwrite mask {(r,c): new_color}.

    Structure: a divider line (color 1) splits the grid. On one side is a shape
    drawn in exactly two non-background colors: a frequent 'body' color and a
    rare 'marker' color. The transformation:
      1) recolours the original shape in place, swapping body <-> marker;
      2) places a mirror reflection of the shape across the divider, keeping the
         shape's ORIGINAL colours.
    """
    g = input_grid
    H, W = len(g), len(g[0])

    line = find_line(g)
    if line is None:
        return {}
    ori, idx = line

    # Two shape colours (anything that is not background 0 or divider 1).
    cnt = {}
    for row in g:
        for v in row:
            if v not in (0, 1):
                cnt[v] = cnt.get(v, 0) + 1
    if len(cnt) != 2:
        return {}
    colors = sorted(cnt, key=lambda k: cnt[k])
    rare, body = colors[0], colors[1]
    swap = {body: rare, rare: body}

    cells = [(r, c, g[r][c]) for r in range(H) for c in range(W)
             if g[r][c] in (body, rare)]

    T = {}
    # 1) original side: swap the two colours.
    for r, c, v in cells:
        T[(r, c)] = swap[v]
    # 2) mirrored side: reflect across the divider, original colours.
    for r, c, v in cells:
        if ori == 'v':
            mr, mc = r, 2 * idx - c
        else:
            mr, mc = 2 * idx - r, c
        if 0 <= mr < H and 0 <= mc < W:
            T[(mr, mc)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
