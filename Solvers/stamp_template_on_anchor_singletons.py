"""
Puzzle: 3e980e27
Rule name: stamp_template_on_anchor_singletons

Transformation rule:
For each lone pixel whose color matches an anchor color inside a multi-cell
template shape, replicate the rest of that template around the pixel,
mirroring horizontally when the anchor color is 2.

Source: GPT-generated code (after Claude R1 produced a wrong_test overfit on
the same puzzle — see research/agent_corpus/batch_001_judged.json). GPT
identified the rule is color-based (anchor color 3 = identity copy, anchor
color 2 = horizontal mirror) rather than geometric, which is what generalized
to the test pair.

Validation: all 5/5 pairs (training + test) of the source puzzle pass.
Judge consensus: 3/5 LLM judges produced this exact rule name.
"""
def solve(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]

    dirs = [(-1,-1),(-1,0),(-1,1),
            (0,-1),        (0,1),
            (1,-1),(1,0),(1,1)]

    seen = [[False] * W for _ in range(H)]
    comps = []

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 0 or seen[r][c]:
                continue

            stack = [(r, c)]
            seen[r][c] = True
            cells = []

            while stack:
                x, y = stack.pop()
                cells.append((x, y, input_grid[x][y]))

                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < H and 0 <= ny < W:
                        if not seen[nx][ny] and input_grid[nx][ny] != 0:
                            seen[nx][ny] = True
                            stack.append((nx, ny))

            comps.append(cells)

    singles = {}
    templates = {}

    for comp in comps:
        if len(comp) == 1:
            r, c, col = comp[0]
            singles.setdefault(col, []).append((r, c))
        else:
            colors = set(v for _, _, v in comp)
            for col in colors:
                templates[col] = comp

    for anchor_col, targets in singles.items():
        if anchor_col not in templates:
            continue

        comp = templates[anchor_col]

        anchors = [(r, c) for r, c, v in comp if v == anchor_col]
        if not anchors:
            continue

        ar, ac = anchors[0]

        pattern = []
        for r, c, v in comp:
            if v == anchor_col:
                continue

            dr, dc = r - ar, c - ac

            if anchor_col == 2:
                dc = -dc

            pattern.append((dr, dc, v))

        for tr, tc in targets:
            for dr, dc, v in pattern:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < H and 0 <= nc < W:
                    out[nr][nc] = v

    return out
