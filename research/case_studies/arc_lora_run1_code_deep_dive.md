# Deep-dive: Reading the LoRA's generated code

_Analysis of all available Python source from Run 1 attempts. Companion to [`arc_lora_run1_locked_eval.md`](./arc_lora_run1_locked_eval.md) and [`arc_lora_run1_code_samples.md`](./arc_lora_run1_code_samples.md)._

This document is the result of actually reading the model's source line by line on 18 of the 31 puzzles touched in Run 1. Not just bucket counts — what the LoRA is doing well, where it consistently breaks, and what the training data should change.

## TL;DR

1. **The model writes real ARC code.** It uses connected-component flood fill, background detection, bounding-box analysis, color counting, symmetry, geometric centroids. It is NOT shotgun-random output.
2. **It has one catastrophic blind spot: output shape.** Every shape-changing puzzle had code that initialized the output at *input* dimensions (`[[bg]*W for _ in range(H)]`) and returned it unchanged. The model never once considered that output rows/cols might differ from input.
3. **Many same-size near-misses are one tweak away.** Several 90%+ attempts have a single off-by-one or boundary-case bug visible by inspection.
4. **A small but real fraction of attempts have plain syntax/import bugs** that crash before any logic runs (missing `from collections import Counter`, undefined variables, etc).

## 1. The shape-change failure, with receipts

13/31 puzzles produced no valid grid on both attempts. Of those, 9 are puzzles where `output.shape != input.shape`. **In every single one of those 9, the model's code initializes the output at input dimensions.**

### `0934a4d8` (30×30 input → ~5×5 output expected)

Attempt 0:
```python
result = [[bg]*W for _ in range(H)]   # ← H,W are the INPUT dims (30×30)
# ... 50 lines of code mutating result ...
return result                          # ← still 30×30
```

Attempt 1:
```python
# ... no construction of an output grid at all ...
return input_grid                      # ← literally the input
```

### `136b0064` (15-cols input → 7-cols output expected)

Both attempts:
```python
out = [[0] * W for _ in range(H)]      # ← W is INPUT width (15), not 7
```

### `269e22fb` (variable input → fixed 20×20 output expected)

Both attempts:
```python
g = [row[:] for row in input_grid]
# ... iterates over min(H, W) for a "diagonal" pattern ...
out = [[0] * W for _ in range(H)]      # ← input dims, not 20×20
```

### `20270e3b`, `20a9e565`, `291dc1e1`, `2ba387bc`, `2d0172a1`, `38007db0`

All six: same pattern. Either `out = [row[:] for row in input_grid]` or `output = [[bg]*W for _ in range(H)]`. None of these even compute what the output shape should be.

### The model literally never wrote code like:

```python
# what we needed to see
H_out, W_out = compute_output_shape_from_training_pairs(train)
output = [[0] * W_out for _ in range(H_out)]
```

**This is the single highest-leverage training fix.** The model has no "compute output shape first" prior. It conflates "the grid" with "the input grid".

## 2. The model's real competencies

The same-size code is genuinely impressive. Recurring building blocks from the LoRA's vocabulary:

### Background detection (correct in nearly every attempt)
```python
cnt = Counter()
for r in range(H):
    for c in range(W):
        cnt[grid[r][c]] += 1
bg = cnt.most_common(1)[0][0]
```

### Connected-component flood fill (BFS or DFS, both common)
```python
visited = [[False]*W for _ in range(H)]
for r in range(H):
    for c in range(W):
        if grid[r][c] != bg and not visited[r][c]:
            q = deque([(r,c)]); visited[r][c] = True; comp = []
            while q:
                y, x = q.popleft()
                comp.append((y, x))
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < H and 0 <= nx < W and not visited[ny][nx] and grid[ny][nx] != bg:
                        visited[ny][nx] = True
                        q.append((ny, nx))
            components.append(comp)
```

### Bounding boxes, centroids, symmetry checks, color-multiset comparisons
All appear repeatedly and correctly.

