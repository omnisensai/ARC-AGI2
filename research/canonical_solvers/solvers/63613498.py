from collections import Counter


def get_components(grid, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    if not (0 <= cr < H and 0 <= cc < W):
                        continue
                    if seen[cr][cc] or grid[cr][cc] != color:
                        continue
                    seen[cr][cc] = True
                    cells.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((cr + dr, cc + dc))
                comps.append((color, cells))
    return comps


def norm(cells):
    mr = min(c[0] for c in cells)
    mc = min(c[1] for c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def infer_T(input_grid):
    """Latent mask: locate the legend box (region enclosed by an L of color-5
    border cells in the top-left). The colored shape inside the box is the
    template. Find every other object whose normalized shape matches the
    template and mark its cells to be recolored to 5."""
    H, W = len(input_grid), len(input_grid[0])
    T = [[None] * W for _ in range(H)]
    comps = get_components(input_grid, H, W)

    # collect all color-5 (border) cells; the legend border is an L: one full
    # column (vertical side) and one full row (horizontal side).
    five_cells = set()
    for color, cells in comps:
        if color == 5:
            five_cells |= set(cells)
    if not five_cells:
        return T
    border_row = max(Counter(r for r, _ in five_cells).items(), key=lambda kv: kv[1])[0]
    border_col = max(Counter(c for _, c in five_cells).items(), key=lambda kv: kv[1])[0]

    def inside_box(cells):
        return all(r < border_row and c < border_col for r, c in cells)

    template = None
    for color, cells in comps:
        if color == 5:
            continue
        if inside_box(cells):
            template = norm(cells)
            break
    if template is None:
        return T

    for color, cells in comps:
        if color == 5 or inside_box(cells):
            continue
        if norm(cells) == template:
            for r, c in cells:
                T[r][c] = 5
    return T


def apply_T(input_grid, T):
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
