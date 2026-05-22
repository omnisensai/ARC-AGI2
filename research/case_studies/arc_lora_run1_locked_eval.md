# Case Study: arc-lora-run1 on Locked ARC-AGI-2 Eval

_Run: 2026-05-22, RunPod A100-SXM4-80GB_

## Setup

| Component | Value |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB (RunPod) |
| Base model | `Qwen/Qwen2.5-7B-Instruct` |
| LoRA adapter | `Omnisensai/arc-lora-run1` (rank=32, α=64, axolotl) |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Server | vLLM 0.21.0 |
| vLLM flags | `--enable-lora --max-lora-rank 32 --max-model-len 16384 --dtype bfloat16 --gpu-memory-utilization 0.85 --enforce-eager --chat-template <copied from LoRA repo>` |
| Eval client | `run_eval_lora.py` (system=`D`, phase2 prompt, compact grids via `substrate.format_grid`) |

Prompt format matches `build_sft_jsonl.py` phase2 records exactly:
- System message: literal `"D"`
- User message: phase2 template (`Write a Python def solve(input_grid)...`) with `format_grid()`-rendered training pairs and test input
- Grids: no spaces, no commas (one digit per cell, rows separated by `\n`)

## Eval Set

- `splits/locked_arc2_eval.json` — 120 puzzle IDs
- Source: byte-identical to `arcprize/ARC-AGI-2/data/evaluation/` (SHAs verified)
- Held out from all training per `FINETUNE_SPEC.md`

## Run Summary

| Run | Temp | Attempts/puzzle | Workers | Completed | Pass@2 |
|---|---|---|---|---|---|
| 1 | 0.7 | 2 | 8 | 60 / 240 (crash) | 0 / 31 |
| 2 | 0.2 | 2 | 4 | ~11 / 240 (killed) | 0 / 5 |

Run 1 crashed on a MooseFS `OSError: [Errno 5]` write to the network volume at attempt 60. Run 2 was started to probe whether deterministic decoding helped; killed early once the breakdown showed more `train_no_grid` and `exec_error` than Run 1 — **temperature lowering did NOT help**.

## Run 1 per-puzzle cell accuracy (sorted by best attempt)

Cell accuracy = (cells matching ground truth) / (total cells), averaged across training pairs.

| PID | best train % | a0 | a1 |
|---|---|---|---|
| `135a2760` | **98.3%** | 96.4% | 98.3% |
| `332f06d7` | **95.3%** | no_grid | 95.3% |
| `2c181942` | 93.5% | 93.5% | 90.0% |
| `28a6681f` | 93.0% | 93.0% | no_grid |
| `1818057f` | 90.4% | 90.4% | 90.4% |
| `142ca369` | 90.3% | 84.9% | 90.3% |
| `31f7f899` | 90.2% | 90.2% | 85.0% |
| `1ae2feb7` | 89.8% | 89.8% | 89.5% |
| `195c6913` | 86.8% | no_grid | 86.8% |
| `221dfab4` | 86.1% | 86.1% | no_grid |
| `16de56c4` | 80.0% | 72.2% | 80.0% |
| `3dc255db` | 80.0% | no_grid | 80.0% |
| `35ab12c3` | 79.2% | 78.6% | 79.2% |
| `16b78196` | 76.6% | 76.6% | 74.9% |
| `2b83f449` | 73.1% | 73.1% | no_grid |
| `36a08778` | 71.3% | 71.3% | 67.2% |
| `271d71e2` | 65.0% | no_grid | 65.0% |
| `21897d95` | 24.0% | no_grid | 24.0% |
| `0934a4d8` | — | no_grid | no_grid |
| `136b0064` | — | no_grid | no_grid |
| `13e47133` | — | no_grid | no_grid |
| `20270e3b` | — | no_grid | no_grid |
| `20a9e565` | — | no_grid | no_grid |
| `247ef758` | — | no_grid | no_grid |
| `269e22fb` | — | no_grid | no_grid |
| `291dc1e1` | — | no_grid | no_grid |
| `2ba387bc` | — | no_grid | no_grid |
| `2d0172a1` | — | no_grid | no_grid |
| `38007db0` | — | no_grid | no_grid |
| `3a25b0d8` | — | (only a1) no_grid | n/a |
| `3e6067c3` | — | no_grid | (only a0) n/a |

`no_grid` = `solve()` returned something that isn't a 2D list of ints (None, wrong shape, etc).

## Key findings

1. **23% of puzzles touched (7/31) reach ≥90% cell accuracy** — LoRA understands the rule structure but misses by a handful of cells. Top: `135a2760` at 98.3% (3/65 cells wrong on pair 1, 12/462 on pair 2).
2. **42% of puzzles (13/31) produced `no_grid` on both attempts** — strong systematic failure on certain transformations.
3. **0/31 exact matches**. ARC scoring is binary, so 98% counts the same as 0%.
4. **T=0.2 made things worse, not better.** The 11-attempt slice at T=0.2 showed `train_no_grid` and `exec_error` dominating where `wrong_training` had dominated at T=0.7. Sampling diversity is doing real work here.

## Failure-mode taxonomy

### A. Near-miss rules (90–99%)
Code runs cleanly, output shape correct, a few cells off. Model has the high-level rule but misses an edge case. Often boundary handling, off-by-one in iteration, or a missed condition.

The generated code for these is sophisticated — background detection, flood-fill connected components, shape classification, directional logic. Model identifies the puzzle's rule family correctly; just gets ~2% of cells wrong in execution.

### B. Shape-change failures (no_grid)
13 puzzles produced no valid grid on BOTH attempts. **Hypothesis**: these are puzzles where `output.shape != input.shape` (crops, upscaling, tiling, extraction). Training data heavily emphasized same-size transformations, so the model writes code that returns the input grid (or a same-shape modification) — failing the shape check or returning `None`.

The 13 PIDs: `0934a4d8, 136b0064, 13e47133, 20270e3b, 20a9e565, 247ef758, 269e22fb, 291dc1e1, 2ba387bc, 2d0172a1, 38007db0, 3a25b0d8, 3e6067c3`.

### C. Wide misses (<50%)
`21897d95` at 24% — model misread the rule entirely. Output shape correct, most cells wrong. Rare in this run (1/31).

## Caveats vs the "18%" target

`FINETUNE_SPEC.md` states the **18% goal is pass@10 on the same-size training split** (`splits/all_samesize.json`, 706 puzzles), NOT pass@2 on the locked `arc2_eval`. We measured against the harder, truly-held-out split with 5× fewer attempts. The numbers are not directly comparable. A pass@10 measurement on this same locked set would likely lift several near-miss puzzles into the `correct` bucket purely from sampling diversity.

## Recommended next steps

1. **Re-run as pass@10 (T=0.7)** on this locked set for a fair comparison. Estimated time: ~1h on this A100.
2. **Phase-3 corrector pass**: feed the ≥90% outputs (with structured feedback from `build_sft_jsonl.render_feedback`) into the E-task corrector. If "almost right → right" converts, that's the biggest single lever for closing the gap.
3. **Audit shape-changing puzzle coverage** in `data_sft/phase2_train.jsonl`. The 13 systematic `no_grid` failures all live in this category.
4. **Skip lowering temperature** — Run 2 disconfirmed the hypothesis. Stick with T=0.7 or higher.
5. **Longer-term**: consider full SFT instead of LoRA, or rank-128 LoRA, if held-out generalization is the bottleneck.

## Artifacts

- Raw attempts: `eval_runs/20260522_110054_arc/` on the RunPod pod (60 JSON files)
- No-grid failure code samples: see `research/case_studies/arc_lora_run1_no_grid_failures.md` (populate from pod, see next section)
- Analyzer scripts: `analyze_proximity.py`, `per_puzzle_stats.py` on pod


#Failed Codes
# Code samples from Run 1 (T=0.7, 60 attempts)

## Near-miss puzzles (≥90% cell accuracy)

## `135a2760` [near-miss]

- Train shapes (in→out): [(5, 13, 5, 13), (21, 22, 21, 22)]
- Test shapes (in→out): (29, 29, 29, 29)
- Shape-preserving: **YES (same-size)**

### Attempt 0
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
            'color': color,
            'marker_pos': (my, mx),
            'direction': d,
            'steps': steps,
            'along_direction': direction_along,
            'hit_edge_row': hit_edge_row,
            'hit_edge_col': hit_edge_col,
            'hit_is_body': hit_is_body,
            'other_marker': other_marker,
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
        hit_row = ed['hit_edge_row']
        hit_col = ed['hit_edge_col']
        marker_pos = ed['marker_pos']
        hit_is_body = ed['hit_is_body']
        hit_cell = ed['hit_cell']

        if hit_is_body:
            continue

        d_index = {'up': -1, 'down': 1, 'left': -1, 'right': 1}.get(d, 0)
        along_index = {'down': -1, 'up': 1, 'right': -1, 'left': 1}.get(along, 0)

        last_step_col = None
        for i, (r, c) in enumerate(ed['steps']):
            if i % 2 == 1:
                last_step_col = c

        if d == 'up':
            start_r = marker_pos[0] + 1
            start_c = marker_pos[1]
            set_r = start_r - d_index
        elif d == 'down':
            start_r = marker_pos[0] - 1
            start_c = marker_pos[1]
            set_r = start_r + d_index
        elif d == 'left':
            start_r = marker_pos[0]
            start_c = marker_pos[1] + 1
            set_r = start_r + along_index
        elif d == 'right':
            start_r = marker_pos[0]
            start_c = marker_pos[1] - 1
            set_r = start_r - along_index

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

