"""Canonical latent-T solver for ARC puzzle db615bd4.

Structure of every pair:
  * A lattice grid: separator color `bg` on even rows/cols, a lattice
    color `lat` filling the data cells (odd row, odd col).
  * A rectangular FRAME drawn (in data cells) with a single `frame` color.
    Its outline may be partially drawn in the input; the output draws the
    complete outline.
  * Several small colored MARKER blobs sitting in the separator space
    outside the frame.  Each marker's bounding box (counted in separator
    cells) gives the size of a solid colored BLOCK.  Markers are erased and
    their blocks are laid out inside the frame interior, in order, along the
    longer interior axis, separated by 1px gaps and centered on the short
    axis.

infer_T builds a latent mask {(r,c): new_color} describing every cell that
changes (frame completion, marker erasure, block fills); apply_T copies the
input and overwrites only those cells.
"""

from collections import Counter, defaultdict


def _detect(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    bg = input_grid[0][0]
    # lattice color = most common data-cell color
    dcc = Counter()
    for r in range(1, H, 2):
        for c in range(1, W, 2):
            dcc[input_grid[r][c]] += 1
    lat = dcc.most_common(1)[0][0]
    # frame color = a non-lattice color present in data cells
    frame = None
    for col, _ in dcc.most_common():
        if col != lat:
            frame = col
            break
    return H, W, bg, lat, frame


def _frame_bbox(input_grid, frame):
    H, W = len(input_grid), len(input_grid[0])
    cells = [(r, c) for r in range(1, H, 2) for c in range(1, W, 2)
             if input_grid[r][c] == frame]
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _markers(input_grid, bg, lat, frame):
    """Group colored marker cells (outside the data-cell colors) by color."""
    H, W = len(input_grid), len(input_grid[0])
    blobs = defaultdict(list)
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v in (bg, lat, frame):
                continue
            blobs[v].append((r, c))
    out = {}
    for col, cells in blobs.items():
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        out[col] = (min(rs), max(rs), min(cs), max(cs))
    return out


def infer_T(input_grid):
    H, W, bg, lat, frame = _detect(input_grid)
    T = {}
    if frame is None:
        return T

    fr0, fr1, fc0, fc1 = _frame_bbox(input_grid, frame)

    # 1) Draw the complete frame as a solid 1px rectangle border (pixel space)
    #    and clear its interior to the separator/background color.
    for c in range(fc0, fc1 + 1):
        T[(fr0, c)] = frame
        T[(fr1, c)] = frame
    for r in range(fr0, fr1 + 1):
        T[(r, fc0)] = frame
        T[(r, fc1)] = frame
    for r in range(fr0 + 1, fr1):
        for c in range(fc0 + 1, fc1):
            T[(r, c)] = bg

    # 2) Markers -> blocks.  Erase markers first.
    markers = _markers(input_grid, bg, lat, frame)
    for col, (mr0, mr1, mc0, mc1) in markers.items():
        for r in range(mr0, mr1 + 1):
            for c in range(mc0, mc1 + 1):
                if input_grid[r][c] == col:
                    T[(r, c)] = lat if (r % 2 == 1 and c % 2 == 1) else bg

    # Block sizes from marker bounding boxes (counted in separator cells).
    blocks = []  # (color, height_px, width_px, sort_row, sort_col)
    for col, (mr0, mr1, mc0, mc1) in markers.items():
        sep_rows = (mr1 - mr0) // 2 + 1
        sep_cols = (mc1 - mc0) // 2 + 1
        h_px = 2 * sep_rows - 1
        w_px = 2 * sep_cols - 1
        blocks.append((col, h_px, w_px, mr0, mc0))

    # Interior pixel bbox.
    ir0, ir1 = fr0 + 2, fr1 - 2
    ic0, ic1 = fc0 + 2, fc1 - 2
    ih = ir1 - ir0 + 1
    iw = ic1 - ic0 + 1

    horizontal = iw >= ih

    if horizontal:
        blocks.sort(key=lambda b: b[4])  # by source column
        total = sum(b[2] for b in blocks) + (len(blocks) - 1)
        start = ic0 + (iw - total) // 2
        cpos = start
        for col, h_px, w_px, _, _ in blocks:
            rstart = ir0 + (ih - h_px) // 2
            for r in range(rstart, rstart + h_px):
                for c in range(cpos, cpos + w_px):
                    T[(r, c)] = col
            cpos += w_px + 1
    else:
        blocks.sort(key=lambda b: b[3])  # by source row
        total = sum(b[1] for b in blocks) + (len(blocks) - 1)
        start = ir0 + (ih - total) // 2
        rpos = start
        for col, h_px, w_px, _, _ in blocks:
            cstart = ic0 + (iw - w_px) // 2
            for r in range(rpos, rpos + h_px):
                for c in range(cstart, cstart + w_px):
                    T[(r, c)] = col
            rpos += h_px + 1

    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
