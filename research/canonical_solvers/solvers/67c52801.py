from collections import Counter, deque


def _floor_color(g):
    H = len(g)
    cnt = Counter(v for v in g[H - 1] if v != 0)
    return cnt.most_common(1)[0][0]


def infer_T(input_grid):
    """Infer the latent fill mask.

    Structure of every pair: the bottom row is a solid 'floor' line; the row
    just above it (H-2) is the same floor color but has gaps (0s). Each
    contiguous run of gaps is a 'slot' of a given width. Floating shapes above
    the floor are matched to slots: slots sorted by width ascending pair with
    shapes sorted by cell count ascending. Each shape is repacked as a
    width x height block (height = cells // slot_width) sitting on the floor,
    occupying the slot columns from row H-2 upward.
    """
    g = input_grid
    H, W = len(g), len(g[0])
    fc = _floor_color(g)

    # slots: contiguous runs of 0 in row H-2
    slots = []
    for c in range(W):
        if g[H - 2][c] == 0:
            if slots and c == slots[-1][-1] + 1:
                slots[-1].append(c)
            else:
                slots.append([c])

    # shapes: connected components of color != 0 and != floor color
    seen = set()
    shapes = []
    for r in range(H):
        for c in range(W):
            v = g[r][c]
            if v == 0 or v == fc or (r, c) in seen:
                continue
            q = deque([(r, c)])
            comp = []
            seen.add((r, c))
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < H and 0 <= nc < W and (nr, nc) not in seen
                            and g[nr][nc] == v):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            shapes.append((v, len(comp)))

    slots_sorted = sorted(slots, key=lambda s: len(s))
    shapes_sorted = sorted(shapes, key=lambda s: s[1])

    T = {}
    for slot, (color, cells) in zip(slots_sorted, shapes_sorted):
        w = len(slot)
        height = cells // w
        for h in range(height):
            row = H - 2 - h
            if 0 <= row < H:
                for c in slot:
                    T[(row, c)] = color
    return T


def apply_T(input_grid, T):
    """Copy input, remove the original floating shapes, then paint the mask."""
    H, W = len(input_grid), len(input_grid[0])
    fc = _floor_color(input_grid)
    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if out[r][c] != 0 and out[r][c] != fc:
                out[r][c] = 0
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