### Attempt 1
```python
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]
    out = [row[:] for row in input_grid]

    border_color = grid[0][0]

    def find_rect(r, c, color, step=1):
        cells = []
        while True:
            br = r - (len(cells) - 1) * step
            bc = c - (len(cells) - 1) * step
            row_line = None
            col_line = None
            for i, v in enumerate(cells):
                rr = br + i * step
                bb = bc + i * step
                if v == color:
                    row_line = (rr, rr)
                else:
                    col_line = (bb, bb)
            if all(v == color for v in cells):
                return cells, row_line, col_line
            if step > H:
                return cells, row_line, col_line
            ncols = (len(grid[0]) - bc + step - 1) // step
            nrows = (H - br + step - 1) // step
            if nrows <= 0 or ncols <= 0:
                return cells, row_line, col_line
            enough_space = (len(cells) + min(nrows, ncols)) <= 50
            if not enough_space:
                return cells, row_line, col_line
            cells.extend([bc + i * step for i in range(ncols)])
            cells.extend([br + i * step for i in range(1, nrows)])
            if step == 1:
                cells.append(bc + ncols * step)
            else:
                cells.append(br + nrows * step)
            r += step
            c += step

    all_rects = []

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != border_color:
                continue
            cells, row_line, col_line = find_rect(r, c, input_grid[r][c], step=1)
            if not row_line or not col_line:
                continue
            r0, r1 = row_line
            c0, c1 = col_line
            thickness = len(cells)
            rect = {
                'cells': cells,
                'thickness': thickness,
                'r0': r0, 'r1': r1,
                'c0': c0, 'c1': c1,
                'row_line': row_line,
                'col_line': col_line,
            }
            all_rects.append(rect)

    rects_by_thickness = {}
    for r in all_rects:
        rects_by_thickness.setdefault(r['thickness'], []).append(r)

    candidates = []
    for thickness, group in rects_by_thickness.items():
        group = sorted(group, key=lambda r: r['r1' if r['r1'] < H - 1 else 'c1'])
        chain_rects = []
        prev_end = None
        for r in group:
            if prev_end is None:
                chain_rects.append(r)
                prev_end = r['r1' if r['r1'] < H - 1 else 'c1']
                continue
            if r['r0' if r['r0'] >= 0 else 'c0'] == prev_end + 1:
                chain_rects.append(r)
                prev_end = r['r1' if r['r1'] < H - 1 else 'c1']
            else:
                break
        if len(chain_rects) >= 2:
            candidates.append(chain_rects)

    running = True
    iteration = 0
    while running and iteration < 100:
        running = False
        for group in candidates:
            thickness = group[0]['thickness']
            rects = group
            vertical = ('r1' in rects[0]['col_line'])
            order = 'r1' if vertical else 'c1'
            spaces = [rects[i-1][order] - rects[i][order] - thickness for i in range(1, len(rects))]
            if all(s == spaces[0] for s in spaces) and spaces[0] > 0:
                total = sum(s for s in spaces) + (len(rects) - 1) * thickness
                start = rects[0]['r0' if vertical else 'c0']
                end = start + total
                if vertical:
                    for r in range(start, end):
                        c = rects[0][order]
                        while c < W:
                            out[r][c] = border_color
                            c += thickness
                else:
                    for c in range(start, end):
                        r = rects[0][order]
                        while r < H:
                            out[r][c] = border_color
                            r += thickness
                running = True
        iteration += 1

    return out
```

## `332f06d7` [near-miss]

