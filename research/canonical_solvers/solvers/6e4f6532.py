"""Canonical solver for ARC task 6e4f6532.

Rule (inferred from all pairs):
  The grid is split into rectangular regions by 2-wide colored frame bands
  (outer borders + internal dividers); each region's four walls carry colors.
  Floating in the regions are:
    * "objects": connected clumps of color-8 cells that contain one or more
      embedded 9 cells, plus a few "marker" cells whose colors equal a frame
      band color (each marker indicates which wall that edge should face).
    * "targets": small isolated groups of 9 cells (no 8 adjacent).
  Each object is matched to the target whose 9-shape is congruent (same number
  of 9 cells, mappable by a rotation/reflection).  The object is rotated /
  reflected so its embedded-9 cells coincide with the target's 9 cells AND its
  marker cells lie as close as possible to the frame bands of matching color.
  The object is erased from its original spot (filled with background) and
  redrawn, oriented, on top of the target.

infer_T builds a latent overwrite mask {(r,c): new_color}: original object
cells -> background, destination cells -> object colors.
"""

from collections import Counter, deque


# the 8 dihedral transforms of a point (r, c) about the origin
def _tf(p, t):
    r, c = p
    return [(r, c), (c, -r), (-r, -c), (-c, r),
            (r, -c), (-r, c), (c, r), (-c, -r)][t]


def _detect_bands(inp):
    """Return (bg, vbands{col:color}, hbands{row:color}) describing the frame."""
    H, W = len(inp), len(inp[0])
    bg = Counter(v for row in inp for v in row).most_common(1)[0][0]
    vb, hb = {}, {}
    for c in range(W):
        col = [inp[r][c] for r in range(H)]
        mc, n = Counter(col).most_common(1)[0]
        if mc != bg and n >= 0.8 * H:
            vb[c] = mc
    for r in range(H):
        mc, n = Counter(inp[r]).most_common(1)[0]
        if mc != bg and n >= 0.8 * W:
            hb[r] = mc
    return bg, vb, hb


def _components(inp, pred):
    """8-connected components of cells satisfying pred(r, c)."""
    H, W = len(inp), len(inp[0])
    seen = [[False] * W for _ in range(H)]
    res = []
    for r in range(H):
        for c in range(W):
            if pred(r, c) and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    rr, cc = q.popleft()
                    cells.append((rr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            nr, nc = rr + dr, cc + dc
                            if (0 <= nr < H and 0 <= nc < W
                                    and not seen[nr][nc] and pred(nr, nc)):
                                seen[nr][nc] = True
                                q.append((nr, nc))
                res.append(cells)
    return res


def infer_T(input_grid):
    inp = input_grid
    H, W = len(inp), len(inp[0])
    bg, vb, hb = _detect_bands(inp)

    def is_frame(r, c):
        return (c in vb) or (r in hb)

    # foreground (non-bg, non-frame) connected components
    comps = _components(inp, lambda r, c: inp[r][c] != bg and not is_frame(r, c))
    objects = [o for o in comps if any(inp[r][c] == 8 for r, c in o)]
    targets = [o for o in comps if all(inp[r][c] == 9 for r, c in o)]

    T = {}
    used = set()
    for o in objects:
        odict = {(r, c): inp[r][c] for r, c in o}
        keys = list(odict)
        nines = [(r, c) for r, c in o if inp[r][c] == 9]
        best = None  # (score, target_index, placed_dict)
        for ti, t in enumerate(targets):
            if ti in used or len(t) != len(nines) or not nines:
                continue
            tg = sorted(t)
            for tr in range(8):
                tn = [_tf(p, tr) for p in nines]
                tn_s = sorted(tn)
                dr = tg[0][0] - tn_s[0][0]
                dc = tg[0][1] - tn_s[0][1]
                if set((r + dr, c + dc) for r, c in tn) != set(t):
                    continue
                placed = {}
                for k in keys:
                    a, b = _tf(k, tr)
                    placed[(a + dr, b + dc)] = odict[k]
                # orientation score: total distance from each marker to the
                # nearest frame band of the same color (lower = better)
                score = 0
                for (mr, mc), v in placed.items():
                    if v in (8, 9):
                        continue
                    d = [abs(mc - cc) for cc, col in vb.items() if col == v]
                    d += [abs(mr - rr) for rr, col in hb.items() if col == v]
                    if d:
                        score += min(d)
                if best is None or score < best[0]:
                    best = (score, ti, placed)
        if best is None:
            continue
        _, ti, placed = best
        used.add(ti)
        # erase original object cells -> background
        for (r, c) in o:
            T[(r, c)] = bg
        # draw oriented object at the destination
        for (r, c), v in placed.items():
            if 0 <= r < H and 0 <= c < W:
                T[(r, c)] = v
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
