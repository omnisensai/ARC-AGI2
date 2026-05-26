# Canonical latent-T solver — agent brief

You are generating ONE verified canonical ARC solver for a distillation corpus.

Your puzzle id and its data file are given in your task message. The data file
(`research/canonical_solvers/_tasks/<pid>.json`) is JSON:
`{"puzzle_id","train":[{"input","output"}...],"test":[{"input","output"}...]}`,
grids are `list[list[int]]` colors 0-9. **Same-size** puzzle (output dims ==
input dims). For corpus building you may use **ALL** pairs (train AND test) as
evidence — the goal is the best canonical solver, not Kaggle inference.

## Goal
Write `def solve(input_grid):` that reproduces the output for EVERY pair EXACTLY,
in CANONICAL latent-T form:

    def solve(input_grid):
        T = infer_T(input_grid)        # infer a transformation MASK from input structure
        return apply_T(input_grid, T)  # copy input, overwrite only masked cells

`T` is a latent mask: a 2D None/int grid, OR a dict `{(r,c): new_color}`, OR a
set of changed cells + color rule, OR a boundary/fill/repair mask. `infer_T`
computes it from `input_grid` ALONE (objects, connected components, flood-fill,
symmetry, markers, repetition, consensus templates, ray/line tracing, etc.).
`apply_T` copies the input and overwrites only the masked cells.

## Hard rules (your solver will be AST-audited and rejected otherwise)
- Must contain the `infer_T`/`apply_T` decomposition — the mask must be explicit.
- NO hardcoded grids, NO `if input_grid == [...]`, NO fingerprint/lookup over
  whole grids or block-position sets, NO giant literal output. Must read input.
- Same-size output (dims == input). Standard library only.

## Exemplar of the required shape (marker/region/boundary rule)
```python
def solve(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    out = [row[:] for row in input_grid]
    counts = {}
    for row in input_grid:
        for v in row: counts[v] = counts.get(v,0)+1
    bg = max(counts, key=counts.get)
    start = next(((r,c) for r in range(H) for c in range(W) if input_grid[r][c]==6), None)
    if start is None: return out
    reachable, stack = set(), [start]
    while stack:
        r,c = stack.pop()
        if (r,c) in reachable or not (0<=r<H and 0<=c<W): continue
        if input_grid[r][c] not in (bg,6): continue
        reachable.add((r,c))
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)): stack.append((r+dr,c+dc))
    T = [[None]*W for _ in range(H)]            # latent transformation mask
    for r,c in reachable:
        if input_grid[r][c]!=bg: continue
        if any(not(0<=r+dr<H and 0<=c+dc<W) or (r+dr,c+dc) not in reachable
               for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0)):
            T[r][c] = 7
    for r in range(H):
        for c in range(W):
            if T[r][c] is not None: out[r][c]=T[r][c]
    return out
```

## Process (verify — do not trust yourself)
1. Read the task JSON.
2. Study ALL pairs; infer the single transformation rule.
3. Write `solve()` in canonical `infer_T`/`apply_T` form.
4. Write a test harness: run `solve(input)` for every pair, compare exactly,
   print PASS/FAIL per pair. Run it.
5. On any fail, inspect the diff, fix `infer_T`, re-run. Iterate until ALL pass.
6. When ALL pass, write the final solver (solve + helpers, NO test harness) to
   `research/canonical_solvers/solvers/<pid>.py`. Put any scratch/test files in
   `/tmp`, NOT in the repo.

## Report back (concise)
ALL-PASS or not, number of iterations, the rule, and paste the final `solve()`.
If you genuinely cannot pass all pairs after honest effort, say so, paste your
best attempt, and list which pairs fail and why. **Do not fake success or
hardcode** — the orchestrator re-runs your code against all pairs independently.
