"""Canonical latent-T solver for ARC puzzle 6a1e5592.

Rule (derived from ALL pairs):
  The grid has a top band of color 2 with 0-cells carved into it (each carved
  0-region is the visible TOP fragment of a hidden shape poking up into the 2
  band), and a bottom field of color-5 shapes that grow up from the floor.

  Each top 0-fragment is matched to the bottom 5-shape whose TOP rows (in its
  original orientation, no rotation/flip) coincide exactly with the fragment.
  That full 5-shape is then redrawn as color 1, translated so its top rows land
  on the fragment cells (i.e. the rest of the shape hangs downward into the
  0-field). All original 5-shapes are erased to background 0.

  Matching is a bijection: when a fragment matches several 5-shapes, fragments
  that have only one available match are assigned first (constraint
  propagation), freeing the ambiguity.

infer_T returns a mask dict {(r,c): 1} of every cell to paint with color 1
(fragments redrawn in place + their downward extensions). apply_T copies the
input, erases color 5, and overwrites masked cells with 1.
"""


def _components(cells):
    """4-connected components of a set of (r,c) cells."""
    cellset = set(cells)
    seen = set()
    out = []
    for cell in cells:
        if cell in seen:
            continue
        stack = [cell]
        cur = set()
        while stack:
            a, b = stack.pop()
            if (a, b) in seen or (a, b) not in cellset:
                continue
            seen.add((a, b))
            cur.add((a, b))
            stack.extend([(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)])
        out.append(cur)
    return out


def _norm(cells):
    """Normalize a set of cells to have min row/col at 0; return sorted list."""
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])

    # Top fragments: 0-cells lying in a row that still contains a 2 (the 2 band).
    rows_with_two = [any(g[r][c] == 2 for c in range(W)) for r in range(H)]
    top_cells = [(r, c) for r in range(H) for c in range(W)
                 if g[r][c] == 0 and rows_with_two[r]]
    fragments = sorted(_components(top_cells), key=lambda f: min(c for r, c in f))

    # Bottom shapes: connected components of color 5.
    five_cells = [(r, c) for r in range(H) for c in range(W) if g[r][c] == 5]
    bottoms = _components(five_cells)

    # For each fragment, list candidate (bottom_index, placed_cells) where the
    # fragment equals the top `fh` rows of the bottom shape (original orientation).
    cands = {}
    for fi, frag in enumerate(fragments):
        fh = max(r for r, c in frag) - min(r for r, c in frag) + 1
        fnorm = frozenset(_norm(frag))
        tr0 = min(r for r, c in frag)
        tc0 = min(c for r, c in frag)
        lst = []
        for bi, b in enumerate(bottoms):
            bn = _norm(b)
            top_rows = [(r, c) for r, c in bn if r < fh]
            if frozenset(_norm(top_rows)) != fnorm:
                continue
            # Align the shape so its top rows sit on the fragment.
            fmr = min(r for r, c in top_rows)
            fmc = min(c for r, c in top_rows)
            dr, dc = tr0 - fmr, tc0 - fmc
            placed = frozenset((r + dr, c + dc) for r, c in bn)
            if all(0 <= r < H and 0 <= c < W for r, c in placed):
                lst.append((bi, placed))
        cands[fi] = lst

    # Bijective assignment via constraint propagation: repeatedly assign any
    # fragment that has exactly one still-available bottom shape.
    assigned = {}
    used_bottoms = set()
    remaining = set(range(len(fragments)))
    progress = True
    while remaining and progress:
        progress = False
        for fi in list(remaining):
            opts = [(bi, pl) for bi, pl in cands[fi] if bi not in used_bottoms]
            if len(opts) == 1:
                bi, pl = opts[0]
                assigned[fi] = pl
                used_bottoms.add(bi)
                remaining.discard(fi)
                progress = True
    # Fallback for any unresolved fragment: take first available option.
    for fi in list(remaining):
        opts = [(bi, pl) for bi, pl in cands[fi] if bi not in used_bottoms]
        if opts:
            bi, pl = opts[0]
            assigned[fi] = pl
            used_bottoms.add(bi)

    # Latent mask: every cell to paint with color 1.
    T = {}
    for pl in assigned.values():
        for r, c in pl:
            T[(r, c)] = 1
    return T


def apply_T(input_grid, T):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    # Erase the original bottom shapes (color 5) to background 0.
    for r in range(H):
        for c in range(W):
            if out[r][c] == 5:
                out[r][c] = 0
    # Overwrite masked cells with their new color.
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
