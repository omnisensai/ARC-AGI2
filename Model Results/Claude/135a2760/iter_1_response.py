def solve(input_grid):
    from collections import Counter

    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])
    bg = grid[0][0]

    bg_rows = {r for r in range(H) if all(grid[r][c] == bg for c in range(W))}
    bg_cols = {c for c in range(W) if all(grid[r][c] == bg for r in range(H))}

    row_ranges = []
    start = None
    for r in range(H):
        if r not in bg_rows:
            if start is None:
                start = r
        else:
            if start is not None:
                row_ranges.append((start, r - 1))
                start = None
    if start is not None:
        row_ranges.append((start, H - 1))

    col_ranges = []
    start = None
    for c in range(W):
        if c not in bg_cols:
            if start is None:
                start = c
        else:
            if start is not None:
                col_ranges.append((start, c - 1))
                start = None
    if start is not None:
        col_ranges.append((start, W - 1))

    for (r1, r2) in row_ranges:
        for (c1, c2) in col_ranges:
            ir1, ir2 = r1 + 1, r2 - 1
            ic1, ic2 = c1 + 1, c2 - 1
            if ir1 > ir2 or ic1 > ic2:
                continue

            ih = ir2 - ir1 + 1
            iw = ic2 - ic1 + 1

            interior = []
            for r in range(ir1, ir2 + 1):
                interior.append([grid[r][c] for c in range(ic1, ic2 + 1)])

            best_period = None
            best_mismatches = float('inf')

            for pr in range(1, ih + 1):
                for pc in range(1, iw + 1):
                    if ih // pr < 2 and iw // pc < 2:
                        continue

                    tile = [[Counter() for _ in range(pc)] for _ in range(pr)]
                    for r in range(ih):
                        for c in range(iw):
                            tile[r % pr][c % pc][interior[r][c]] += 1

                    mismatches = 0
                    for r in range(ih):
                        for c in range(iw):
                            majority = tile[r % pr][c % pc].most_common(1)[0][0]
                            if interior[r][c] != majority:
                                mismatches += 1

                    if (mismatches < best_mismatches or
                        (mismatches == best_mismatches and pr * pc < best_period[0] * best_period[1])):
                        best_mismatches = mismatches
                        best_period = (pr, pc)

            pr, pc = best_period
            tile = [[Counter() for _ in range(pc)] for _ in range(pr)]
            for r in range(ih):
                for c in range(iw):
                    tile[r % pr][c % pc][interior[r][c]] += 1

            for r in range(ih):
                for c in range(iw):
                    majority = tile[r % pr][c % pc].most_common(1)[0][0]
                    grid[ir1 + r][ic1 + c] = majority

    return grid
