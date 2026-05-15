"""TRUE_SOLVE: 13e47133 via GPT, fresh-refinement path.

Outcome: training 3/3, test 1800/1800 (both test pairs exact match).

Path:
  iter 1 (continuation seed)        : 2/3 training (pair 1 FAIL 26/400)
  iter 2 (fresh refinement, B-pick) : 3/3 training, 1800/1800 test → TRUE_SOLVE

Iter 1's rule: "min(distance to bounding-box edges)" — treated each room as a
rectangle. Fresh refinement (new chat, prior code + prior rule + judge-then-
repair, no test-derived hints) judged B and replaced the depth metric with
Chebyshev BFS from the actual room boundary, where boundary = grid edge or
any 8-neighbor outside the 4-connected non-wall room.

The fresh-refinement prompt added the following information not present in
iter 1: per-pair PASS/FAIL counts on the training pairs (derivable from the
puzzle + prior code, comp-clean), plus process scaffolding (judge step,
no-special-cases constraint). Nothing derived from test ground truth was
shown to the model.

STATED_RULE: For each 4-connected non-wall room, fill cells by a repeating
color cycle inferred from seed colors at their Chebyshev BFS depth from the
room boundary (boundary = grid edge or any cell with an 8-neighbor outside
the room).
"""


def solve(input_grid):
    from collections import Counter, deque

    grid = input_grid
    h, w = len(grid), len(grid[0])

    counts = Counter(x for row in grid for x in row)
    background = counts.most_common(1)[0][0]
    wall = max((c for c in counts if c != background), key=lambda c: counts[c])

    output_grid = [row[:] for row in grid]
    seen = [[False] * w for _ in range(h)]

    dirs4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    dirs8 = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if dr != 0 or dc != 0
    ]

    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] == wall:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            cells = []
            cellset = set()

            while q:
                r, c = q.popleft()
                cells.append((r, c))
                cellset.add((r, c))

                for dr, dc in dirs4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != wall
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))

            depth = {}
            q = deque()

            for r, c in cells:
                is_boundary = r == 0 or r == h - 1 or c == 0 or c == w - 1
                if not is_boundary:
                    for dr, dc in dirs8:
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) not in cellset:
                            is_boundary = True
                            break

                if is_boundary:
                    depth[(r, c)] = 0
                    q.append((r, c))

            while q:
                r, c = q.popleft()
                for dr, dc in dirs8:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in cellset and (nr, nc) not in depth:
                        depth[(nr, nc)] = depth[(r, c)] + 1
                        q.append((nr, nc))

            colors_by_depth = {}
            for r, c in cells:
                if grid[r][c] != background:
                    colors_by_depth.setdefault(depth[(r, c)], grid[r][c])

            if not colors_by_depth:
                continue

            cycle = [background] * (max(colors_by_depth) + 1)
            for d, color in colors_by_depth.items():
                cycle[d] = color

            period = len(cycle)
            for r, c in cells:
                output_grid[r][c] = cycle[depth[(r, c)] % period]

    return output_grid
