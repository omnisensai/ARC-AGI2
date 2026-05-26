"""Canonical solver for ARC puzzle 753ea09b.

Rule (same-size):
  Each grid has three colors: a background (most common), a "structure" color and
  a "marker" color. The structure + marker cells form one long winding RIBBON
  (a band whose two parallel staircase edges are drawn in the structure color and
  whose interior crossings are tagged by the marker color). The transformation
  FILLS the interior of that ribbon with the structure color, leaving the original
  marker cells untouched. Small scattered structure/marker noise (not part of the
  main ribbon) and the two large exterior background regions are left unchanged.

  infer_T: identify bg / structure / marker; find the main ribbon as the largest
  8-connected component of (structure | marker); flood the background into
  4-connected components; the two largest border-touching components are the
  exterior (the ribbon, spanning border to border, splits the outside in two);
  every other background component that 8-touches the main ribbon is interior.
  The latent mask T marks those interior background cells -> structure color.

  apply_T: copy the input and overwrite only the masked cells.
"""

from collections import deque


def _comps8(grid, in_set):
    """8-connected components of cells whose color is in `in_set`."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] in in_set and not seen[r][c]:
                comp = []
                dq = deque([(r, c)])
                seen[r][c] = True
                while dq:
                    a, b = dq.popleft()
                    comp.append((a, b))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            na, nb = a + dr, b + dc
                            if 0 <= na < H and 0 <= nb < W and not seen[na][nb] \
                                    and grid[na][nb] in in_set:
                                seen[na][nb] = True
                                dq.append((na, nb))
                comps.append(comp)
    return comps


def _comps4_bg(grid, bg):
    """4-connected background components, each with a 'touches border' flag."""
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == bg and not seen[r][c]:
                comp = []
                touch = False
                dq = deque([(r, c)])
                seen[r][c] = True
                while dq:
                    a, b = dq.popleft()
                    comp.append((a, b))
                    if a in (0, H - 1) or b in (0, W - 1):
                        touch = True
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        na, nb = a + dr, b + dc
                        if 0 <= na < H and 0 <= nb < W and not seen[na][nb] \
                                and grid[na][nb] == bg:
                            seen[na][nb] = True
                            dq.append((na, nb))
                comps.append((comp, touch))
    return comps


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])

    # Identify colors: background is most common.
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    others = sorted((k for k in counts if k != bg), key=lambda k: -counts[k])

    T = [[None] * W for _ in range(H)]
    if len(others) < 2:
        return T, bg

    # Of the two non-background colors, the more frequent is the ribbon's edge
    # ("structure"), the rarer is the "marker".
    structure, marker = others[0], others[1]

    # Main ribbon = largest 8-connected component of structure | marker cells.
    ribbon_comps = _comps8(input_grid, {structure, marker})
    if not ribbon_comps:
        return T, bg
    main = set(max(ribbon_comps, key=len))

    # Exterior background = the two largest border-touching bg components
    # (a ribbon spanning the grid from border to border splits the outside in two).
    bg_comps = _comps4_bg(input_grid, bg)
    border_comps = sorted((bc for bc in bg_comps if bc[1]),
                          key=lambda x: -len(x[0]))
    exterior = set()
    for comp, _ in border_comps[:2]:
        exterior.update(comp)

    def touches_main(a, b):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if (a + dr, b + dc) in main:
                    return True
        return False

    # Interior background cells (in a non-exterior component that hugs the main
    # ribbon) get filled with the structure color.
    for comp, _ in bg_comps:
        if comp[0] in exterior:
            continue
        if any(touches_main(a, b) for a, b in comp):
            for a, b in comp:
                T[a][b] = structure
    return T, bg


def apply_T(input_grid, T_bundle):
    T, _bg = T_bundle
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
