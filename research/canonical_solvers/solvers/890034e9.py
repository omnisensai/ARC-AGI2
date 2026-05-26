def find_box(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    colors = set(v for row in input_grid for v in row if v != 0)
    for color in colors:
        cells = set((r, c) for r in range(H) for c in range(W)
                    if input_grid[r][c] == color)
        seen = set()
        for cell in cells:
            if cell in seen:
                continue
            comp = []
            stack = [cell]
            while stack:
                x = stack.pop()
                if x in seen or x not in cells:
                    continue
                seen.add(x)
                comp.append(x)
                r, c = x
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    stack.append((r + dr, c + dc))
            rs = [a for a, b in comp]
            cs = [b for a, b in comp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if h < 3 or w < 3:
                continue
            perim = 2 * h + 2 * w - 4
            if len(comp) != perim:
                continue
            # interior must be hollow (no marker cells inside)
            interior_ok = all((rr, cc) not in cells
                              for rr in range(r0 + 1, r1)
                              for cc in range(c0 + 1, c1))
            if interior_ok:
                return color, r0, r1, c0, c1
    return None


def infer_T(input_grid):
    """Find the hollow box, then locate the matching empty (all-0) interior
    region elsewhere and build a mask that stamps the box frame around it."""
    H, W = len(input_grid), len(input_grid[0])
    T = {}
    box = find_box(input_grid)
    if box is None:
        return T
    color, br0, br1, bc0, bc1 = box
    h, w = br1 - br0 + 1, bc1 - bc0 + 1
    ih, iw = h - 2, w - 2

    # Find the (unique) all-0 interior-sized rectangle that is NOT the box's
    # own interior.
    target = None
    for r in range(H - ih + 1):
        for c in range(W - iw + 1):
            # skip the box's own interior
            if br0 + 1 <= r and r + ih - 1 <= br1 - 1 and \
               bc0 + 1 <= c and c + iw - 1 <= bc1 - 1:
                continue
            # need room for a frame ring one cell out on every side
            if r - 1 < 0 or c - 1 < 0 or r + ih >= H or c + iw >= W:
                continue
            if all(input_grid[r + i][c + j] == 0
                   for i in range(ih) for j in range(iw)):
                if target is None:
                    target = (r, c)
                else:
                    target = "ambiguous"

    if target is None or target == "ambiguous":
        return T

    ir0, ic0 = target
    # frame ring is one cell out from the interior
    fr0, fc0 = ir0 - 1, ic0 - 1
    fr1, fc1 = ir0 + ih, ic0 + iw
    for c in range(fc0, fc1 + 1):
        T[(fr0, c)] = color
        T[(fr1, c)] = color
    for r in range(fr0, fr1 + 1):
        T[(r, fc0)] = color
        T[(r, fc1)] = color
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
