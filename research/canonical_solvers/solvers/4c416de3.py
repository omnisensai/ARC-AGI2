from collections import Counter

# Puzzle 4c416de3
#
# Rule: the grid contains rectangular "boxes" outlined in color 0 (some are
# partial / L-shaped). Inside each box sit single-cell colored markers, each
# lying on an inward diagonal from one box corner. Exactly one marker anywhere
# in the grid already has its full "arrowhead" drawn at its corner -- that is
# the global TEMPLATE shape. Every marker (in every box) gets that template
# arrowhead stamped at its corner, in the marker's color, reflected so the
# arrowhead always points outward from the box.
#
# Canonical latent-T form: infer_T builds a {(r,c): new_color} mask from the
# input structure (boxes, corners, markers, template); apply_T overwrites only
# the masked cells of a copy of the input.

_NEI8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _components(g, H, W, accept):
    """8-connected components of cells where accept(value) is True, grouped by
    requiring identical color within a component."""
    seen = set()
    comps = []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if (r, c) in seen or not accept(v):
                continue
            stack = [(r, c)]
            comp = []
            while stack:
                y, x = stack.pop()
                if (y, x) in seen or not (0 <= y < H and 0 <= x < W) or g[y][x] != v:
                    continue
                seen.add((y, x))
                comp.append((y, x))
                for dy, dx in _NEI8:
                    stack.append((y + dy, x + dx))
            comps.append(comp)
    return comps


def _bbox(cells):
    rs = [y for y, x in cells]
    cs = [x for y, x in cells]
    return min(rs), max(rs), min(cs), max(cs)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    g = input_grid

    # Background = most common color; outline color is 0.
    bg = Counter(v for row in g for v in row).most_common(1)[0][0]

    # Boxes: connected components of the outline color 0.
    boxes = _components(g, H, W, lambda v: v == 0)

    # Colored marker/arrow components (anything that is not background and not 0).
    color_comps = _components(g, H, W, lambda v: v != bg and v != 0)
    if not boxes or not color_comps:
        return {}

    # Template = the largest colored component: the one pre-drawn arrowhead.
    templ_comp = max(color_comps, key=len)
    tcy = sum(y for y, x in templ_comp) / len(templ_comp)
    tcx = sum(x for y, x in templ_comp) / len(templ_comp)

    def corners_of(box):
        r0, r1, c0, c1 = _bbox(box)
        return [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]

    # The box the template attaches to: nearest box corner to the template centroid.
    templ_box = min(
        boxes,
        key=lambda b: min((tcy - a) ** 2 + (tcx - bb) ** 2 for a, bb in corners_of(b)),
    )
    tcr, tcc = min(
        corners_of(templ_box),
        key=lambda k: (tcy - k[0]) ** 2 + (tcx - k[1]) ** 2,
    )
    tr0, tr1, tc0, tc1 = _bbox(templ_box)
    tod_r = 1 if tcr == tr1 else -1   # outward row direction at template corner
    tod_c = 1 if tcc == tc1 else -1   # outward col direction

    # Canonicalize template cells relative to its corner, flipped to outward (+,+).
    canon = {((1 if tod_r > 0 else -1) * (y - tcr),
              (1 if tod_c > 0 else -1) * (x - tcc)) for (y, x) in templ_comp}

    # Stamp the template at every marker's corner.
    T = {}
    for box in boxes:
        r0, r1, c0, c1 = _bbox(box)
        box_corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
        for y in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                color = g[y][x]
                if color == bg or color == 0:
                    continue
                # Corner whose inward diagonal best aligns with this marker.
                best = None
                for (cr0, cc0) in box_corners:
                    dr = (y - cr0) if cr0 == r0 else (cr0 - y)   # inward-positive
                    dc = (x - cc0) if cc0 == c0 else (cc0 - x)
                    key = (abs(dr - dc), dr * dr + dc * dc)
                    if best is None or key < best[0]:
                        best = (key, cr0, cc0)
                _, cr, cc = best
                sr = 1 if cr == r1 else -1     # outward row dir at this corner
                sc = 1 if cc == c1 else -1
                for (rr, ccc) in canon:
                    ny, nx = cr + sr * rr, cc + sc * ccc
                    if 0 <= ny < H and 0 <= nx < W:
                        T[(ny, nx)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
