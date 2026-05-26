"""Canonical solver for ARC task d255d7a7.

Rule
----
The grid contains "lollipop" objects: a 3x3 box (head, possibly containing
marker cells of color 9) attached to a straight stem (a 1-wide line of 0s)
that runs from the middle of one box edge out to a grid border. Each object
slides along its stem axis so that the box becomes flush against the far
border (the end the stem points to); the stem is erased. The box's 3x3
contents (including any internal 9 markers) are carried over verbatim.
Standalone markers that are not attached to a stem stay where they are.

infer_T returns a latent mask `{(r,c): new_color}`: stem + old-box cells set
to background, destination box cells set to the carried box contents.
apply_T copies the input and overwrites only the masked cells.
"""

from collections import Counter

STEM_MIN = 4  # minimum 0-run length that counts as a stem (boxes are only 3 wide)


def _bg(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def _find_stems(g):
    """Maximal runs of color 0 (length >= STEM_MIN) in a row or column."""
    H, W = len(g), len(g[0])
    stems = []
    for r in range(H):
        c = 0
        while c < W:
            if g[r][c] == 0:
                s = c
                while c < W and g[r][c] == 0:
                    c += 1
                if c - s >= STEM_MIN:
                    stems.append(('H', r, s, c - 1))
            else:
                c += 1
    for c in range(W):
        r = 0
        while r < H:
            if g[r][c] == 0:
                s = r
                while r < H and g[r][c] == 0:
                    r += 1
                if r - s >= STEM_MIN:
                    stems.append(('V', c, s, r - 1))
            else:
                r += 1
    return stems


def infer_T(input_grid):
    g = input_grid
    H, W = len(g), len(g[0])
    bg = _bg(g)
    T = {}
    for st in _find_stems(g):
        if st[0] == 'H':
            _, r, s, e = st
            # the box is the 3x3 sitting at whichever stem end has vertical neighbours
            left_box = (r - 1 >= 0 and g[r - 1][s] != bg) or (r + 1 < H and g[r + 1][s] != bg)
            right_box = (r - 1 >= 0 and g[r - 1][e] != bg) or (r + 1 < H and g[r + 1][e] != bg)
            if left_box and not right_box:
                bc0, direction = s - 2, 'R'      # box on the left, stem points right
            elif right_box and not left_box:
                bc0, direction = e, 'L'          # box on the right, stem points left
            else:
                continue
            box = [[g[r - 1 + i][bc0 + j] for j in range(3)] for i in range(3)]
            # erase stem + original box footprint
            c_lo, c_hi = min(s, bc0), max(e, bc0 + 2)
            for rr in range(r - 1, r + 2):
                for cc in range(c_lo, c_hi + 1):
                    if 0 <= rr < H and 0 <= cc < W:
                        T[(rr, cc)] = bg
            # place box flush against the destination border
            ndc0 = (W - 3) if direction == 'R' else 0
            for i in range(3):
                for j in range(3):
                    T[(r - 1 + i, ndc0 + j)] = box[i][j]
        else:
            _, c, s, e = st
            top_box = (c - 1 >= 0 and g[s][c - 1] != bg) or (c + 1 < W and g[s][c + 1] != bg)
            bot_box = (c - 1 >= 0 and g[e][c - 1] != bg) or (c + 1 < W and g[e][c + 1] != bg)
            if top_box and not bot_box:
                br0, direction = s - 2, 'D'      # box on top, stem points down
            elif bot_box and not top_box:
                br0, direction = e, 'U'          # box on bottom, stem points up
            else:
                continue
            box = [[g[br0 + i][c - 1 + j] for j in range(3)] for i in range(3)]
            r_lo, r_hi = min(s, br0), max(e, br0 + 2)
            for rr in range(r_lo, r_hi + 1):
                for cc in range(c - 1, c + 2):
                    if 0 <= rr < H and 0 <= cc < W:
                        T[(rr, cc)] = bg
            ndr0 = (H - 3) if direction == 'D' else 0
            for i in range(3):
                for j in range(3):
                    T[(ndr0 + i, c - 1 + j)] = box[i][j]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
