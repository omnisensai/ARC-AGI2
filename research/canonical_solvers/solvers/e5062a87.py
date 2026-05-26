"""Canonical latent-T solver for ARC puzzle e5062a87.

Rule (inferred from input structure alone):
- The grid is a noise field of foreground (the dominant non-background color
  among the 5/0-style pattern) and background, with a small marker drawn in a
  distinct color (the marker color is the least frequent color whose cells form
  the marker shape; here it sits on foreground cells).
- The marker is a shape sitting on FOREGROUND cells. Reconstruct the "base"
  grid by treating the marker cells as foreground.
- Find every other location where the SAME shape (same orientation/translation)
  lands entirely on BACKGROUND cells, i.e. the marker's congruent "shadow".
  A placement is only accepted when the cells geometrically enclosed by the
  shape (background cells whose 4 orthogonal neighbours all belong to the shape)
  map onto foreground -- this keeps hollow shapes (e.g. a diamond ring) hollow.
- Overlapping candidate placements are resolved by preferring the one whose
  background shape is the tightest (fewest background cells leaking out of its
  immediate 8-neighbourhood).
- A degenerate single-line marker (1 cell thick) is axial: its shadows are
  constrained to lie on the marker's own row (horizontal line) or column
  (vertical line).
- Stamp the marker color onto every accepted background placement.

infer_T returns a latent mask {(r,c): color}; apply_T overwrites only those cells.
"""


def _analyze(input_grid):
    """Identify (marker_color, fg, bg).

    The marker is the least frequent color. It is drawn ON the foreground, and
    the transformation stamps the marker color onto BACKGROUND cells.  The two
    main colors must be classified into foreground / background using only the
    input structure:
      * If the marker shape encloses any cells (e.g. a hollow ring/diamond),
        those enclosed cells lie on the foreground -> their majority color = fg.
      * Otherwise (solid / line markers) the marker is embedded in foreground,
        so the majority color on the marker's orthogonal border = fg.
    """
    H = len(input_grid)
    W = len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    marker_color = min(counts, key=counts.get)
    others = [k for k in counts if k != marker_color]
    if len(others) < 2:
        # Degenerate: only one main color; treat it as background.
        bg = others[0] if others else marker_color
        fg = bg
        return H, W, fg, bg, marker_color

    marker = set((r, c) for r in range(H) for c in range(W)
                 if input_grid[r][c] == marker_color)
    rs = [r for r, c in marker]
    cs = [c for r, c in marker]
    r0, c0 = min(rs), min(cs)
    relset = set((r - r0, c - c0) for r, c in marker)
    hh = max(r for r, c in marker) - r0 + 1
    ww = max(c for r, c in marker) - c0 + 1
    enclosed = [(r0 + dr, c0 + dc)
                for dr in range(hh) for dc in range(ww)
                if (dr, dc) not in relset
                and all((dr + a, dc + b) in relset
                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]

    score = {k: 0 for k in others}
    if enclosed:
        for r, c in enclosed:
            v = input_grid[r][c]
            if v in score:
                score[v] += 1
    else:
        for r, c in marker:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + a, c + b
                if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in marker:
                    v = input_grid[nr][nc]
                    if v in score:
                        score[v] += 1
    fg = max(score, key=score.get)
    bg = others[0] if others[1] == fg else others[1]
    return H, W, fg, bg, marker_color


def infer_T(input_grid):
    H, W, fg, bg, marker_color = _analyze(input_grid)

    marker = [(r, c) for r in range(H) for c in range(W)
              if input_grid[r][c] == marker_color]
    if not marker:
        return {}

    def is_bg(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] == bg

    def is_fg(r, c):
        # foreground = in grid and not background (marker cells count as fg too)
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] != bg

    rs = [r for r, c in marker]
    cs = [c for r, c in marker]
    r0, c0 = min(rs), min(cs)
    rel = [(r - r0, c - c0) for r, c in marker]
    relset = set(rel)
    hh = max(r for r, c in rel) + 1
    ww = max(c for r, c in rel) + 1

    # Cells enclosed by the shape (must be foreground at a valid placement).
    enclosed = [(dr, dc)
                for dr in range(hh) for dc in range(ww)
                if (dr, dc) not in relset
                and all((dr + a, dc + b) in relset
                        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]

    is_hline = (hh == 1)
    is_vline = (ww == 1)

    candidates = []
    for tr in range(H - hh + 1):
        for tc in range(W - ww + 1):
            # all shape cells must be background
            if not all(is_bg(tr + dr, tc + dc) for dr, dc in rel):
                continue
            # enclosed cells must be foreground
            if not all(is_fg(tr + dr, tc + dc) for dr, dc in enclosed):
                continue
            # axial constraint for degenerate line markers
            if is_hline and is_vline:
                pass
            elif is_hline:
                if tr != r0:
                    continue
            elif is_vline:
                if tc != c0:
                    continue
            cells = frozenset((tr + dr, tc + dc) for dr, dc in rel)
            # leakage = background cells in the 8-neighbourhood outside the shape
            leak = 0
            for dr, dc in rel:
                for a in (-1, 0, 1):
                    for b in (-1, 0, 1):
                        if (a or b) and (dr + a, dc + b) not in relset:
                            if is_bg(tr + dr + a, tc + dc + b):
                                leak += 1
            candidates.append((cells, leak))

    # Resolve overlaps: prefer tighter (lower-leak) placements.
    candidates.sort(key=lambda x: (x[1], sorted(x[0])))
    kept = []
    used = set()
    for cells, leak in candidates:
        if cells & used:
            continue
        kept.append(cells)
        used |= cells

    T = {}
    for cells in kept:
        for (r, c) in cells:
            T[(r, c)] = marker_color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