### Sophisticated rule attempts
The 98.3% accuracy on `135a2760` came from code that:
- Finds components
- Classifies each component's "body" vs "marker" cells
- Computes marker direction from centroid offset
- Draws lines from each marker toward the edge in the right direction
- Repaints the bottom row by mapping `neutral → wild` colors

That's an ARC solver, not pattern matching.

## 3. Bug categories I found by inspection

### A. Missing imports (instant crash → `exec_error`)
Several attempts use `Counter`, `deque`, `defaultdict` etc without ever importing them. The LoRA seems to forget the import line ~10–20% of the time when the prompt context is long.

Examples:
- `13e47133` attempt 0: uses `deque` (no import) and references undefined `center_r`
- `247ef758` attempt 1: uses `Counter` (no import) inside `find_min_convex`
- `2d0172a1` attempt 0: uses `Counter` and `deque` (no import)
- `38007db0` attempt 1: uses `Counter` (no import)
- `20270e3b` attempt 1: uses `Counter` (no import)
- `20a9e565` attempt 1: uses `Counter`, `deque` (no import)
- `2ba387bc` attempts 0+1: uses `Counter`, `deque` (no import)
- `269e22fb`: actually correctly imports nothing because it doesn't use anything from collections — uses built-ins only — but this is rare

**Recommendation**: training data should always begin solve() bodies with the standard `from collections import Counter, deque` line. Or move imports to the top of the file. The phase-2 training records may have stripped these inconsistently.

### B. Malformed comprehensions / type errors
- `28a6681f` attempt 0: `set({(i,j) for ...} | {((y,x) for i in range(...))})` — generator OR'd with set, raises `TypeError`
- `2c181942` attempt 1: hardcodes `bg = 8` instead of computing it. Fragile — fails on any puzzle where bg is not 8.

### C. Variable scope / off-by-one
- `135a2760` attempt 0: the loop `for i, (r, c) in enumerate(ed['steps']): if i % 2 == 1: last_step_col = c` is checking parity in a way that misses every-other cell — that's where its 2-4% cell errors come from
- `1818057f` attempt 0: simple `out[r][W - 1 - c] = 8` mirror — works for some grids, fails on others where the mirror needs to preserve color rather than replace it
- `142ca369` attempt 0: thorough rectangle-detection algorithm, but the final "protrusion" handling has the inside/outside logic inverted

### D. Truncation-induced bugs
- `31f7f899` attempt 0: has a weird mid-dict literal `5: (0, 0), 7: (0, 1), 16: (1, 0), 26: (1, 1)...` — looks like the model was trying to map something but the keys are nonsense. Maybe a token boundary cut it off, maybe sampling drift. Either way the dict is broken.

## 4. Detailed read of the highest-performing attempt: `135a2760` (98.3%)

```python
def solve(input_grid):
    from collections import Counter
    H = len(input_grid); W = len(input_grid[0])
    grid = [row[:] for row in input_grid]

    cnt = Counter()
    for r in range(H):
        for c in range(W):
            cnt[grid[r][c]] += 1
    bg = cnt.most_common(1)[0][0]

    # 1. Find connected components of non-bg cells
    visited = [[False]*W for _ in range(H)]
    components = []
    for r in range(H):
        for c in range(W):
            if grid[r][c] != bg and not visited[r][c]:
                stack = [(r,c)]; comp = []
                while stack:
                    y, x = stack.pop()
                    if not (0 <= y < H and 0 <= x < W): continue
                    if visited[y][x] or grid[y][x] == bg: continue
                    visited[y][x] = True
                    comp.append((y, x))
                    stack.extend([(y+1,x),(y-1,x),(y,x+1),(y,x-1)])
                components.append(comp)

    # 2. Per component: identify "body" color and "marker" cell
    shapes = []
    for comp in components:
        colors = Counter(grid[y][x] for y, x in comp)
        body_color = colors.most_common(1)[0][0]
        markers = [(y, x) for y, x in comp if grid[y][x] != body_color]
        if not markers: continue
        my, mx = markers[0]
        marker_color = grid[my][mx]
        body = [(y, x) for y, x in comp if grid[y][x] == body_color]
        cy = sum(y for y, x in body) / len(body)
        cx = sum(x for y, x in body) / len(body)
        dy = my - cy; dx = mx - cx
        if abs(dy) > abs(dx):
            direction = 'up' if dy < 0 else 'down'
        else:
            direction = 'left' if dx < 0 else 'right'
        shapes.append({'marker_pos':(my,mx), 'marker_color':marker_color, 'direction':direction})

    # 3. For each marker, trace toward the grid edge and record what's hit
    edge_directions = []
    for shape in shapes:
        # ... 30 lines of per-direction stepping logic ...

    # 4. Draw lines from markers; repaint bottom row using neutral/wild logic
    for ed in edge_directions:
        # ... applies the rule ...
```

