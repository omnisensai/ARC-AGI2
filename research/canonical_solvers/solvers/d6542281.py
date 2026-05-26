from collections import Counter


def _bg(g):
    c = Counter(v for row in g for v in row)
    return c.most_common(1)[0][0]


def _components(g, bg):
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = {}
                while stack:
                    y, x = stack.pop()
                    cells[(y, x)] = g[y][x]
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != bg and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((ny, nx))
                comps.append(cells)
    return comps


def infer_T(input_grid):
    """Infer the latent overwrite mask.

    Structure: the grid contains multi-color "template" shapes and isolated
    single-color "marker" cells.  Each marker is a copy of one (or more) of a
    template's cells.  A set of markers pins a template placement (the unique
    shift making every marker land on a same-colored template cell).  We stamp
    the complete template at each such placement (filling only background
    cells).  Finally, a template's unique "key" cell (a color that occurs once
    in the template) is erased when no marker anchored on that key color.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _bg(g)
    comps = _components(g, bg)

    templates = []
    markers = []
    for comp in comps:
        if len(set(comp.values())) >= 2:
            templates.append(comp)
        else:
            markers.append(comp)

    marker_cells = {}
    for m in markers:
        for k, v in m.items():
            marker_cells[k] = v

    # enumerate candidate (template, shift) placements anchored by markers
    candidates = []
    for ti, tmpl in enumerate(templates):
        offsets = set()
        for mc, mcol in marker_cells.items():
            for tc, tcol in tmpl.items():
                if tcol == mcol:
                    offsets.add((mc[0] - tc[0], mc[1] - tc[1]))
        for off in offsets:
            if off == (0, 0):
                continue
            valid = True
            matched = set()
            for tc, tcol in tmpl.items():
                ny, nx = tc[0] + off[0], tc[1] + off[1]
                if not (0 <= ny < H and 0 <= nx < W):
                    valid = False
                    break
                cur = g[ny][nx]
                if cur == bg:
                    continue
                if cur == tcol and (ny, nx) in marker_cells:
                    matched.add((ny, nx))
                else:
                    valid = False
                    break
            if valid and matched:
                candidates.append((len(matched), ti, off, frozenset(matched)))

    # greedily accept placements covering the most markers, no marker reused
    candidates.sort(key=lambda x: -x[0])
    used_markers = set()
    placements = []
    anchor_colors = {}  # template index -> set of marker colors used
    for score, ti, off, matched in candidates:
        if matched & used_markers:
            continue
        placements.append((ti, off))
        used_markers |= set(matched)
        ac = anchor_colors.setdefault(ti, set())
        for (my, mx) in matched:
            ac.add(g[my][mx])

    T = {}
    # stamp each placed template onto background cells
    for ti, off in placements:
        tmpl = templates[ti]
        for tc, tcol in tmpl.items():
            ny, nx = tc[0] + off[0], tc[1] + off[1]
            if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == bg:
                T[(ny, nx)] = tcol
    # erase a used template's unique key cell when its color was not anchored
    for ti, ac in anchor_colors.items():
        tmpl = templates[ti]
        cnt = Counter(tmpl.values())
        for (r, c), col in tmpl.items():
            if cnt[col] == 1 and col not in ac:
                T[(r, c)] = bg
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
