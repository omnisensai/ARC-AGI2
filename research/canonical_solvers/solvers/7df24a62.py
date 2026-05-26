"""Canonical solver for ARC puzzle 7df24a62.

Rule
----
The grid contains one "template": a solid rectangle filled with color 1 (the
border + interior) in which a few cells are color 4. The 4s inside the template
form a small spatial pattern. Elsewhere the grid is sprinkled with isolated 4s
on a background of 0.

For every group of scattered 4s that reproduces the template's 4-pattern (under
any of the 8 dihedral transforms: rotations/reflections), we stamp a copy of the
template onto the grid at that location: the rectangle that tightly bounds the
matched 4s, grown by one cell on every side, is filled with color 1, leaving the
matched 4s themselves intact. The original template is left unchanged (it stamps
itself).

Latent T
--------
infer_T scans the input alone: it locates the template (bbox of the 1s), reads
its embedded 4-pattern, enumerates the dihedral transforms, finds every matching
group of scattered 4s (with no extra 4 inside the bounding box), and records the
cells each stamp would set to 1. apply_T copies the input and writes 1 into
exactly those cells.
"""


def _transforms(offsets):
    """All 8 dihedral images of a set of (r,c) offsets, normalized to origin."""
    def norm(pts):
        mr = min(r for r, c in pts)
        mc = min(c for r, c in pts)
        return frozenset((r - mr, c - mc) for r, c in pts)

    out = set()
    cur = [(r, c) for r, c in offsets]
    for _ in range(4):
        cur = [(c, -r) for r, c in cur]            # rotate 90 degrees
        out.add(norm(cur))
        out.add(norm([(r, -c) for r, c in cur]))   # plus its mirror
    return [sorted(t) for t in out]


def infer_T(input_grid):
    """Return a set of (r, c) cells that must be overwritten with color 1."""
    H, W = len(input_grid), len(input_grid[0])
    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]
    mask = set()
    if not ones:
        return mask

    # Template = bounding box of all 1s; its interior holds the 4-pattern.
    tr0 = min(r for r, c in ones)
    tr1 = max(r for r, c in ones)
    tc0 = min(c for r, c in ones)
    tc1 = max(c for r, c in ones)
    template_fours = sorted(
        (r - (tr0 + 1), c - (tc0 + 1))
        for r in range(tr0 + 1, tr1)
        for c in range(tc0 + 1, tc1)
        if input_grid[r][c] == 4
    )
    if not template_fours:
        return mask
    variants = _transforms(template_fours)

    # Scattered 4s (everything outside the template rectangle).
    fours = set(
        (r, c)
        for r in range(H)
        for c in range(W)
        if input_grid[r][c] == 4
        and not (tr0 <= r <= tr1 and tc0 <= c <= tc1)
    )

    stamps = set()
    for variant in variants:
        vh = max(r for r, c in variant)
        vw = max(c for r, c in variant)
        for br in range(H):
            for bc in range(W):
                cells = frozenset((br + r, bc + c) for r, c in variant)
                if not all(cell in fours for cell in cells):
                    continue
                # The tight bounding box of the matched 4s is the box interior.
                ir0, ir1 = br, br + vh
                ic0, ic1 = bc, bc + vw
                # Reject if any other scattered 4 sits inside that interior.
                if any(
                    (r, c) in fours and (r, c) not in cells
                    for r in range(ir0, ir1 + 1)
                    for c in range(ic0, ic1 + 1)
                ):
                    continue
                stamps.add((ir0, ir1, ic0, ic1, cells))

    for ir0, ir1, ic0, ic1, cells in stamps:
        for r in range(ir0 - 1, ir1 + 2):
            for c in range(ic0 - 1, ic1 + 2):
                if 0 <= r < H and 0 <= c < W and (r, c) not in cells:
                    mask.add((r, c))
    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for r, c in T:
        out[r][c] = 1
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
