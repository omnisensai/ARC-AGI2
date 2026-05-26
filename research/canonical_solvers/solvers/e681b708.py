"""Canonical solver for ARC puzzle e681b708.

Structure: the grid is partitioned by long straight "lines" made of color 1
(horizontal/vertical runs). Colored marker cells (any color other than 0 or 1)
sit at line endpoints and line-line intersections. Inside the rectangular
regions delimited by the lines there are scattered isolated dots of color 1.
Each such dot is recolored to the dominant marker color bordering its region.

infer_T computes, for every isolated dot, the consensus marker color of the
region it belongs to, producing a latent mask {(r,c): new_color}. apply_T copies
the input and overwrites only those masked cells.
"""

from collections import Counter


def _line_mask(g, H, W):
    """Cells that belong to a long straight run of non-background cells."""
    def nz(r, c):
        return 0 <= r < H and 0 <= c < W and g[r][c] != 0
    line = [[False] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if g[r][c] == 0:
                continue
            hl = 1
            cc = c - 1
            while nz(r, cc):
                hl += 1
                cc -= 1
            cc = c + 1
            while nz(r, cc):
                hl += 1
                cc += 1
            vl = 1
            rr = r - 1
            while nz(rr, c):
                vl += 1
                rr -= 1
            rr = r + 1
            while nz(rr, c):
                vl += 1
                rr += 1
            if hl >= 5 or vl >= 5:
                line[r][c] = True
    return line


def _regions(line, H, W):
    """Connected components (4-conn) of cells not belonging to any line."""
    seen = [[False] * W for _ in range(H)]
    comps = []
    for sr in range(H):
        for sc in range(W):
            if line[sr][sc] or seen[sr][sc]:
                continue
            stack = [(sr, sc)]
            comp = []
            while stack:
                r, c = stack.pop()
                if not (0 <= r < H and 0 <= c < W) or seen[r][c] or line[r][c]:
                    continue
                seen[r][c] = True
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((r + dr, c + dc))
            comps.append(comp)
    return comps


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    line = _line_mask(g, H, W)
    comps = _regions(line, H, W)

    T = {}
    for comp in comps:
        # Dots in this region that need recoloring.
        dots = [(r, c) for (r, c) in comp if g[r][c] == 1]
        if not dots:
            continue
        # Consensus marker color: count marker cells (color not in {0,1})
        # adjacent (8-connectivity) to any cell of the region.
        markers = Counter()
        counted = set()
        for r, c in comp:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < H and 0 <= cc < W
                            and (rr, cc) not in counted
                            and g[rr][cc] not in (0, 1)):
                        markers[g[rr][cc]] += 1
                        counted.add((rr, cc))
        if not markers:
            continue
        color = markers.most_common(1)[0][0]
        for r, c in dots:
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
