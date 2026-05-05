def solve(input_grid):
    from collections import Counter

    grid = [row[:] for row in input_grid]
    H, W = len(grid), len(grid[0])
    bg = grid[0][0]

    def full_bg_row(r):
        return all(grid[r][c] == bg for c in range(W))

    def full_bg_col(c):
        return all(grid[r][c] == bg for r in range(H))

    bg_rows = [r for r in range(H) if full_bg_row(r)]
    bg_cols = [c for c in range(W) if full_bg_col(c)]

    row_bounds = [-1] + bg_rows + [H]
    col_bounds = [-1] + bg_cols + [W]

    def best_period_patch(block):
        h, w = len(block), len(block[0])
        vals = [v for row in block for v in row if v != bg]
        if not vals:
            return block

        fg = Counter(vals).most_common(1)[0][0]
        binary = [[1 if block[r][c] == fg else 0 for c in range(w)] for r in range(h)]

        best = None

        for pr in range(1, h + 1):
            for pc in range(1, w + 1):
                if pr == h and pc == w:
                    continue

                # In very shallow blocks, a full-width period just memorizes
                # the corrupted row(s) instead of repairing the repeating motif.
                if h <= 2 and pc == w:
                    continue

                errors = 0
                tile = [[0] * pc for _ in range(pr)]

                for rr in range(pr):
                    for cc in range(pc):
                        ones = 0
                        total = 0

                        for r in range(rr, h, pr):
                            for c in range(cc, w, pc):
                                ones += binary[r][c]
                                total += 1

                        zeros = total - ones

                        if ones >= zeros:
                            tile[rr][cc] = 1
                            errors += zeros
                        else:
                            tile[rr][cc] = 0
                            errors += ones

                cost = errors + 0.2 * pr * pc

                if best is None or cost < best[0]:
                    best = (cost, errors, pr, pc, tile)

        if best is None:
            return block

        _, _, pr, pc, tile = best

        out = []
        for r in range(h):
            new_row = []
            for c in range(w):
                new_row.append(fg if tile[r % pr][c % pc] else bg)
            out.append(new_row)

        return out

    for i in range(len(row_bounds) - 1):
        r0 = row_bounds[i] + 1
        r1 = row_bounds[i + 1] - 1
        if r1 - r0 + 1 < 3:
            continue

        for j in range(len(col_bounds) - 1):
            c0 = col_bounds[j] + 1
            c1 = col_bounds[j + 1] - 1
            if c1 - c0 + 1 < 3:
                continue

            ir0, ir1 = r0 + 1, r1 - 1
            ic0, ic1 = c0 + 1, c1 - 1

            if ir0 > ir1 or ic0 > ic1:
                continue

            block = [grid[r][ic0:ic1 + 1] for r in range(ir0, ir1 + 1)]
            patched = best_period_patch(block)

            for rr, r in enumerate(range(ir0, ir1 + 1)):
                for cc, c in enumerate(range(ic0, ic1 + 1)):
                    grid[r][c] = patched[rr][cc]

    return grid
