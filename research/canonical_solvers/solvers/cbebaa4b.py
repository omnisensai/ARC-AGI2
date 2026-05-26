"""Canonical latent-T solver for ARC puzzle cbebaa4b.

Rule (inferred from all train+test pairs):
The input scatters several frame-like objects across an empty (0) field. Each
object has a single main color plus some `2` connector markers sitting at the
tips of its open edges. Exactly one object is a fully-filled solid square -- the
ANCHOR. The objects are jigsaw pieces that assemble into a single connected
structure: the anchor stays fixed, and every other object is translated (no
rotation/reflection) so that one of its open ports docks against an existing
piece, with their `2` markers overlapping. The assembled structure is drawn on
an otherwise-empty grid of the same size; all original scattered cells are
cleared.

infer_T computes, for each cell, the post-assembly color (or 0), as a latent
mask over only the cells that differ from the input. apply_T overwrites just
those masked cells.
"""


def _components(g):
    """8-connected components of all non-zero cells."""
    H, W = len(g), len(g[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0 or seen[r][c]:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < H and 0 <= cc < W) or seen[rr][cc] or g[rr][cc] == 0:
                    continue
                seen[rr][cc] = True
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            stack.append((rr + dr, cc + dc))
            comps.append(cells)
    return comps


def _objinfo(g, cells):
    """Return (main_color, {(r,c): value}) for one object; main = non-2 color."""
    cellmap = {(r, c): g[r][c] for (r, c) in cells}
    colors = {v for v in cellmap.values() if v != 2}
    main = next(iter(colors)) if colors else 2
    return main, cellmap


def _assemble(input_grid):
    """Return {color: (dr, dc)} placement offsets for each object."""
    objs = {}
    for cells in _components(input_grid):
        m, cm = _objinfo(input_grid, cells)
        objs[m] = cm

    # Anchor = the object whose main-color cells fully fill its bounding box.
    anchor = None
    for m, cm in objs.items():
        colorcells = [(r, c) for (r, c), v in cm.items() if v == m]
        rs = [r for r, c in colorcells]
        cs = [c for r, c in colorcells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if len(colorcells) == area:
            anchor = m
            break
    if anchor is None:
        # Fallback: largest object.
        anchor = max(objs, key=lambda m: len(objs[m]))

    placed = {anchor: (0, 0)}

    def current_state():
        twoowner = {}
        colorset = set()
        for m, (dr, dc) in placed.items():
            for (r, c), v in objs[m].items():
                if v == 2:
                    twoowner.setdefault((r + dr, c + dc), set()).add(m)
                else:
                    colorset.add((r + dr, c + dc))
        return twoowner, colorset

    remaining = set(objs) - {anchor}
    progress = True
    while remaining and progress:
        progress = False
        twoowner, pcolor = current_state()
        placed_twos = set(twoowner)
        for m in list(remaining):
            cm = objs[m]
            mtwos = [(r, c) for (r, c), v in cm.items() if v == 2]
            mcolor = [(r, c) for (r, c), v in cm.items() if v != 2]
            # Candidate offsets: align one of this object's 2-markers onto a
            # placed 2-marker.
            cand = set()
            for (mr, mc) in mtwos:
                for (pr, pc) in placed_twos:
                    cand.add((pr - mr, pc - mc))
            best = None
            for (dr, dc) in cand:
                overlap = [(r + dr, c + dc) for (r, c) in mtwos
                           if (r + dr, c + dc) in placed_twos]
                if len(overlap) < 2:
                    continue
                # All overlapping placed markers must belong to a single
                # existing object (one coherent port-to-port docking).
                owners = set()
                for x in overlap:
                    owners |= twoowner[x]
                if len(owners) != 1:
                    continue
                # Color cells must not collide with placed color cells.
                if any((r + dr, c + dc) in pcolor for (r, c) in mcolor):
                    continue
                score = len(overlap)
                if best is None or score > best[2]:
                    best = (dr, dc, score)
            if best is not None:
                placed[m] = (best[0], best[1])
                remaining.discard(m)
                progress = True
    return objs, placed


def infer_T(input_grid):
    """Compute the latent transformation mask {(r,c): new_color} of changed cells."""
    H, W = len(input_grid), len(input_grid[0])
    objs, placed = _assemble(input_grid)

    # Build the assembled target grid.
    target = [[0] * W for _ in range(H)]
    for m, (dr, dc) in placed.items():
        for (r, c), v in objs[m].items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W:
                target[nr][nc] = v

    # Mask = cells where the target differs from the input.
    T = {}
    for r in range(H):
        for c in range(W):
            if target[r][c] != input_grid[r][c]:
                T[(r, c)] = target[r][c]
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