This is a five-step pipeline (components → body/marker → direction → trace → repaint). The 1.7% cell error rate is from the parity bug in step 3's step-tracking loop.

A human reviewer with the puzzle in front of them could fix this code in minutes. Which is exactly what the phase-3 corrector task is designed for.

## 5. Concrete recommended changes for the next training run

Listed roughly in order of expected impact:

### High impact

1. **Shape-aware phase-2 records.** Add explicit reasoning about output dimensions to the assistant message for any puzzle where `output.shape != input.shape`. Something like:
   ```python
   def solve(input_grid):
       H, W = len(input_grid), len(input_grid[0])
       # output shape: 7 rows, 7 cols (consistent across all training pairs)
       output = [[0]*7 for _ in range(7)]
       ...
   ```
   This is the highest-leverage single change. Roughly 30% of the locked eval is shape-changing.

2. **Always-on imports.** Standardize the first non-def lines of every phase-2 assistant body:
   ```python
   def solve(input_grid):
       from collections import Counter, deque
       H, W = len(input_grid), len(input_grid[0])
   ```
   Reduces the 10–20% no-import crash rate to near zero.

3. **Dynamic background detection.** Penalize hardcoded values like `bg = 8` or `border_color = grid[0][0]` in training data. The model is copying these from specific training examples and they don't transfer.

### Medium impact

4. **Self-check before return.** Train phase-2 assistant bodies to end with:
   ```python
   # sanity: output is a 2D list of ints
   assert isinstance(output, list) and all(isinstance(r, list) for r in output)
   return output
   ```
   Catches the `return None` / `return input_grid` failure modes earlier.

5. **Phase-3 corrector on the near-misses.** Run the 7 ≥90% outputs through the phase-3 task with feedback like:
   - "Output shape correct. Cells wrong at: (r0,c5)=2 (expected 4), (r3,c12)=8 (expected 0). The rule may have an off-by-one in iteration."
   
   If even half of the near-misses convert to wins, that's +3–4 puzzles on the locked eval.

### Lower impact

6. **More diverse rule categories.** The recurring use of "connected components + body/marker classification" feels overfit to the phase-1 substrate task. Puzzles where the rule is geometric (rotation, reflection, scaling) get treated with the component-finding hammer.

7. **Temperature**: don't lower below 0.7. Run 2 disconfirmed that lowering helps. If anything, try 1.0 with 5+ attempts and pass@k aggregation.

## 6. What you don't yet know (open questions for the next run)

- Does the same-size near-miss rate stay this high on the rest of the 89 untouched puzzles in the locked eval? Or did Run 1 happen to hit the easy 31 alphabetically first?
- What does pass@10 look like? The 7 near-misses may flip with more samples.
- Does the base Qwen-2.5-7B-Instruct (no LoRA) produce *any* near-misses on the same set, or just garbage? That establishes the LoRA's marginal contribution.

These would be the next three things to measure.
