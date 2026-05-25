def infer_T(input_grid):
    """Infer the latent transformation mask for puzzle 6bcdb01e.

    Structure: a 2-cell domino of color 3 (the marker) sits against a grid edge.
    It emits a beam of 3s travelling in a straight line. 8s act as mirrors:
    when the cell directly ahead of the beam is an 8, the beam turns 90 degrees
    toward whichever perpendicular side is open. The grid boundary terminates
    the beam (no reflection off the edge). The mask is the set of cells the beam
    paints (excluding the marker itself, which is already 3).
    """
    H, W = len(input_grid), len(input_grid[0])

    def oob(r, c):
        return not (0 <= r < H and 0 <= c < W)

    def is8(r, c):
        return (not oob(r, c)) and input_grid[r][c] == 8

    def blocked(r, c):
        return oob(r, c) or is8(r, c)

    marker = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 3]
    T = {}
    if len(marker) != 2:
        return T

    a, b = sorted(marker)
    # Determine the beam's start direction along the domino axis: it points
    # from the marker end nearer a grid edge toward the end farther from it.
    if a[0] == b[0]:  # horizontal domino -> beam moves horizontally
        da = min(a[1], W - 1 - a[1])
        db = min(b[1], W - 1 - b[1])
        if da < db:
            head = b
            d = (0, 1 if b[1] > a[1] else -1)
        else:
            head = a
            d = (0, 1 if a[1] > b[1] else -1)
    else:  # vertical domino -> beam moves vertically
        da = min(a[0], H - 1 - a[0])
        db = min(b[0], H - 1 - b[0])
        if da < db:
            head = b
            d = (1 if b[0] > a[0] else -1, 0)
        else:
            head = a
            d = (1 if a[0] > b[0] else -1, 0)

    r, c = head
    visited = set(marker)
    for _ in range(H * W * 4 + 10):
        nr, nc = r + d[0], c + d[1]
        if oob(nr, nc):
            break  # boundary terminates the beam
        if not is8(nr, nc):
            r, c = nr, nc
            visited.add((r, c))
        else:
            # Wall ahead: turn toward the open perpendicular side.
            dr, dc = d
            left = (-dc, dr)
            right = (dc, -dr)
            lblock = blocked(r + left[0], c + left[1])
            rblock = blocked(r + right[0], c + right[1])
            if not lblock and rblock:
                d = left
            elif not rblock and lblock:
                d = right
            else:
                # both blocked (dead end) or ambiguous -> stop
                break

    for (rr, cc) in visited:
        if input_grid[rr][cc] != 3:
            T[(rr, cc)] = 3
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
