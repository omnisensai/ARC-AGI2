from collections import defaultdict


def infer_T(input_grid):
    """Latent mask: for every concentric-ring object, reverse the order of its
    color bands (outermost color <-> innermost color, swapping inward).

    Each non-background object is a stack of concentric color bands. Ordering
    the bands by their minimum Chebyshev distance to the object's bounding-box
    edge gives the outer->inner sequence (robust to bands of any thickness).
    Reversing that color sequence yields the per-cell recolor mask T.
    """
    H, W = len(input_grid), len(input_grid[0])
    counts = defaultdict(int)
    for row in input_grid:
        for v in row:
            counts[v] += 1
    bg = max(counts, key=counts.get)

    seen = [[False] * W for _ in range(H)]
    T = {}
    for sr in range(H):
        for sc in range(W):
            if input_grid[sr][sc] == bg or seen[sr][sc]:
                continue
            # Flood-fill one object over all non-background cells (4-conn).
            comp = []
            stack = [(sr, sc)]
            seen[sr][sc] = True
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < H and 0 <= nc < W and not seen[nr][nc]
                            and input_grid[nr][nc] != bg):
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            r0 = min(r for r, _ in comp)
            r1 = max(r for r, _ in comp)
            c0 = min(c for _, c in comp)
            c1 = max(c for _, c in comp)

            # Depth of each cell = min distance to the bounding-box border.
            # For each color band, take its smallest depth (closest to edge).
            min_depth = {}
            for r, c in comp:
                depth = min(r - r0, r1 - r, c - c0, c1 - c)
                col = input_grid[r][c]
                if col not in min_depth or depth < min_depth[col]:
                    min_depth[col] = depth

            order = sorted(min_depth, key=lambda col: min_depth[col])  # outer->inner
            rev = order[::-1]
            remap = {order[i]: rev[i] for i in range(len(order))}

            for r, c in comp:
                T[(r, c)] = remap[input_grid[r][c]]
    return T


def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out


def solve(input_grid):
    T = infer_T(input_grid)
    return apply_T(input_grid, T)
