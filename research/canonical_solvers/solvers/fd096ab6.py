"""Canonical solver for ARC puzzle fd096ab6.

Rule: the grid contains one complete "template" shape (the colored object with
the most cells) plus several smaller fragments, each in its own color. Every
fragment is a translated subset of the template. For each fragment we find the
unique translation that aligns its cells onto a subset of the template, then we
draw the full template shape at that location in the fragment's color (the
fragment's existing cells stay put; the missing template cells are filled in).
"""


def _components(grid, bg):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not seen[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if seen[rr][cc] or grid[rr][cc] != color:
                        continue
                    seen[rr][cc] = True
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr or dc:
                                stack.append((rr + dr, cc + dc))
                comps.append((color, cells))
    return comps


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def infer_T(input_grid):
    """Return a dict {(r, c): color} of cells to overwrite (the latent mask)."""
    H, W = len(input_grid), len(input_grid[0])
    bg = _background(input_grid)

    # Group colored cells by color (a fragment may be split into several
    # 8-connected components, so group on color rather than component).
    by_color = {}
    for color, cells in _components(input_grid, bg):
        by_color.setdefault(color, []).extend(cells)

    if not by_color:
        return {}

    # Template = the color with the most cells; it is left unchanged.
    tcolor = max(by_color, key=lambda k: len(by_color[k]))
    tset = set(by_color[tcolor])
    trs = [r for r, _ in tset]
    tcs = [c for _, c in tset]
    th = max(trs) - min(trs) + 1
    tw = max(tcs) - min(tcs) + 1

    # A fragment fits inside the template's bounding box, so two same-colored
    # cells belong to the same fragment only if they are within that extent.
    # Cluster each color's cells by single-linkage on Chebyshev proximity.
    fragments = []
    for color, cells in by_color.items():
        if color == tcolor:
            continue
        remaining = list(cells)
        while remaining:
            cluster = [remaining.pop()]
            changed = True
            while changed:
                changed = False
                for cell in list(remaining):
                    r, c = cell
                    if any(abs(r - er) < th and abs(c - ec) < tw
                           for er, ec in cluster):
                        cluster.append(cell)
                        remaining.remove(cell)
                        changed = True
            fragments.append((color, cluster))

    T = {}
    for color, cells in fragments:
        cset = set(cells)
        # Find translations (dr, dc) so that fragment+offset lies inside template.
        translations = set()
        for tr, tc in tset:
            for fr, fc in cset:
                dr, dc = tr - fr, tc - fc
                if all((r + dr, c + dc) in tset for r, c in cset):
                    translations.add((dr, dc))
        if len(translations) != 1:
            # Ambiguous or no alignment: skip this fragment.
            continue
        dr, dc = translations.pop()
        # Draw the full template, shifted back so the fragment keeps its place.
        for r, c in tset:
            nr, nc = r - dr, c - dc
            if 0 <= nr < H and 0 <= nc < W:
                T[(nr, nc)] = color

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
