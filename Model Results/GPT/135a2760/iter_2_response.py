def solve(input_grid):
    from collections import Counter

    grid = [row[:] for row in input_grid]
    H, W = len(grid), len(grid[0])
    bg = grid[0][0]

    def is_full_bg_row(r):
        return all(grid[r][c] == bg for c in range(W))

    def is_full_bg_col(c):
        return all(grid[r][c] == bg for r in range(H))

    sep_rows = [r for r in range(H) if is_full_bg_row(r)]
    sep_cols = [c for c in range(W) if is_full_bg_col(c)]

    row_bounds = [-1] + sep_rows + [H]
    col_bounds = [-1] + sep_cols + [W]

    def repeated_patch(block):
        h, w = len(block), len(block[0])
        vals = [v for row in block for v in row if v != bg]
        if not vals:
            return block

        fg = Counter(vals).most_common(1)[0][0]
        bits = [[1 if block[r][c] == fg else 0 for c in range(w)] for r in range(h)]

        best = None

        for pr in range(1, h + 1):
            for pc in range(1, w + 1):
                if pr == h and pc == w:
                    continue

                if pc == w and pr == 1:
                    continue
                if pr == h and pc == 1:
                    continue

                if not (pr < h or pc < w):
                    continue

                tile = [[0] * pc for _ in range(pr)]
                errors = 0

                for rr in range(pr):
                    for cc in range(pc):
                        members = []
                        for r in range(rr, h, pr):
                            for c in range(cc, w, pc):
                                members.append(bits[r][c])

                        ones = sum(members)
                        zeros = len(members) - ones

                        if ones >= zeros:
                            tile[rr][cc] = 1
                            errors += zeros
                        else:
                            tile[rr][cc] = 0
                            errors += ones

                score = (errors, pr * pc, pr + pc)

                if best is None or score < best[0]:
                    best = (score, pr, pc, tile)

        if best is None:
            return block

        _, pr, pc, tile = best

        out = []
        for r in range(h):
            row = []
            for c in range(w):
                row.append(fg if tile[r % pr][c % pc] else bg)
            out.append(row)

        return out

    for bi in range(len(row_bounds) - 1):
        r0 = row_bounds[bi] + 1
        r1 = row_bounds[bi + 1] - 1
        if r1 - r0 + 1 < 3:
            continue

        for bj in range(len(col_bounds) - 1):
            c0 = col_bounds[bj] + 1
            c1 = col_bounds[bj + 1] - 1
            if c1 - c0 + 1 < 3:
                continue

            ir0, ir1 = r0 + 1, r1 - 1
            ic0, ic1 = c0 + 1, c1 - 1

            if ir0 > ir1 or ic0 > ic1:
                continue

            block = [grid[r][ic0:ic1 + 1] for r in range(ir0, ir1 + 1)]
            fixed = repeated_patch(block)

            for rr, r in enumerate(range(ir0, ir1 + 1)):
                for cc, c in enumerate(range(ic0, ic1 + 1)):
                    grid[r][c] = fixed[rr][cc]

    return grid
