from collections import Counter


def infer_T(input_grid):
    """Compute the latent mask of cells to overwrite with color 1.

    Structure of the puzzle:
      * One background color (the most common value).
      * Scattered single-cell "noise" markers of one non-background color.
      * One or more activation markers of color 1, all in column 0.
    Rule:
      * From each color-1 marker, a horizontal "beam" of 1s is drawn rightward
        along the marker row (over background cells).
      * Every noise cell the beam reaches becomes "active" and gets a 3x3 box
        of 1s painted around it (noise centers keep their own color).
      * Activation cascades: an active noise cell's forward diagonal corners
        (up-right / down-right), if they are noise, become active too.
      * A box side (the row above / below the cell) is suppressed if the cell
        immediately diagonally-back on that side is an *inactive* noise cell
        (a non-participating obstacle).  The single forward cell is suppressed
        when both backward diagonal corners are noise (a squeeze).
      * A "gate": if a beam-row noise cell has BOTH forward diagonal corners
        noise, the beam stops there and those two walls emit a reflected
        diamond of boxes that grows forward (up to Chebyshev distance 2),
        with directional emission relative to the gate.
    The mask is the set of background cells that get repainted to 1.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]

    def isn(r, c):
        return 0 <= r < H and 0 <= c < W and input_grid[r][c] not in (bg, 1)

    noise = [(r, c) for r in range(H) for c in range(W) if isn(r, c)]

    active = set()
    stack = []
    beam_cells = set()
    gatemode = set()      # cells handled by the gate (reflection) emission rule
    gates = set()         # the gate centers (on the marker row)
    ring1 = set()         # the two immediate gate walls
    gate_of = {}          # gate-cluster cell -> (gate_row, gate_col)

    markers = [r for r in range(H) for c in range(W)
               if input_grid[r][c] == 1 and c == 0]

    # Phase 1: trace each beam and seed activations.
    for mr in markers:
        c = 0
        while c < W:
            if isn(mr, c):
                if (mr, c) not in active:
                    active.add((mr, c)); stack.append((mr, c))
                # gate detection: both forward diagonal corners are noise
                if isn(mr - 1, c + 1) and isn(mr + 1, c + 1):
                    gates.add((mr, c)); gatemode.add((mr, c))
                    gate_of[(mr, c)] = (mr, c)
                    for w in ((mr - 1, c + 1), (mr + 1, c + 1)):
                        ring1.add(w); gatemode.add(w); gate_of[w] = (mr, c)
                        if w not in active:
                            active.add(w); stack.append(w)
                    break  # beam stops at the gate
            else:
                beam_cells.add((mr, c))
            c += 1

    # Phase 1b: cascade activations.
    while stack:
        r, c = stack.pop()
        if (r, c) in gatemode:
            # gate-cluster cells (except the gate center) grow the diamond
            # forward to any noise within Chebyshev distance 2.
            if (r, c) not in gates:
                gr, gc = gate_of[(r, c)]
                for (nr, nc) in noise:
                    if ((nr, nc) not in active and nc > c
                            and abs(nr - r) <= 2 and abs(nc - c) <= 2):
                        active.add((nr, nc)); stack.append((nr, nc))
                        gatemode.add((nr, nc)); gate_of[(nr, nc)] = (gr, gc)
        else:
            for (nr, nc) in ((r - 1, c + 1), (r + 1, c + 1)):
                if isn(nr, nc) and (nr, nc) not in active:
                    active.add((nr, nc)); stack.append((nr, nc))

    # Phase 2: emit the boxes into the mask.
    mask = set(beam_cells)

    def add(r, c):
        if 0 <= r < H and 0 <= c < W and not isn(r, c):
            mask.add((r, c))

    ALL = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
           if not (dr == 0 and dc == 0)]

    for (r, c) in active:
        if (r, c) in gatemode:
            gr, gc = gate_of[(r, c)]
            for (dr, dc) in ALL:
                if (r, c) in gates:
                    # gate center: emit up/down/back, never forward
                    if dc <= 0:
                        add(r + dr, c + dc)
                elif (r, c) in ring1:
                    # walls: forward + away-from-gate; never toward the gate row
                    if r < gr and dr == 1:
                        continue
                    if r > gr and dr == -1:
                        continue
                    add(r + dr, c + dc)
                else:
                    # reflected diamond cells: toward gate + back, never forward
                    if dc > 0:
                        continue
                    if r < gr and dr == -1:
                        continue
                    if r > gr and dr == 1:
                        continue
                    if r == gr and dr == 0:
                        continue
                    add(r + dr, c + dc)
            continue
        # standard 3x3 box with directional suppression
        add(r, c - 1)
        if not (isn(r - 1, c - 1) and isn(r + 1, c - 1)):
            add(r, c + 1)
        if not (isn(r - 1, c - 1) and (r - 1, c - 1) not in active):
            add(r - 1, c - 1); add(r - 1, c); add(r - 1, c + 1)
        if not (isn(r + 1, c - 1) and (r + 1, c - 1) not in active):
            add(r + 1, c - 1); add(r + 1, c); add(r + 1, c + 1)

    return mask


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c) in T:
        out[r][c] = 1
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
