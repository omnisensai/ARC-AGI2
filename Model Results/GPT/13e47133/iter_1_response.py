def solve(input_grid):
    from collections import Counter, defaultdict

    h, w = len(input_grid), len(input_grid[0])

    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]
    sep = max((c for c in counts if c != bg), key=lambda c: counts[c])

    output_grid = [row[:] for row in input_grid]

    def local_bounds(r, c):
        r0 = r
        while r0 - 1 >= 0 and input_grid[r0 - 1][c] != sep:
            r0 -= 1

        r1 = r
        while r1 + 1 < h and input_grid[r1 + 1][c] != sep:
            r1 += 1

        c0 = c
        while c0 - 1 >= 0 and input_grid[r][c0 - 1] != sep:
            c0 -= 1

        c1 = c
        while c1 + 1 < w and input_grid[r][c1 + 1] != sep:
            c1 += 1

        return r0, r1, c0, c1

    groups = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if input_grid[r][c] != sep:
                groups[local_bounds(r, c)].append((r, c))

    for (r0, r1, c0, c1), cells in groups.items():
        seeds = []
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if input_grid[r][c] != sep and input_grid[r][c] != bg:
                    seeds.append((r, c, input_grid[r][c]))

        if not seeds:
            continue

        corner_tests = [
            lambda r, c: r - r0 if r - r0 == c - c0 else None,
            lambda r, c: r - r0 if r - r0 == c1 - c else None,
            lambda r, c: r1 - r if r1 - r == c - c0 else None,
            lambda r, c: r1 - r if r1 - r == c1 - c else None,
        ]

        best_offsets = []
        for test in corner_tests:
            offsets = []
            for r, c, color in seeds:
                d = test(r, c)
                if d is not None:
                    offsets.append((d, color))
            if len(offsets) > len(best_offsets):
                best_offsets = offsets

        if not best_offsets:
            continue

        max_offset = max(d for d, color in best_offsets)
        sequence = [bg] * (max_offset + 1)
        for d, color in best_offsets:
            sequence[d] = color

        for r, c in cells:
            d = min(r - r0, r1 - r, c - c0, c1 - c)
            output_grid[r][c] = sequence[d % len(sequence)]

    return output_grid