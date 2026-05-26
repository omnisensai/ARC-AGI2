from collections import Counter


def _components(grid, color):
    H, W = len(grid), len(grid[0])
    seen = [[False] * W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] == color and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    y, x = stack.pop()
                    cells.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and grid[ny][nx] == color and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps


def _is_hollow_rect(grid, cells, color):
    rs = [y for y, x in cells]
    cs = [x for y, x in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    cellset = set(cells)
    # border must be fully the color; interior must be empty of the color
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            border = (y == r0 or y == r1 or x == c0 or x == c1)
            if border:
                if (y, x) not in cellset:
                    return None
            else:
                if (y, x) in cellset:
                    return None
    return (r0, r1, c0, c1)


def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]

    # find hollow-rectangle box frames per color
    boxes = []  # (r0,r1,c0,c1, frame_color)
    frame_colors = set()
    for color in counts:
        if color == bg:
            continue
        for comp in _components(input_grid, color):
            rect = _is_hollow_rect(input_grid, comp, color)
            if rect is not None:
                r0, r1, c0, c1 = rect
                boxes.append((r0, r1, c0, c1, color))
                frame_colors.add(color)

    # noise colors = non-bg colors that are not frame colors
    noise_counts = {col: cnt for col, cnt in counts.items()
                    if col != bg and col not in frame_colors}

    T = {}  # (r,c) -> new color  (latent mask)

    # First: every non-bg cell defaults to bg (clear noise + everything)
    # then re-assert frames and fill interiors.
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != bg:
                T[(r, c)] = bg

    # re-assert box frames (keep them)
    box_interiors = []
    for (r0, r1, c0, c1, color) in boxes:
        for y in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                if y == r0 or y == r1 or x == c0 or x == c1:
                    T[(y, x)] = color
        ir0, ir1, ic0, ic1 = r0 + 1, r1 - 1, c0 + 1, c1 - 1
        even = 0
        for y in range(ir0, ir1 + 1):
            for x in range(ic0, ic1 + 1):
                if ((y - ir0) + (x - ic0)) % 2 == 0:
                    even += 1
        box_interiors.append((ir0, ir1, ic0, ic1, even))

    # match each box interior to the noise color whose count == even-cell count
    used = set()
    for (ir0, ir1, ic0, ic1, even) in box_interiors:
        fill = None
        for col, cnt in noise_counts.items():
            if col in used:
                continue
            if cnt == even:
                fill = col
                break
        if fill is None:
            # fallback: closest count among unused
            best = None
            for col, cnt in noise_counts.items():
                if col in used:
                    continue
                if best is None or abs(cnt - even) < abs(noise_counts[best] - even):
                    best = col
            fill = best
        if fill is not None:
            used.add(fill)
        for y in range(ir0, ir1 + 1):
            for x in range(ic0, ic1 + 1):
                if ((y - ir0) + (x - ic0)) % 2 == 0 and fill is not None:
                    T[(y, x)] = fill
                # odd cells remain bg (already set)

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
