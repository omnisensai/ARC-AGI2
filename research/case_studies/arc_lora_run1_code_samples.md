# Code Samples from Run 1 (T=0.7, 60 attempts)

Companion to [`arc_lora_run1_locked_eval.md`](./arc_lora_run1_locked_eval.md).

Each section shows the exact Python code the LoRA produced for a given puzzle attempt, plus the puzzle's train/test shapes so you can see whether the puzzle requires a shape change.

## Near-miss puzzles (≥90% cell accuracy)

### `135a2760` [near-miss, 98.3% best]

- Train shapes (in→out): `[(5, 13, 5, 13), (21, 22, 21, 22)]`
- Test shapes (in→out): `(29, 29, 29, 29)`
- Shape-preserving: **YES (same-size)**

#### Attempt 0 (96.4%)

```python
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    visited = [[False] * W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                stack = [(r, c)]
                comp = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W:
                        continue
                    if visited[y][x] or grid[y][x] == bg:
                        continue
                    visited[y][x] = True
                    comp.append((y, x))
                    stack.extend([(y+1, x), (y-1, x), (y, x+1), (y, x-1)])
                components.append(comp)

    shapes = []
    for comp in components:
        colors = Counter(grid[y][x] for y, x in comp)
        body_color = colors.most_common(1)[0][0]
        markers = [(y, x) for y, x in comp if grid[y][x] != body_color]
        if not markers:
            continue
        my, mx = markers[0]
        marker_color = grid[my][mx]
        body = [(y, x) for y, x in comp if grid[y][x] == body_color]
        cy = sum(y for y, x in body) / len(body)
        cx = sum(x for y, x in body) / len(body)
        dy = my - cy
        dx = mx - cx
        if abs(dy) > abs(dx):
            direction = 'up' if dy < 0 else 'down'
        else:
            direction = 'left' if dx < 0 else 'right'
        shapes.append({
            'marker_pos': (my, mx),
            'marker_color': marker_color,
            'direction': direction,
        })

    edge_directions = []

    for shape in shapes:
        my, mx = shape['marker_pos']
        color = shape['marker_color']
        d = shape['direction']

        if d == 'up':
            steps = [(r, mx) for r in range(my-1, -1, -1)]
            direction_along = 'right'
            hit_edge_row = my - 1
            hit_edge_col = mx
            hit_cell = (hit_edge_row, hit_edge_col)
            other_marker = None
        elif d == 'down':
            steps = [(r, mx) for r in range(my+1, H)]
            direction_along = 'right'
            hit_edge_row = my + 1
            hit_edge_col = mx
            hit_cell = (hit_edge_row, hit_edge_col)
            other_marker = None
        elif d == 'left':
            steps = [(my, c) for c in range(mx-1, -1, -1)]
            direction_along = 'down'
            hit_edge_row = my
            hit_edge_col = mx - 1
            hit_cell = (my, hit_edge_col)
            other_marker = (my, mx + 1)
        elif d == 'right':
            steps = [(my, c) for c in range(mx+1, W)]
            direction_along = 'down'
            hit_edge_row = my
            hit_edge_col = mx + 1
            hit_cell = (my, hit_edge_col)
            other_marker = (my, mx - 1)

        hit_is_body = hit_cell in components

        edge_directions.append({
            'color': color, 'marker_pos': (my, mx), 'direction': d,
            'steps': steps, 'along_direction': direction_along,
            'hit_edge_row': hit_edge_row, 'hit_edge_col': hit_edge_col,
            'hit_is_body': hit_is_body, 'other_marker': other_marker,
            'hit_cell': hit_cell,
        })

    neutral = None
    positives = []
    for ed in edge_directions:
        color = ed['color']
        hit_is_body = ed['hit_is_body']
        if hit_is_body:
            neutral = color
        else:
            positives.append(color)

    pos_set = set(positives)
    wild = None
    for c in range(W):
        if grid[H-1][c] not in pos_set:
            wild = grid[H-1][c]
            break

    out = [row[:] for row in input_grid]

    for ed in edge_directions:
        color = ed['color']
        d = ed['direction']
        along = ed['along_direction']
        marker_pos = ed['marker_pos']
        hit_is_body = ed['hit_is_body']

        if hit_is_body:
            continue

        d_index = {'up': -1, 'down': 1, 'left': -1, 'right': 1}.get(d, 0)
        along_index = {'down': -1, 'up': 1, 'right': -1, 'left': 1}.get(along, 0)

        last_step_col = None
        for i, (r, c) in enumerate(ed['steps']):
            if i % 2 == 1:
                last_step_col = c

        if d == 'up':
            start_r = marker_pos[0] + 1; start_c = marker_pos[1]; set_r = start_r - d_index
        elif d == 'down':
            start_r = marker_pos[0] - 1; start_c = marker_pos[1]; set_r = start_r + d_index
        elif d == 'left':
            start_r = marker_pos[0]; start_c = marker_pos[1] + 1; set_r = start_r + along_index
        elif d == 'right':
            start_r = marker_pos[0]; start_c = marker_pos[1] - 1; set_r = start_r - along_index

        if d in ('up', 'down'):
            length = abs(start_c - last_step_col)
            col_sign = 1 if start_c < last_step_col else -1
            for c in range(start_c, last_step_col + col_sign, col_sign):
                if 0 <= set_r < H and 0 <= c < W:
                    out[set_r][c] = color
        else:
            length = abs(start_r - set_r)
            row_sign = 1 if start_r < set_r else -1
            for r in range(start_r, set_r + row_sign, row_sign):
                if 0 <= r < H and 0 <= start_c < W:
                    out[r][start_c] = color

    for c in range(W):
        if out[H-1][c] == neutral:
            out[H-1][c] = wild

    return out
```

