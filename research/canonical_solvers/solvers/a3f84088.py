"""Canonical latent-T solver for ARC puzzle a3f84088.

Rule
----
The input contains a single hollow rectangular box drawn in color 5 (a 5-pixel
border around an empty interior of color 0).  The transformation fills the
interior with concentric, self-similar square rings that spiral inward.

Numbering each cell by its "shell" depth (Chebyshev distance to the box border),
the color of a shell follows the period-4 cycle::

    layer % 4 == 0 -> 5   (a box border)
    layer % 4 == 1 -> 2   (a "2" ring just inside a border)
    layer % 4 == 2 -> 5   (the inner border of that box)
    layer % 4 == 3 -> 0   (the gap before the next nested box)

i.e. the rings read 5,2,5,0,5,2,5,0,... from the outer border inward, producing
nested boxes [outer-5-border, 2-ring, inner-5-border, 0-gap] repeated.

Terminal-center exception: when the box has an odd side, the single center cell
lands on a "5" position (layer%4==0) and would be the border-dot of a would-be
innermost box.  That dot is only actually drawn (5) when the recursion is deep
enough to have completed at least two full 5,2,5,0 cycles (maxlayer >= 8);
otherwise the leftover center stays part of the gap (0).

`infer_T` builds the explicit recolor mask from the box geometry alone;
`apply_T` copies the input and overwrites only the masked cells.
"""

# period-4 ring palette, indexed by (shell depth % 4)
_PAL = {0: 5, 1: 2, 2: 5, 3: 0}


def infer_T(input_grid):
    """Return a latent transformation mask {(r, c): new_color} for the box fill."""
    H = len(input_grid)
    W = len(input_grid[0]) if H else 0

    # locate the single color-5 box via its bounding rectangle
    cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 5]
    if not cells:
        return {}
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    top, bot = min(rs), max(rs)
    left, right = min(cs), max(cs)

    # deepest shell index reachable from the border
    maxlayer = min(bot - top, right - left) // 2
    # the box has a single center cell only when both spans are even
    odd_center = ((bot - top) % 2 == 0) and ((right - left) % 2 == 0)

    T = {}
    for r in range(top, bot + 1):
        for c in range(left, right + 1):
            layer = min(r - top, bot - r, c - left, right - c)
            color = _PAL[layer % 4]
            # lone-center exception: a would-be innermost box-border dot is only
            # drawn when at least two full 5,2,5,0 cycles precede it.
            if odd_center and layer == maxlayer and layer % 4 == 0 and maxlayer < 8:
                color = 0
            T[(r, c)] = color
    return T


def apply_T(input_grid, T):
    """Copy the input and overwrite only the masked cells."""
    out = [row[:] for row in input_grid]
    for (r, c), color in T.items():
        out[r][c] = color
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