- Train shapes (in→out): [(12, 12, 12, 12), (14, 14, 14, 14), (16, 16, 16, 16), (10, 10, 10, 10)]
- Test shapes (in→out): (20, 20, 20, 20)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])
    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    visited = [[False]*W for _ in range(H)]
    shapes = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                q = deque([(r, c)])
                visited[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not visited[ny][nx] and grid[ny][nx] != bg:
                            visited[ny][nx] = True
                            q.append((ny, nx))
                shapes.append(cells)

    out = [row[:] for row in input_grid]

    for cells in shapes:
        colors = Counter(grid[r][c] for r, c in cells)
        fill_color = colors.most_common(1)[0][0]
        size = len(cells)
        if fill_color == 2:
            new_size = 4 - size
            if new_size <= 0:
                continue
            half = new_size // 2
            for (r, c) in cells:
                if grid[r][c] == 1:
                    for dr in range(-half, half + 1):
                        for dc in range(-half, half + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < H and 0 <= nc < W:
                                if dr == -half or dr == half or dc == -half or dc == half:
                                    out[nr][nc] = 1
                                else:
                                    out[nr][nc] = 2
                else:
                    out[r][c] = 2
        elif fill_color == 1:
            new_size = 4 - size
            if new_size <= 0:
                continue
            half = new_size // 2
            for (r, c) in cells:
                if grid[r][c] == 1:
                    for dr in range(-half, half + 1):
                        for dc in range(-half, half + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < H and 0 <= nc < W:
                                out[nr][nc] = 1
                else:
                    out[r][c] = 2
        elif fill_color == 0:
            out[[r for r, c in cells][0]][[c for r, c in cells][0]] = 0

    return out
```

### Attempt 1
```python
def solve(input_grid):
    from collections import deque
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    def components(color):
        seen = [[False] * W for _ in range(H)]
        comps = []
        for r in range(H):
            for c in range(W):
                if grid[r][c] == color and not seen[r][c]:
                    q = deque([(r, c)])
                    seen[r][c] = True
                    cells = []
                    while q:
                        y, x = q.popleft()
                        cells.append((y, x))
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and grid[ny][nx] == color:
                                seen[ny][nx] = True
                                q.append((ny, nx))
                    comps.append(cells)
        return comps

    colors = set(v for row in grid for v in row if v != 3)
    best_color = None
    best_size = -1
    for color in colors:
        for cells in components(color):
            if len(cells) > best_size:
                best_size = len(cells)
                best_color = color

    out = [row[:] for row in grid]
    for r in range(H):
        for c in range(W):
            if grid[r][c] == best_color:
                out[r][c] = 1

    return out
```

## `2c181942` [near-miss]

- Train shapes (in→out): [(23, 20, 23, 20), (18, 21, 18, 21), (20, 25, 20, 25)]
- Test shapes (in→out): (24, 26, 24, 26)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    from collections import Counter
    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    visited = [[False]*W for _ in range(H)]
    comps = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                stack = [(r, c)]
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if visited[rr][cc] or grid[rr][cc] == bg:
                        continue
                    visited[rr][cc] = True
                    cells.append((rr, cc, grid[rr][cc]))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((rr + dr, cc + dc))
                comps.append(cells)

    out = [[bg] * W for _ in range(H)]

    for cells in comps:
        colors = sorted(set(c for _, _, c in cells))
        if len(colors) != 2:
            continue
        a, b = colors[0], colors[1]
        a_cells = [(r, c) for r, c, v in cells if v == a]
        b_cells = [(r, c) for r, c, v in cells if v == b]

        if not a_cells or not b_cells:
            continue

        rmin_a = min(r for r, c in a_cells)
        rmax_a = max(r for r, c in a_cells)
        cmin_a = min(c for r, c in a_cells)
        cmax_a = max(c for r, c in a_cells)
        rmin_b = min(r for r, c in b_cells)
        rmax_b = max(r for r, c in b_cells)
        cmin_b = min(c for r, c in b_cells)
        cmax_b = max(c for r, c in b_cells)

        h = rmax_a - rmin_a + 1
        w = cmax_a - cmin_a + 1
        bh = rmax_b - rmin_b + 1
        bw = cmax_b - cmin_b + 1

        if bh == w and bw == h:
            dr = rmin_b - rmax_a - 1
            dc = cmin_b - cmax_a - 1
            for r, c, v in cells:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W:
                    out[nr][nc] = v

    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    bg = 8

    colors = set()
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != bg:
                colors.add(v)

    shape_cells = {}
    shape_centers = {}
    for color in colors:
        cells = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == color]
        shape_cells[color] = cells
        avg_r = sum(p[0] for p in cells) / len(cells)
        avg_c = sum(p[1] for p in cells) / len(cells)
        shape_centers[color] = (avg_r, avg_c)

    cr = sum(v[0] for v in shape_centers.values()) / len(shape_centers)
    cc = sum(v[1] for v in shape_centers.values()) / len(shape_centers)

    tips = {}
    for color, cells in shape_cells.items():
        best = None
        best_d = None
        for (r, c) in cells:
            d = (r - cr) ** 2 + (c - cc) ** 2
            if best_d is None or d < best_d:
                best_d = d
                best = (r, c)
        tips[color] = best

    largest_color = max(shape_cells.keys(), key=lambda k: len(shape_cells[k]))

    out = [[bg] * W for _ in range(H)]

    for color, cells in shape_cells.items():
        tip = tips[color]
        target_r = int(round(tip[0]))
        target_c = int(round(tip[1]))
        for (r, c) in cells:
            dr = r - target_r
            dc = c - target_c
            nr = target_r + dr
            nc = target_c + dc
            if 0 <= nr < H and 0 <= nc < W:
                out[nr][nc] = color

    return out
```

## `28a6681f` [near-miss]

- Train shapes (in→out): [(10, 10, 10, 10), (10, 10, 10, 10), (10, 10, 10, 10)]
- Test shapes (in→out): (10, 10, 10, 10)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    from collections import deque
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    def find_components(predicate):
        seen = [[False] * W for _ in range(H)]
        comps = []
        for i in range(H):
            for j in range(W):
                if seen[i][j] or not predicate(grid[i][j]):
                    continue
                q = deque([(i, j)])
                seen[i][j] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and predicate(grid[ny][nx]):
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
        return comps

    templates = find_components(lambda v: v != 0 and v != 1 and v != 2)
    twos = find_components(lambda v: v == 2)
    ones = find_components(lambda v: v == 1)

    two_shape = set(twos[0])
    two_count = len(twos[0])
    one_shape = set(ones[0])
    one_count = len(ones[0])

    for comp in templates:
        if len(comp) != one_count:
            continue
        straights = [set({(i, j) for (y, x) in comp for i in range(y - 9, y + 10)} |
                         {((y, x) for i in range(x - 9, x + 10))})
                     for (i, j) in comp]
        s = straights[0]
        for c in straights[1:]:
            s &= c
        template_straights = s

        one_candidates = [comp for comp in ones if len(comp) == one_count
                          and set(comp) != one_shape]

        translated_template_straights = []
        for (y0, x0) in comp:
            translated = {(y - y0, x - x0) for (y, x) in template_straights}
            translated_template_straights.append(translated)

        best_one = None
        best_score = -1
        for one_comp in one_candidates:
            one_straights = [set({(i, j) for (y, x) in one_comp for i in range(y - 9, y + 10)}
                                 | {(y, x) for i in range(x - 9, x + 10)})
                             for (i, j) in one_comp]
            score = 0
            for tstr in translated_template_straights:
                for ostr in one_straights:
                    score += len(tstr & ostr)
            if score > best_score:
                best_score = score
                best_one = one_comp

        if best_one is None:
            continue

        template_cells = set(comp)
        best_one_set = set(best_one)

        offset_y = sum(y for (y, x) in comp) / len(comp) \
                   - sum(y for (y, x) in best_one) / len(best_one)
        offset_x = sum(x for (y, x) in comp) / len(comp) \
                   - sum(x for (y, x) in best_one) / len(best_one)

        for (y, x) in template_cells:
            ny = round(y + offset_y)
            nx = round(x + offset_x)
            if 0 <= ny < H and 0 <= nx < W:
                grid[ny][nx] = 0
        for (y, x) in best_one_set:
            if 0 <= y < H and 0 <= x < W:
                grid[y][x] = 0

    return grid
```

### Attempt 1
```python
def solve(input_grid):
    from collections import deque
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    def find_components(predicate):
        seen = [[False] * W for _ in range(H)]
        comps = []
        for i in range(H):
            for j in range(W):
                if seen[i][j] or not predicate(grid[i][j]):
                    continue
                q = deque([(i, j)])
                seen[i][j] = True
                cells = []
                while q:
                    r, c = q.popleft()
                    cells.append((r, c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < H and 0 <= nc < W and not seen[nr][nc] and predicate(grid[nr][nc]):
                            seen[nr][nc] = True
                            q.append((nr, nc))
                comps.append(cells)
        return comps

    template_comps = find_components(lambda v: v != 0 and v != 1 and v != 2)
    if not template_comps:
        return grid
    template_cells = max(template_comps, key=len)
    ts = [(i, j) for i, j in template_cells]
    t_rows = [i for i, j in ts]
    t_cols = [j for i, j in ts]
    t_min_r, t_max_r = min(t_rows), max(t_rows)
    t_min_c, t_max_c = min(t_cols), max(t_cols)

    ones = find_components(lambda v: v == 1)[0]
    oh = max(r for r, c in ones)
    ot = min(r for r, c in ones)

    target_rows = [r for r, c in ones]
    target_cols = [c for r, c in ones]
    tgt_min_r = min(target_rows)
    tgt_max_r = max(target_rows)
    tgt_min_c = min(target_cols)
    tgt_max_c = max(target_cols)

    vert_gap = ot - oh - 1
    horz_gap = 1 + vert_gap

    template_rows_full = t_max_r - t_min_r + 1
    template_cols_full = t_max_c - t_min_c + 1

    last_row_end = tgt_max_r + template_rows_full - 1
    first_row_start = tgt_min_r - template_rows_full + 1
    last_col_end = tgt_max_c + template_cols_full - 1
    first_col_start = tgt_min_c - template_cols_full + 1

    for i, j in ts:
        ni = i - t_min_r + first_row_start
        nj = j - t_min_c + first_col_start
        if 0 <= ni < H and 0 <= nj < W:
            grid[ni][nj] = grid[i][j]

    for r in range(first_row_start, last_row_end + 1):
        for c in range(tgt_min_c, tgt_max_c + 1):
            if grid[r][c] != 1:
                grid[r][c] = 0
    for c in range(first_col_start, last_col_end + 1):
        for r in range(tgt_min_r, tgt_max_r + 1):
            if grid[r][c] != 1:
                grid[r][c] = 0

    return grid
```

## `1818057f` [near-miss]

- Train shapes (in→out): [(10, 12, 10, 12), (15, 17, 15, 17), (12, 12, 12, 12)]
- Test shapes (in→out): (22, 22, 22, 22)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]
    fg = None
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 2 and v != 4:
                fg = v
                break
        if fg is not None:
            break
    out = [row[:] for row in grid]
    for r in range(H):
        for c in range(W):
            if grid[r][c] == fg:
                out[r][W - 1 - c] = 8
    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    key_r = key_c = -1
    for r in range(H - 1):
        for c in range(W - 1):
            vals = [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]]
            if all(v == 4 for v in vals):
                key_r, key_c = r, c
                break
        if key_r != -1:
            break

    key = [[grid[key_r + 0 - i][key_c + 0 - j] for j in range(2)] for i in range(2)]

    def reflect(v):
        if v == 2:
            return 8
        if v == 4:
            return 4
        if v == 8:
            return 2
        return v

    out = [row[:] for row in grid]
    for r in range(H):
        for c in range(W):
            if out[r][c] == 4:
                continue
            dr = r - (key_r + 0.5)
            dc = c - (key_c + 0.5)
            if abs(dr) > 1 or abs(dc) > 1:
                continue
            ii = int(round(dr))
            jj = int(round(dc))
            out[r][c] = reflect(key[ii][jj])

    return out
```

## `142ca369` [near-miss]

- Train shapes (in→out): [(20, 20, 20, 20), (18, 18, 18, 18), (20, 20, 20, 20)]
- Test shapes (in→out): (18, 18, 18, 18)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    counts = {}
    for r in range(H):
        for c in range(W):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    colors = list(counts.keys())
    bbox = {}
    for col in colors:
        rs = [r for r in range(H) for c in range(W) if grid[r][c] == col]
        cs = [c for r in range(H) for c in range(W) if grid[r][c] == col]
        bbox[col] = (min(rs), max(rs), min(cs), max(cs))

    A = None
    B = None
    for c1 in colors:
        for c2 in colors:
            if c1 == c2:
                continue
            r1a, r2a, c1a, c2a = bbox[c1]
            r1b, r2b, c1b, c2b = bbox[c2]
            if r1a <= r1b and r2a >= r2b and c1a <= c1b and c2a >= c2b and (r1a < r1b or r2a > r2b or c1a < c1b or c2a > c2b):
                A = c1
                B = c2
                break
        if A is not None:
            break

    fr1, fr2, fc1, fc2 = bbox[A]
    br1, br2, bc1, bc2 = bbox[B]

    row_extents = {}
    for r in range(br1, br2 + 1):
        cs = [c for c in range(W) if grid[r][c] == B]
        if cs:
            row_extents[r] = (min(cs), max(cs))
    col_extents = {}
    for c in range(bc1, bc2 + 1):
        rs = [r for r in range(H) if grid[r][c] == B]
        if rs:
            col_extents[c] = (min(rs), max(rs))

    from collections import Counter
    rc = Counter(row_extents.values())
    core_cols = rc.most_common(1)[0][0]
    cc = Counter(col_extents.values())
    core_rows = cc.most_common(1)[0][0]

    core_r1, core_r2 = core_rows
    core_c1, core_c2 = core_cols

    top_cols = []
    bot_cols = []
    left_rows = []
    right_rows = []

    for c in range(W):
        if core_r1 - 1 >= 0 and grid[core_r1 - 1][c] == B:
            top_cols.append(c)
        if core_r2 + 1 < H and grid[core_r2 + 1][c] == B:
            bot_cols.append(c)
    for r in range(H):
        if core_c1 - 1 >= 0 and grid[r][core_c1 - 1] == B:
            left_rows.append(r)
        if core_c2 + 1 < W and grid[r][core_c2 + 1] == B:
            right_rows.append(r)

    out = [row[:] for row in input_grid]

    for r in range(fr1, fr2 + 1):
        for c in range(fc1, fc2 + 1):
            if out[r][c] == B:
                out[r][c] = A

    for r in range(core_r1, core_r2 + 1):
        for c in range(core_c1, core_c2 + 1):
            out[r][c] = B

    protrusion_cols = set(top_cols) | set(bot_cols)
    protrusion_rows = set(left_rows) | set(right_rows)

    for c in protrusion_cols:
        for r in range(core_r1, core_r2 + 1):
            out[r][c] = A
    for r in protrusion_rows:
        for c in range(core_c1, core_c2 + 1):
            out[r][c] = A

    for c in protrusion_cols:
        for r in range(0, fr1):
            out[r][c] = B
        for r in range(fr2 + 1, H):
            out[r][c] = B

    for r in protrusion_rows:
        for c in range(0, fc1):
            out[r][c] = B
        for c in range(fc2 + 1, W):
            out[r][c] = B

    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    corners = []
    for r in range(H - 1):
        for c in range(W - 1):
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            vals = [grid[rr][cc] for rr, cc in cells]
            colored = [(i, v) for i, v in enumerate(vals) if v != 0 and v != 1]
            if len(colored) != 3:
                continue
            colors = set(v for _, v in colored)
            if len(colors) != 1:
                continue
            color = next(iter(colors))
            colored_idx = [j for j, _ in colored]
            empty_idx = [i for i in range(4) if i not in colored_idx]
            ei = empty_idx[0]
            if ei == 3:
                orient = 'TL'; outer = (r, c)
            elif ei == 2:
                orient = 'TR'; outer = (r, c + 1)
            elif ei == 1:
                orient = 'BL'; outer = (r + 1, c)
            else:
                orient = 'BR'; outer = (r + 1, c + 1)
            corners.append((color, orient, outer))

    by_color = {}
    for color, orient, outer in corners:
        by_color.setdefault(color, {'TL': [], 'TR': [], 'BL': [], 'BR': []})[orient].append(outer)

    rectangles = []
    for color, d in by_color.items():
        for tl in d['TL']:
            for tr in d['TR']:
                if tl[0] != tr[0] or tr[1] <= tl[1]:
                    continue
                for bl in d['BL']:
                    if bl[1] != tl[1] or bl[0] <= tl[0]:
                        continue
                    for br in d['BR']:
                        if br[0] == bl[0] and br[1] == tr[1]:
                            rectangles.append((tl[0], tl[1], br[0], br[1], color))

    inside = [[False] * W for _ in range(H)]
    for r1, c1, r2, c2, _ in rectangles:
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                inside[rr][cc] = True

    out = [row[:] for row in grid]
    for r in range(H):
        for c in range(W):
            if inside[r][c]:
                out[r][c] = 1

    for r1, c1, r2, c2, color in rectangles:
        h = r2 - r1 + 1
        w = c2 - c1 + 1
        for i in range(max(0, r1 + 1), min(H, r1 + h - 1)):
            for j in range(max(0, c1 + 1), min(W, c1 + w - 1)):
                if out[i][j] != color:
                    out[i][j] = color

    return out
```

## `31f7f899` [near-miss]

- Train shapes (in→out): [(13, 13, 13, 13), (15, 15, 15, 15), (7, 7, 7, 7)]
- Test shapes (in→out): (17, 17, 17, 17)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    g = [row[:] for row in input_grid]

    six_row = None
    for r in range(H):
        if any(v == 6 for v in g[r]):
            six_row = r
            break

    right_col = None
    for c in range(W):
        if g[six_row][c] == 6:
            right_col = c
            break

    shapes = {
        5: (0, 0),
        7: (0, 1),
     16: (1, 0),
     26: (1, 1),
     36: (2, 0),
     46: (2, 1),
     56: (3, 0),
     66: (3, 1),
     76: (4, 0),
     86: (4, 1),
    }

    for r in range(H):
        for c in range(right_col, W):
            v = g[r][c]
            if v == 6:
                break
            if v in shapes:
                dr, dc = shapes[v]
                if r - dr >= 0 and c - dc >= 0:
                    g[r][c] = g[r - dr][c - dc]

    return g
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    g = [row[:] for row in input_grid]

    six_rows = set()
    for r in range(H):
        for c in range(W):
            if g[r][c] == 6:
                six_rows.add(r)
                break

    template_row = None
    template_col = None
    template = None
    for r in six_rows:
        for c in range(W):
            if g[r][c] != 8:
                template_row = r
                template_col = c
                template = g[r][c]
                break
        if template is not None:
            break

    for r in range(H):
        for c in range(W):
            if g[r][c] == template:
                g[r][c] = 8

    for r in range(H):
        for c in range(W):
            if g[r][c] == 6:
                rr = r - template_row
                cc = c - template_col
                new_r = six_rows.issuperset({r + rr})
                new_c = six_rows.issuperset({c + cc})
                if new_r and new_c:
                    g[r][c] = template
                else:
                    g[r][c] = 8

    return g
```


## No-grid failures (both attempts returned non-grid)

## `0934a4d8` [no_grid]

- Train shapes (in→out): [(30, 30, 9, 4), (30, 30, 4, 5), (30, 30, 3, 7), (30, 30, 4, 4)]
- Test shapes (in→out): (30, 30, 9, 3)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    counts = {}
    for row in input_grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)

    other_colors = {k: v for k,v in counts.items() if k != bg}

    def find_min_convex(H, W, cls):
        areas = []
        perimeters = []
        for r in range(1, H):
            for c in range(1, W):
                if input_grid[r][c] != cls and input_grid[r-1][c] == cls and input_grid[r][c-1] == cls and input_grid[r-1][c-1] == cls:
                    ok = True
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            if input_grid[r+dr][c+dc] != cls:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        areas.append(r*c)
                        perimeters.append((r+1)*(c+1))

        if not areas:
            return None, None
        idx = areas.index(min(areas))
        return perimeters[idx], areas[idx]

    by_color = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v == bg:
                continue
            by_color.setdefault(v, []).append((r, c))

    shapes = []
    for color, cells in by_color.items():
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        h = max(rs) - min(rs) + 1
        w = max(cs) - min(cs) + 1
        shapes.append((color, h, w, cells))

    used = set()
    result = [[bg]*W for _ in range(H)]
    remaining = list(range(len(shapes)))

    while remaining:
        color_idx = remaining[0]
        color, h, w, cells = shapes[color_idx]
        p_required, a_required = find_min_convex(H, W, bg)
        found = False
        for i in range(len(shapes)):
            if i in used:
                continue
            if i == color_idx:
                continue
            other_color, other_h, other_w, other_cells = shapes[i]
            if other_color == color:
                continue
            if other_h > h or other_w > w:
                perim, area = find_min_convex(other_h, other_w, other_color)
                if perim == p_required and area == a_required:
                    used.add(i)
                    for (rr, cc) in other_cells:
                        result[rr][cc] = other_color
                    remaining.remove(i)
                    found = True
                    break
        if not found:
            best = None
            best_score = float('inf')
            for i in remaining:
                other_color, other_h, other_w, _ = shapes[i]
                score = max(other_h, other_w) ** 2
                if score < best_score:
                    best_score = score
                    best = i
            used.add(best)
            other_color, other_h, other_w, other_cells = shapes[best]
            for (rr, cc) in other_cells:
                result[rr][cc] = other_color
            remaining.remove(best)

    return result
```

### Attempt 1
```python
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    running = True
    rounds = 0
    while running:
        counts = Counter()
        for row in input_grid:
            for v in row:
                counts[v] += 1
        top_color = counts.most_common(1)[0][0]

        marker_rows = []
        for r in range(H):
            if input_grid[r][W // 2] == top_color:
                marker_rows.append(r)
        marker_cols = []
        for c in range(W):
            if input_grid[H // 2][c] == top_color:
                marker_cols.append(c)

        A_rows = sorted(set(marker_rows) - {H // 2})
        A_cols = sorted(set(marker_cols) - {W // 2})

        A_R = max(A_rows) + 1
        A_C = max(A_cols) + 1
        B_R = H - A_R - 1
        B_C = W - A_C - 1

        cells = []
        for r in range(A_R, H - A_R):
            for c in range(A_C, W - A_C):
                cells.append(input_grid[r][c])

        mc = Counter(cells).most_common(1)[0][0]
        new_color = mc[0] if len(cells) > 0 else 0

        for r in range(A_R, H - A_R):
            for c in range(A_C, W - A_C):
                input_grid[r][c] = new_color

        if rounds >= 10:
            running = False

        rounds += 1

    return input_grid
```

## `136b0064` [no_grid]

- Train shapes (in→out): [(15, 15, 15, 7), (7, 15, 7, 7), (11, 15, 11, 7)]
- Test shapes (in→out): (19, 15, 19, 7)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    fours = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 4]
    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]
    ones = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 1]

    R_min = min(r for r, c in fours)
    R_max = max(r for r, c in fours)
    C_min = min(c for r, c in fours)
    C_max = max(c for r, c in fours)

    shapes = {
        'fours': fours,
        'sixes': [(r, 2 * C_max - c) for r, c in sixes],
        'ones': ones,
    }

    def mirror(cells):
        return [(r, 2 * R_max - r, c) for r, c in cells]

    colors = ['fours', 'sixes', 'ones']
    py = {c: 0 for c in range(3)}
    px = {c: 0 for c in range(3)}
    for i, name in enumerate(colors):
        for r, c in shapes[name]:
            py[i] += r
            px[i] += c
        py[i] /= len(shapes[name])
        px[i] /= len(shapes[name])

    out = [[0] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            closest = min(range(3), key=lambda i: abs(r - py[i]) + abs(c - px[i]))
            out[r][c] = {0: 2, 1: 1, 2: 3}[closest]

    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    fours = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 4:
                fours.append((r, c))
    fives = []
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 5:
                fives.append((r, c))

    def has_nonzero_neighbor(pos):
        r, c = pos
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W:
                    if input_grid[nr][nc] != 0 and input_grid[nr][nc] != 4:
                        return True
        return False

    def components(pred):
        seen = [[False] * W for _ in range(H)]
        comps = []
        for r in range(H):
            for c in range(W):
                if not seen[r][c] and pred(r, c):
                    stack = [(r, c)]
                    comp = []
                    while stack:
                        cr, cc = stack.pop()
                        if cr < 0 or cr >= H or cc < 0 or cc >= W:
                            continue
                        if seen[cr][cc]:
                            continue
                        if not pred(cr, cc):
                            continue
                        seen[cr][cc] = True
                        comp.append((cr, cc))
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = cr + dr, cc + dc
                                stack.append((nr, nc))
                    comps.append(comp)
        return comps

    four_comps = components(lambda r, c: (r, c) in fours)
    five_comps = components(lambda r, c: (r, c) in fives)

    four_centers = [(sum(x for x, y in comp) / len(comp), sum(y for x, y in comp) / len(comp)) for comp in four_comps]
    five_centers = [(sum(x for x, y in comp) / len(comp), sum(y for x, y in comp) / len(comp)) for comp in five_comps]

    def find_closest_fiver(r, c):
        min_dist = float('inf')
        closest = None
        for i, (xr, yr) in enumerate(five_centers):
            dist = abs(xr - r) + abs(yr - c)
            if dist < min_dist:
                min_dist = dist
                closest = i
        return closest

    def find_closest_foure(r, c):
        min_dist = float('inf')
        closest = None
        for i, (xr, yr) in enumerate(four_centers):
            dist = abs(xr - r) + abs(yr - c)
            if dist < min_dist:
                min_dist = dist
                closest = i
        return closest

    six = None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 6:
                six = (r, c)
                break
        if six:
            break

    sr, sc = six

    closest_five_idx = find_closest_fiver(sr, sc)
    closest_four_idx = find_closest_foure(sr, sc)

    tk = five_comps[closest_five_idx]
    tk_4 = four_comps[closest_four_idx]

    tk_set = set(tk)
    best_dir = None
    best_count = -1
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        count = sum(1 for (x, y) in tk if (x + dr, y + dc) in tk_set)
        if count > best_count:
            best_count = count
            best_dir = (dr, dc)

    dr, dc = best_dir

    output = [[0] * W for _ in range(H)]
    for (x, y) in tk:
        nr, nc = x + dr, y + dc
        if 0 <= nr < H and 0 <= nc < W:
            output[nr][nc] = 1

    for (x, y) in tk_4:
        nr, nc = x + dr, y + dc
        if 0 <= nr < H and 0 <= nc < W:
            output[nr][nc] = 2

    return output
```

## `13e47133` [no_grid]

- Train shapes (in→out): [(20, 20, 20, 20), (20, 20, 20, 20), (10, 13, 10, 13)]
- Test shapes (in→out): (30, 30, 30, 30)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    row1, col1 = None, None
    row2, col2 = None, None
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                if row1 is None:
                    row1, col1 = r, c
                else:
                    row2, col2 = r, c

    def find_components(cells_set):
        visited = set()
        comps = []
        for cell in cells_set:
            if cell in visited:
                continue
            color = None
            q = deque([cell])
            visited.add(cell)
            comp = []
            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in cells_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
            comps.append(comp)
        return comps

    horiz_bridge = {(row1, col1), (row1, col2)}
    vert_bridge = {(row1, col1), (row2, col1)}

    bridge_cells = set()
    bridge_cells.update(horiz_bridge)
    bridge_cells.update(vert_bridge)

    rect_cells = set()
    r_min = min(col1, col2)
    r_max = max(col1, col2)
    for c in (col1, col2):
        for r in range(row1 + 1, row2):
            rect_cells.add((r, c))

    outer = find_components(rect_cells - bridge_cells)

    gaps = []
    for comp in outer:
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r_min, r_max = min(rs), max(rs)
        c_min, c_max = min(cs), max(cs)
        gap = None
        if r_min > 0:
            gap = ('up', r_min, c_min, c_max)
        elif r_max < H - 1:
            gap = ('down', r_max, c_min, c_max)
        elif c_min > 0:
            gap = ('left', c_min, r_min, r_max)
        elif c_max < W - 1:
            gap = ('right', c_max, r_min, r_max)
        if gap is not None:
            gaps.append(gap)

    if not gaps:
        solid_color = 0
        for r in range(H):
            for c in range(W):
                v = input_grid[r][c]
                if v != 1 and v != 2:
                    solid_color = v
                    break
            if solid_color != 0:
                break
        return grid

    chosen = None
    for g in gaps:
        if g[0] in ('left', 'right'):
            chosen = g
            break
    if chosen is None:
        chosen = gaps[0]

    orientation, center_c, r_min, r_max = chosen
    if orientation == 'left':
        c_min = center_c
        c_max = center_c
        direction = 'right'
    elif orientation == 'right':
        c_min = center_c
        c_max = center_c
        direction = 'left'
    elif orientation == 'up':
        r_min = center_r
        r_max = center_r
        direction = 'down'
    elif orientation == 'down':
        r_min = center_r
        r_max = center_r
        direction = 'up'

    if direction == 'right':
        skeleton_cells = {(r, c) for r in range(r_min, r_max + 1) for c in range(0, col2)}
    elif direction == 'left':
        skeleton_cells = {(r, c) for r in range(r_min, r_max + 1) for c in range(col1, W)}
    elif direction == 'down':
        skeleton_cells = {(r, c) for r in range(0, row2) for c in range(c_min, c_max + 1)}
    elif direction == 'up':
        skeleton_cells = {(r, c) for r in range(row1, H) for c in range(c_min, c_max + 1)}

    skeleton_visited = set()
    markers = []
    for sc in skeleton_cells:
        if sc in bridge_cells or sc in rect_cells:
            continue
        q = deque([sc])
        skeleton_visited.add(sc)
        marked = False
        comp = []
        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in skeleton_cells and (nr, nc) not in skeleton_visited:
                    skeleton_visited.add((nr, nc))
                    q.append((nr, nc))
                    marked = True
        if marked:
            markers.append(comp)

    for comp in markers:
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r_min, r_max = min(rs), max(rs)
        c_min, c_max = min(cs), max(cs)

    marker_colors = set(v for r, c, v in markers)
    if len(marker_colors) == 1:
        fill_color = next(iter(marker_colors))
    else:
        if any(c == 2 for c in marker_colors):
            fill_color = 2
        else:
            fill_color = 0

    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                grid[r][c] = fill_color

    return grid
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    color = None
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 1 and v != 2:
                color = v
                break
        if color is not None:
            break

    if color is None:
        return [row[:] for row in input_grid]

    def find_components(cells_set, num_cells):
        visited = set()
        comps = []
        for cell in cells_set:
            if cell in visited:
                continue
            queue = deque([cell])
            visited.add(cell)
            comp = []
            while queue:
                r, c = queue.popleft()
                comp.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in cells_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            comps.append(comp)
        if len(comps) < 2:
            return []
        largest = max(comps, key=len)
        smallest = min(comps, key=len)
        Small = frozenset(smallest)
        if len(largest) > 2 * len(smallest):
            return [Small, frozenset(largest)]
        return []

    twenty_cells = set()
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 2:
                twenty_cells.add((r, c))

    visited = set()
    queue = deque([])
    for r in range(H):
        for c in range(W):
            if (r, c) in twenty_cells and ((r, c) not in visited or len(twenty_cells) == 1):
                visited.add((r, c))
                queue.append((r, c))
                if len(twenty_cells) == 1:
                    break
        if len(twenty_cells) == 1:
            break
    cluster = set()
    while queue:
        r, c = queue.popleft()
        cluster.add((r, c))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in twenty_cells and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))

    def symmetries_and_flips():
        result = set()
        s = frozenset(cluster)
        for offset in [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            shifted = frozenset((r - offset[0], c - offset[1]) for r, c in s)
            if shifted != s and shifted <= set(twenty_cells):
                result.add(shifted)
        for orientation in [s, frozenset((c, r) for r, c in s)]:
            result.add(orientation)
            for offset in [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                shifted = frozenset((r - offset[0], c - offset[1]) for r, c in orientation)
                if shifted != orientation and shifted <= set(twenty_cells):
                    result.add(shifted)
        return result

    syms_and_flips = symmetries_and_flips()

    out = [row[:] for row in input_grid]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] == 1:
                out[r][c] = color

    for small in syms_and_flips:
        representative = frozenset((r - 1, c - 1) for r, c in small)
        new_cluster = set()
        for r, c in representative:
            if 0 <= r < H and 0 <= c < W and (r, c) not in twenty_cells:
                nr, nc = r + 1, c + 1
                if 0 <= nr < H and 0 <= nc < W:
                    new_cluster.add((nr, nc))
        for r, c in small:
            if 0 <= r < H and 0 <= c < W and (r, c) not in twenty_cells:
                nr, nc = r + 1, c + 1
                if 0 <= nr < H and 0 <= nc < W:
                    out[nr][nc] = 2
        as_set = set(new_cluster)
        for (r, c) in as_set:
            if (r, c) in twenty_cells:
                as_set.discard((r, c))
                as_set.add((r, c - 1))
                as_set.add((r, c + 1))
                as_set.add((r - 1, c))
                as_set.add((r + 1, c))
        for (r, c) in as_set:
            if not (0 <= r < H and 0 <= c < W):
                continue
            if r == 0 or r == H - 1 or c == 0 or c == W - 1:
                out[r][c] = 8
            else:
                out[r][c] = 2

    return out
```

## `20270e3b` [no_grid]

- Train shapes (in→out): [(7, 13, 7, 8), (7, 13, 7, 6), (9, 3, 6, 3), (7, 9, 5, 12)]
- Test shapes (in→out): (11, 10, 5, 10)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    out = [row[:] for row in input_grid]
    visited = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if input_grid[r][c] == 7 and not visited[r][c]:
                seven_col = c
                break
        else:
            continue
        for c in range(w):
            if input_grid[r][c] == 1:
                one_col = c
                break
        color = input_grid[r][one_col]
        left_count = one_col
        right_count = w - one_col - 1
        for direction, count in [(+1, right_count), (-1, left_count)]:
            c = one_col + direction
            while 0 <= c < w:
                if input_grid[r][c] == color:
                    out[r][c] = 4
                else:
                    break
                c += direction
    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[input_grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]
    non_bg_colors = [k for k in cnt if k != bg]

    def has_bg_neighbor(color):
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] != color:
                    continue
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < H and 0 <= nc < W):
                        return True
                    if input_grid[nr][nc] == bg:
                        return True
        return False

    outer_color = None
    for color in non_bg_colors:
        if has_bg_neighbor(color):
            outer_color = color
            break

    inner_candidates = [c for c in non_bg_colors if c != outer_color]
    inner_color = None
    for color in inner_candidates:
        touches_outer = False
        for r in range(H):
            for c in range(W):
                if input_grid[r][c] != color:
                    continue
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and input_grid[nr][nc] == outer_color:
                        touches_outer = True
                        break
                if touches_outer:
                    break
            if touches_outer:
                break
        if not touches_outer:
            inner_color = color
            break

    if inner_color is None:
        if inner_candidates:
            inner_color = min(inner_candidates, key=lambda c: cnt[c])
        else:
            inner_color = outer_color

    output = [[bg] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if input_grid[r][c] != outer_color:
                continue
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                outward = False
                if not (0 <= nr < H and 0 <= nc < W):
                    outward = True
                elif input_grid[nr][nc] == bg:
                    outward = True
                if outward and 0 <= nr < H and 0 <= nc < W:
                    output[nr][nc] = inner_color
    return output
```

## `20a9e565` [no_grid]

- Train shapes (in→out): [(30, 30, 3, 6), (29, 29, 14, 2), (30, 30, 17, 3)]
- Test shapes (in→out): (30, 30, 2, 21)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    color_cells = {}
    for r in range(H):
        for c in range(W):
            v = input_grid[r][c]
            if v != 0:
                color_cells.setdefault(v, []).append((r, c))

    components = [{'color': c, 'cells': cells} for c, cells in color_cells.items()]

    components.sort(key=lambda c: min(r for r, _ in c['cells']))

    spans = []
    for c in components:
        rs = [r for r, _ in c['cells']]
        spans.append((min(rs), max(rs)))

    output = [[0]*W for _ in range(H)]

    if not components:
        return output

    global_top = min(s[0] for s in spans)

    current_top = global_top
    for c, (top, bot) in reversed(list(zip(components, spans))):
        height = bot - top + 1
        offset = current_top - top
        for r, col in c['cells']:
            nr = r + offset
            output[nr][col] = c['color']
        current_top += height

    return output
```

### Attempt 1
```python
def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])

    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    visited = [[False]*W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                q = deque([(r,c)])
                visited[r][c] = True
                comp = []
                while q:
                    y,x = q.popleft()
                    comp.append((y,x,grid[y][x]))
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            if dy==0 and dx==0: continue
                            ny,nx = y+dy, x+dx
                            if 0<=ny<H and 0<=nx<W and not visited[ny][nx] and grid[ny][nx]!=bg:
                                visited[ny][nx] = True
                                q.append((ny,nx))
                components.append(comp)

    def bbox(comp):
        rs = [c[0] for c in comp]
        cs = [c[1] for c in comp]
        return min(rs), min(cs), max(rs), max(cs)

    n = len(components)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a,b):
        ra,rb = find(a), find(b)
        if ra != rb: parent[ra] = rb

    PROX = 2
    bboxes = [bbox(c) for c in components]
    for i in range(n):
        for j in range(i+1, n):
            r1a,c1a,r2a,c2a = bboxes[i]
            r1b,c1b,r2b,c2b = bboxes[j]
            dr = max(0, max(r1a,r1b) - min(r2a,r2b))
            dc = max(0, max(c1a,c1b) - min(c2a,c2b))
            if dr <= PROX and dc <= PROX:
                union(i,j)

    clusters = {}
    for i in range(n):
        rr = find(i)
        clusters.setdefault(rr, []).append(i)

    cluster_info = []
    for k, idxs in clusters.items():
        cells = []
        for i in idxs:
            cells.extend(components[i])
        colors = frozenset(c[2] for c in cells)
        cluster_info.append({'idx': k, 'comps': idxs, 'cells': cells, 'colors': colors})

    def normalize(cells):
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        mr, mc = min(rs), min(cs)
        return frozenset((r-mr, c-mc, v) for r,c,v in cells), mr, mc

    norm_patterns = []
    for ci in cluster_info:
        pat, mr, mc = normalize(ci['cells'])
        norm_patterns.append((pat, mr, mc))

    def is_subset_under_translation(small_pat, large_pat):
        small_list = list(small_pat)
        if not small_list: return None
        s0 = small_list[0]
        for lc in large_pat:
            if lc[2] != s0[2]: continue
            off_r = lc[0] - s0[0]
            off_c = lc[1] - s0[1]
            shifted = frozenset((r+off_r, c+off_c, v) for r,c,v in small_pat)
            if shifted <= large_pat:
                return (off_r, off_c)
        return None

    is_partial = [False]*len(cluster_info)
    template_of = [None]*len(cluster_info)
    offset_of = [None]*len(cluster_info)
    for i, ci in enumerate(cluster_info):
        best_size = 0
        for j, cj in enumerate(cluster_info):
            if i == j: continue
            if len(cj['cells']) <= len(ci['cells']): continue
            if not ci['colors'].issubset(cj['colors']): continue
            off = is_subset_under_translation(norm_patterns[i][0], norm_patterns[j][0])
            if off is not None:
                if len(cj['cells']) > best_size:
                    best_size = len(cj['cells'])
                    template_of[i] = j
                    offset_of[i] = off
                    is_partial[i] = True

    output = [row[:] for row in grid]

    unique_colors = {color for color, c in cnt.items() if c == 1 and color != bg}

    template_indices = set()
    for i in range(len(cluster_info)):
        if is_partial[i]:
            template_indices.add(template_of[i])

    for partial_idx in range(len(cluster_info)):
        if not is_partial[partial_idx]:
            continue
        template_idx = template_of[partial_idx]
        off_r, off_c = offset_of[partial_idx]
        partial_pat, p_mr, p_mc = norm_patterns[partial_idx]
        template_pat, t_mr, t_mc = norm_patterns[template_idx]
        for DR, DC, v in template_pat:
            gr = DR - off_r + p_mr
            gc = DC - off_c + p_mc
            if 0 <= gr < H and 0 <= gc < W:
                output[gr][gc] = v

    for color in unique_colors:
        for r in range(H):
            for c in range(W):
                if grid[r][c] == color:
                    for ti in template_indices:
                        cells = cluster_info[ti]['cells']
                        if any(cr == r and cc == c for cr,cc,_ in cells):
                            output[r][c] = bg
                            break

    return output
```

## `247ef758` [no_grid]

- Train shapes (in→out): [(12, 18, 12, 18), (10, 15, 10, 15), (10, 14, 10, 14)]
- Test shapes (in→out): (15, 20, 15, 20)
- Shape-preserving: **YES (same-size)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    visited = [[False] * W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not visited[r][c]:
                comp = []
                q = deque([(r, c)])
                visited[r][c] = True
                while q:
                    rr, cc = q.popleft()
                    comp.append((rr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < H and 0 <= nc < W and not visited[nr][nc] and grid[nr][nc] != 0:
                            visited[nr][nc] = True
                            q.append((nr, nc))
                components.append(comp)

    out = [row[:] for row in input_grid]

    for comp in components:
        rs = [p[0] for p in comp]
        cs = [p[1] for p in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        bh = r1 - r0 + 1
        bw = c1 - c0 + 1
        local = [[grid[r0 + i][c0 + j] for j in range(bw)] for i in range(bh)]

        rows_with_nonzero = [i for i in range(bh) if any(local[i][j] != 0 for j in range(bw))]
        cols_with_nonzero = [j for j in range(bw) if any(local[i][j] != 0 for i in range(bh))]
        if not rows_with_nonzero or not cols_with_nonzero:
            continue
        rmin, rmax = min(rows_with_nonzero), max(rows_with_nonzero)
        cmin, cmax = min(cols_with_nonzero), max(cols_with_nonzero)

        h = rmax - rmin + 1
        w = cmax - cmin + 1
        pattern = [[local[rmin + i][cmin + j] for j in range(w)] for i in range(h)]

        for i in range(h):
            for j in range(w):
                out[r0 + i][c0 + j] = pattern[i][j]

    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    corners = [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]
    L_corner = None
    L_color = None
    for (r, c) in corners:
        col_val = grid[r][c]
        row_full = all(grid[r][j] == col_val for j in range(W))
        col_full = all(grid[i][c] == col_val for i in range(H))
        if row_full and col_full:
            L_corner = (r, c)
            L_color = col_val
            break

    r0, c0 = L_corner
    arm_rows = [r0]
    if r0 + 1 < H:
        arm_rows.append(r0 + 1)
    arm_cols = [c0]
    if c0 + 1 < W:
        arm_cols.append(c0 + 1)

    for ce in arm_cols:
        for i in range(r0 + 2, H):
            new_color = grid[i][ce]
            if new_color != 0:
                break
        arm_rows.append(i)

    for ro in arm_rows:
        for i in range(c0 + 2, W):
            new_color = grid[ro][i]
            if new_color != 0:
                break
        arm_cols.append(i)

    clean_rows = [r for r in range(H) if r in arm_rows]
    clean_cols = [c for c in range(W) if c in arm_cols]
    for r in clean_rows:
        for c in clean_cols:
            grid[r][c] = 0

    return grid
```

## `269e22fb` [no_grid]

- Train shapes (in→out): [(8, 10, 20, 20), (16, 8, 20, 20), (10, 10, 20, 20), (13, 12, 20, 20), (8, 10, 20, 20)]
- Test shapes (in→out): (10, 10, 20, 20)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    g = [row[:] for row in input_grid]

    diag_val = None
    for i in range(min(H, W)):
        if g[i][i] != 0:
            diag_val = g[i][i]
            break

    bg_val = g[0][1] if g[0][1] != 0 else g[1][0]

    out = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            v1 = g[r][c]
            v2 = g[c][r] if (c < H and r < W) else 0
            if v1 == diag_val or v2 == diag_val:
                out[r][c] = diag_val
            elif v1 != 0:
                out[r][c] = v1
            elif v2 != 0:
                out[r][c] = v2
            else:
                if r == c:
                    out[r][c] = diag_val
                else:
                    out[r][c] = bg_val
    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    g = [row[:] for row in input_grid]

    diag_val = None
    for i in range(min(H, W)):
        if g[i][i] != 0:
            diag_val = g[i][i]
            break

    bg_val = g[0][1] if g[0][1] != 0 else g[1][0]

    out = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            v1 = g[r][c]
            v2 = g[c][r] if (c < H and r < W) else 0
            if v1 == diag_val or v2 == diag_val:
                out[r][c] = diag_val
            elif v1 != 0:
                out[r][c] = v1
            elif v2 != 0:
                out[r][c] = v2
            else:
                if r == c:
                    out[r][c] = diag_val
                else:
                    out[r][c] = bg_val
    return out
```

## `291dc1e1` [no_grid]

- Train shapes (in→out): [(20, 8, 12, 6), (8, 11, 8, 4), (8, 28, 14, 8), (8, 23, 14, 6)]
- Test shapes (in→out): (28, 8, 18, 8)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    from collections import deque
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]
    seen = [[False] * W for _ in range(H)]
    for i in range(H):
        for j in range(W):
            if input_grid[i][j] == 0 and not seen[i][j]:
                q = deque([(i, j)])
                seen[i][j] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and input_grid[ny][nx] == 0:
                                seen[ny][nx] = True
                                q.append((ny, nx))
                colors = list(set(input_grid[r][c] for r, c in cells))
                if len(colors) == 2:
                    a, b = colors[0], colors[1]
                    for r, c in cells:
                        out[r][c] = b if a == 6 else 6
    return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    def is_pocket(r, c):
        if r < 0 or r >= H or c < 0 or c >= W:
            return False
        if input_grid[r][c] != 0:
            return False
        above_is_6 = (r > 0 and input_grid[r-1][c] == 6)
        left_is_6 = (c > 0 and input_grid[r][c-1] == 6)
        right_is_6 = (c < W-1 and input_grid[r][c+1] == 6)
        return above_is_6 and left_is_6 and right_is_6

    sixes = [(r, c) for r in range(H) for c in range(W) if input_grid[r][c] == 6]

    for r, c in sixes:
        up = r - 1
        while up >= 0 and input_grid[up][c] == 8:
            up -= 1
        if up < 0 or input_grid[up][c] != 0:
            continue
        _, col = c, up
        if is_pocket(up, col):
            r = up
            while r < H and input_grid[r][col] == 0:
                input_grid[r][col] = 6
                r += 1

    for r, c in sixes:
        down = r + 1
        while down < H and input_grid[down][c] == 8:
            down += 1
        if down >= H or input_grid[down][c] != 0:
            continue
        _, col = c, down
        if is_pocket(col, down):
            c = down
            while c >= 0 and input_grid[c][col] == 0:
                input_grid[c][col] = 6
                c -= 1

    return grid
```

## `2ba387bc` [no_grid]

- Train shapes (in→out): [(23, 24, 16, 8), (20, 21, 12, 8), (20, 23, 8, 8), (22, 22, 12, 8)]
- Test shapes (in→out): (24, 19, 16, 8)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])

    visited = [[False] * W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = set()
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if visited[rr][cc]:
                        continue
                    if grid[rr][cc] != color:
                        continue
                    visited[rr][cc] = True
                    cells.add((rr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((rr + dr, cc + dc))
                components.append((color, cells))

    output = [[0] * W for _ in range(H)]

    shape_data = []
    for color, cells in components:
        if len(cells) < 6:
            continue
        reach = [[False] * W for _ in range(H)]
        q = deque()
        for r in range(H):
            for c in (0, W - 1):
                if (r, c) not in cells and not reach[r][c]:
                    reach[r][c] = True
                    q.append((r, c))
        for c in range(W):
            for r in (0, H - 1):
                if (r, c) not in cells and not reach[r][c]:
                    reach[r][c] = True
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and not reach[nr][nc] and (nr, nc) not in cells:
                    reach[nr][nc] = True
                    q.append((nr, nc))
        interior = set()
        for r in range(H):
            for c in range(W):
                if not reach[r][c] and (r, c) not in cells:
                    interior.add((r, c))
        shape_data.append((color, cells, interior))

    for color, border, interior in shape_data:
        for (r, c) in border:
            output[r][c] = color
        cnt = Counter()
        for (r, c) in interior:
            v = grid[r][c]
            if v != 0:
                cnt[v] += 1
        fill_color = 0
        if cnt:
            most = cnt.most_common()
            if most[0][1] >= 2:
                fill_color = most[0][0]
        for (r, c) in interior:
            output[r][c] = fill_color

    return output
```

### Attempt 1
```python
def solve(input_grid):
    grid = [row[:] for row in input_grid]
    H = len(grid)
    W = len(grid[0])

    visited = [[False] * W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                cells = set()
                while stack:
                    rr, cc = stack.pop()
                    if rr < 0 or rr >= H or cc < 0 or cc >= W:
                        continue
                    if visited[rr][cc]:
                        continue
                    if grid[rr][cc] != color:
                        continue
                    visited[rr][cc] = True
                    cells.add((rr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        stack.append((rr + dr, cc + dc))
                components.append((color, cells))

    output = [[0] * W for _ in range(H)]

    shape_data = []
    for color, cells in components:
        if len(cells) < 6:
            continue
        reach = [[False] * W for _ in range(H)]
        q = deque()
        for r in range(H):
            for c in (0, W - 1):
                if (r, c) not in cells and not reach[r][c]:
                    reach[r][c] = True
                    q.append((r, c))
        for c in range(W):
            for r in (0, H - 1):
                if (r, c) not in cells and not reach[r][c]:
                    reach[r][c] = True
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and not reach[nr][nc] and (nr, nc) not in cells:
                    reach[nr][nc] = True
                    q.append((nr, nc))
        interior = set()
        for r in range(H):
            for c in range(W):
                if not reach[r][c] and (r, c) not in cells:
                    interior.add((r, c))
        shape_data.append((color, cells, interior))

    for color, border, interior in shape_data:
        for (r, c) in border:
            output[r][c] = color
        cnt = Counter()
        for (r, c) in interior:
            v = grid[r][c]
            if v != 0:
                cnt[v] += 1
        fill_color = 0
        if cnt:
            most = cnt.most_common()
            if most[0][1] >= 2:
                fill_color = most[0][0]
        for (r, c) in interior:
            output[r][c] = fill_color

    return output
```

## `2d0172a1` [no_grid]

- Train shapes (in→out): [(20, 25, 11, 12), (20, 16, 5, 5), (20, 16, 7, 5), (20, 25, 9, 11)]
- Test shapes (in→out): (25, 25, 9, 13)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    g = [row[:] for row in input_grid]
    out = [row[:] for row in input_grid]

    counts = Counter()
    for r in range(H):
        for c in range(W):
            counts[g[r][c]] += 1
    bg = counts.most_common(1)[0][0]

    visited = [[False] * W for _ in range(H)]
    regions = []
    for r in range(H):
        for c in range(W):
            if g[r][c] != bg and not visited[r][c]:
                q = deque([(r, c)])
                visited[r][c] = True
                cells = []
                while q:
                    y, x = q.popleft()
                    cells.append((y, x))
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < H and 0 <= nx < W and not visited[ny][nx] and g[ny][nx] != bg:
                            visited[ny][nx] = True
                            q.append((ny, nx))
                regions.append(cells)

    for cells in regions:
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        colors = set()
        for (y, x) in cells:
            colors.add(g[y][x])
        n_colors = len(colors)
        if n_colors == 1:
            continue
        color = next(iter(colors))
        if n_colors == 2:
            for y in range(r0, r1 + 1):
                for x in range(c0, c1 + 1):
                    if g[y][x] != color:
                        out[y][x] = 4
        else:
            tr0, tr1 = sorted([r0, r1])[1], sorted([r0, r1])[1]
            tc0, tc1 = sorted([c0, c1])[1], sorted([c0, c1])[1]
            for y in range(tr0, tr1 + 1):
                for x in range(tc0, tc1 + 1):
                    out[y][x] = 4
    return out
```

### Attempt 1
```python
def solve(input_grid):
    h = len(input_grid)
    w = len(input_grid[0])
    n_cols = (w + 1) // 2
    color_map = {}
    for col in range(w):
        c = input_grid[0][col]
        if c != 0:
            color_map[col] = c

    perim = []
    for r in range(h):
        for c in range(w):
            v = input_grid[r][c]
            if v != 0:
                perim.append((r, c, v))

    col_to_perim = {}
    for r, c, v in perim:
        if c in color_map:
            col_to_perim[c] = col_to_perim.get(c, []) + [(r, c, v)]

    def find_separators(cells):
        cell_set = set(cells)
        n = len(cells)
        if n == 0:
            return []
        best = None
        best_score = -1
        for i in range(n):
            S1 = cells[:i+1]
            S2 = cells[i+1:]
            s1 = set(S1)
            s2 = set(S2)
            x = 0
            for j in S1:
                if j in s2:
                    x += 1
            y = 0
            for j in S2:
                if j in s1:
                    y += 1
            score = (x + y) / max(len(S1), len(S2))
            if score > best_score:
                best_score = score
                best = i
        return cells[:best+1]

    all_seps = []
    for col, vals in col_to_perim.items():
        cols = [c for r, c, v in vals]
        seps = find_separators(vals)
        all_seps.append((col, seps, cols.index(seps[-1]) if seps else 0))

    all_seps.sort(key=lambda x: x[0])

    template_col = all_seps[0][0]
    template_seps = all_seps[0][1]
    template_fixed_idx = all_seps[0][2]

    templates_by_seps = {}
    for col, seps, fixed_idx in all_seps:
        if len(seps) != len(template_seps):
            continue
        matched = True
        for i, tsep in enumerate(template_seps):
            if seps[i] != tsep:
                matched = False
                break
        if not matched:
            continue
        offset = fixed_idx - template_fixed_idx
        templates_by_seps[str(seps)] = (col, offset)

    output = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = input_grid[r][c]
            if v != 0:
                output[r][c] = v

    template_cells = [(r, c) for r, c, v in col_to_perim[template_col]]
    template_rows = sorted(set(r for r, c in template_cells))
    template_cols = sorted(set(c for r, c in template_cells))

    for template_pattern, (col, offset) in templates_by_seps.items():
        cells = [(r, c) for r, c, v in col_to_perim[col]]
        rows = sorted(set(r for r, c in cells))
        cols = sorted(set(c for r, c in cells))
        for i, trow in enumerate(rows):
            for j, tcol in enumerate(cols):
                val = input_grid[trow][tcol]
                nr = template_rows[i]
                nc = template_cols[j - offset]
                if 0 <= nr < h and 0 <= nc < w:
                    output[nr][nc] = val

    return output
```

## `38007db0` [no_grid]

- Train shapes (in→out): [(19, 19, 19, 7), (19, 25, 19, 7)]
- Test shapes (in→out): (29, 29, 29, 8)
- Shape-preserving: **NO (shape changes)**

### Attempt 0
```python
def solve(input_grid):
    from collections import Counter
    H = len(input_grid)
    W = len(input_grid[0])
    counts = Counter()
    for row in input_grid:
        for v in row:
            counts[v] += 1
    bg = counts.most_common(1)[0][0]

    colored = [(r, c, input_grid[r][c]) for r in range(H) for c in range(W) if input_grid[r][c] != bg]
    cols = [c for _, c, v in colored]
    left_col = min(cols)
    right_col = max(cols)

    colors = set(v for _, _, v in colored)
    def leftmost_color(val):
        return min(c for c in colored_if if c != bg and input_grid[c][left_col] == val)

    colored_if = [p for p in colored if p[1] != left_col and p[1] != right_col]
    interior_colors = set(v for _, _, v in colored_if)

    if not colored_if:
        return [row[:] for row in input_grid]

    top_color = min(colored, key=lambda p: p[0])

    if len(interior_colors) == 1:
        marker = next(iter(interior_colors))
        if top_color[1] == left_col:
            direction = 1
        else:
            direction = -1
        marker_row = None
        for r, c, v in colored:
            if v == marker:
                marker_row = r
                break
        if top_color[1] == left_col:
            triangle_rows = [r for r, c, v in colored if r > top_color[0] and c == left_col]
            if not triangle_rows:
                triangle_rows = [top_color[0] + 1]
            else:
                triangle_rows.append(triangle_rows[-1] + 1)
            start = triangle_rows[0]
            end = triangle_rows[-1]
            if end < top_color[0]:
                marker_row = end
            else:
                marker_row = start
        else:
            triangle_rows = [r for r, c, v in colored if r > top_color[0] and c == right_col]
            if not triangle_rows:
                triangle_rows = [top_color[0] + 1]
            else:
                triangle_rows.append(triangle_rows[-1] + 1)
            start = triangle_rows[0]
            end = triangle_rows[-1]
            if end < top_color[0]:
                marker_row = end
            else:
                marker_row = start
        out = [row[:] for row in input_grid]
        for r in range(top_color[0], marker_row + 1):
            out[r][top_color[1]] = top_color[2]
        if marker_row < top_color[0]:
            marker_pos = (marker_row, left_col)
        else:
            marker_pos = (marker_row, right_col)
        center_d = abs(marker_pos[1] - left_col) - 1
        triangle_rows_set = set(triangle_rows)
        if top_color[1] == left_col:
            for i in range(1, center_d + 1):
                if top_color[0] - i in triangle_rows_set:
                    r = top_color[0] - i
                    out[r][left_col] = top_color[2]
                else:
                    r = top_color[0] - i + 1
                    out[r][left_col] = marker
                if r <= marker_row:
                    out[r][left_col] = marker
        else:
            for i in range(1, center_d + 1):
                if top_color[0] - i in triangle_rows_set:
                    r = top_color[0] - i
                    out[r][right_col] = top_color[2]
                else:
                    r = top_color[0] - i + 1
                    out[r][right_col] = marker
                if r <= marker_row:
                    out[r][right_col] = marker
        return out
    else:
        if top_color[1] == left_col:
            direction = 1
        else:
            direction = -1
        marker = leftmost_color(top_color[2])
        marker_row = None
        for r, c, v in colored:
            if v == marker:
                marker_row = r
                break
        out = [row[:] for row in input_grid]
        for r, c, v in colored:
            if v == top_color[2]:
                if direction == 1:
                    new_r = 2 * H - 1 - r
                else:
                    new_r = 2 * H - 1 - r
                out[new_r][c] = v
        if marker_row is not None:
            for r in range(0, H):
                out[2 * H - 1 - r][left_col] = marker
        return out
```

### Attempt 1
```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    row_dom = []
    row_score = 0
    for r in range(H):
        c = Counter(input_grid[r])
        val, cnt = c.most_common(1)[0]
        row_dom.append(val)
        row_score += cnt

    col_dom = []
    col_score = 0
    for cc in range(W):
        c = Counter(input_grid[r][cc] for r in range(H))
        val, cnt = c.most_common(1)[0]
        col_dom.append(val)
        col_score += cnt

    if row_score >= col_score:
        return [[row_dom[r]] * W for r in range(H)]
    else:
        return [[col_dom[cc] for cc in range(W)] for _ in range(H)]
```

## `3a25b0d8` [no_grid]

- Train shapes (in→out): [(22, 22, 11, 11), (22, 22, 13, 7)]
- Test shapes (in→out): (30, 30, 18, 13)
- Shape-preserving: **NO (shape changes)**