Same overall logic as attempt 1 — connected components, marker-direction analysis, edge drawing — but with different bookkeeping for the bottom-row repaint. 96.4% of cells correct.

### `332f06d7` [near-miss, 95.3% best]

- Train shapes (in→out): `[(12, 12, 12, 12), (14, 14, 14, 14), (16, 16, 16, 16), (10, 10, 10, 10)]`
- Test shapes (in→out): `(20, 20, 20, 20)`
- Shape-preserving: **YES (same-size)**

Attempt 0 (no_grid) and Attempt 1 (95.3%) — model produced two very different algorithms. Attempt 0 used component analysis with size-based fills; attempt 1 picked the largest non-3 component and recolored it to 1 (simpler, closer to correct).

### `2c181942` [near-miss, 93.5% best]

- Shape-preserving: **YES (same-size)** — `[(23, 20), (18, 21), (20, 25)]` train, `(24, 26)` test

Model identified shape-with-2-colors components and translated them. Subtle bug in centroid-based tip detection.

### `28a6681f` [near-miss, 93.0% best]

- Shape-preserving: **YES (same-size)** — all `(10, 10)`

Model attempts shape-template matching with directional translation. Attempt 0 has syntax-suspect code (uses `comp` instead of `(i, j) for (i,j) in comp` in places); attempt 1 cleaner. Off-by-one in offset calculations.

### `1818057f`, `142ca369`, `31f7f899` — all same-size, all 90%+

All three are shape-preserving puzzles. The model writes substantive ARC-solving code — flood-fill components, find rectangles, transform colors — and gets the rule structurally right but misses fine details.

## No-grid failures (both attempts returned non-grid output)

### `0934a4d8` [no_grid]

- Train shapes (in→out): `[(30, 30, 9, 4), (30, 30, 4, 5), (30, 30, 3, 7), (30, 30, 4, 4)]`
- Test shapes (in→out): `(30, 30, 9, 3)`
- Shape-preserving: **NO** — input 30×30, output ~3-9×3-7

Model writes code that returns a 30×30 grid (input-shaped) instead of the required small output grid. **Classic shape-change failure.**

#### Attempt 0
Returns `result = [[bg]*W for _ in range(H)]` — same-size 30×30, but the puzzle wants ~5×5.

#### Attempt 1
Mutates `input_grid` in place and returns it — same-size 30×30.

### `136b0064` [no_grid]

- Train shapes: input 7-15×15, output 7-11×7 (consistent ×7 width)
- Shape-preserving: **NO**

Both attempts return `H×W` outputs, not the cropped-width 7-column output the puzzle requires.

### `13e47133` [no_grid]

- Train shapes: 20×20→20×20 and 10×13→10×13 (this one IS same-size)
- Shape-preserving: **YES** (mixed)

Despite same-size, the model's code errors out producing non-list returns. Likely the complex flood-fill logic returns `None` or partial state on the test input.

### `20270e3b`, `20a9e565`, `247ef758`, `269e22fb`, `291dc1e1`, `2ba387bc`, `2d0172a1`, `38007db0`

All non-same-size puzzles. The LoRA writes code that processes the input grid but returns a same-shape mutation rather than the expected shape change. Common pattern:
```python
out = [row[:] for row in input_grid]  # ← starts with input shape
# ...transforms in place...
return out                              # ← returns input-shaped, fails the eval
```

### `3a25b0d8`, `3e6067c3`

Incomplete in this dump — see follow-up commit.

## Pattern observed

| Puzzle category | Count (of 31) | Outcome |
|---|---|---|
| Same-size, near-miss (≥90%) | 7 | Model has the rule structure, off by handful of cells |
| Same-size, moderate (50-89%) | 6 | Model has partial rule |
| Same-size, wide miss (<50%) | 1 | Misread rule |
| Same-size, no_grid | 4 | Code crashes despite no shape change required |
| Shape-changing, no_grid | 9 | **Systematic failure**: code returns input shape, not output shape |
| Shape-changing, valid grid | 0 | **None** of the shape-changing puzzles produced even a wrong-but-valid grid |

**Conclusion**: the model has effectively zero competence on output-shape ≠ input-shape transformations. This single failure mode kills ~30% of the eval set on its own.

## Recommended training adjustments

1. **Augment `data_sft/phase2_train.jsonl` with more shape-changing puzzles.** Many ARC-AGI-2 evaluation puzzles require shape transforms (cropping, extraction, tiling). The current model writes code that always returns input-shaped output.
2. **Add an explicit "compute output shape first" reasoning step** in the training prompts for phase 2. The model could be encouraged to write `H_out, W_out = ...` before constructing the output grid.
3. **Phase-3 corrector on shape failures**: provide structured feedback like "output shape was 30×30 but expected 9×4" and train the corrector to redo the shape calculation.
