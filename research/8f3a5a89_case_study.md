# 8f3a5a89 — Fine Tuning Notes

**Source:** https://arcprize.org/tasks/8f3a5a89
**Canonical solver:** [`Solvers/seeded_reachable_wall_contouring.py`](../Solvers/seeded_reachable_wall_contouring.py)

## Canonical rule

Starting from the unique 6 marker, flood-fill through the background while
treating only edge-touching 1-clusters as barriers. Draw the exposed boundary
of that reachable region in 7. Preserve the 6 marker and any 1-clusters that
touch or lie inside the reachable region; remove all others.

Three wall categories (implicit in the edge-barrier framing):
1. **Edge-touching walls** that bound the reachable region → barriers; halo
   forms against them
2. **Interior walls** surrounded by the reachable region → preserved as walls,
   no halo around them
3. **Unreachable walls** not adjacent to the reachable region → removed

## Per-model arc

| Model | Iters | Final result | Notes |
|---|---|---|---|
| GPT     | 2 | SUBMIT (3/3 + test) | Iter 1: 2/3 (false-positive on test). Iter 2: realised internal walls aren't barriers → SUBMIT |
| Gemini  | 5 | SUBMIT (3/3 + test) | Stepwise: perimeter frame → flood-fill → cluster pruning → edge/interior split |
| Grok    | 3 | SUBMIT (3/3 + test) | Iter 1: hardcoded test grid (0/3). Iter 2: BFS but 4-conn halo (1/3). Iter 3: 8-conn + edge-touching halo trigger (3/3) |
| Opus 4.7 (TIPS+lockdown) | 2 | SUBMIT (3/3 + test) | Iter 1: BFS from anchor on first try (2/3). Iter 2: added edge-touching distinction → SUBMIT. **Same model went 7+ iters without TIPS** |
| Sonnet 4.6 (TIPS+lockdown) | 6+ stuck | 0/3 (regression at iter 6) | Got 8-conn fix at iter 5 (2/3), then over-extended the "interior cluster doesn't halo" rule to ALL kept 1s — broke the structural wall halo on Pair 1 |

## Failure modes observed

Grouped by category. The same modes are likely to repeat on other puzzles.

### A. Output-format anti-patterns (the model isn't even producing the right kind of artefact)

- **A1. Hardcoded test output as literal grid**
  - Seen in: Grok narrative, Gemini iter 3 narrative, Opus iter 1 (no-TIPS run), Sonnet iter 1 (no-TIPS run)
  - Looks correct on test, fails 0/N on training (training grids have different shapes)
  - The training validator catches it deterministically
  - **Mitigation:** v6+ substrate prompt + feedback's `WHAT TO DO NEXT` block both forbid this explicitly

- **A2. No code at all (only prose / pseudocode)**
  - Seen in: Gemini after first feedback
  - Validator can't run anything → no useful signal back to the model
  - **Mitigation:** v6+ prompt + feedback `MUST contain def solve(input_grid):` warning

- **A3. Hardcoded dimensions / row indices / col indices in code**
  - Seen in: Grok iter 1 (`wall_col = 10`), Opus pre-TIPS run iter 1
  - Code runs but only on grids matching the test shape; all training pairs fail
  - **Mitigation:** v6+ prompt explicitly says "do not hardcode dimensions, row indices, or column indices"

### B. Algorithmic anti-patterns (model produces code, but the wrong algorithm)

- **B1. Generic perimeter framing** (default ARC bias)
  - Seen in: Gemini iter 1-2, Opus pre-TIPS
  - Draws a 7-frame around the whole grid, ignoring the seed entirely
  - Likely a learned shortcut from common ARC training puzzles
  - **What unlocked the fix:** mechanistic feedback's structural cluster analysis
    showed expected output had 1 cluster of 7s of specific shape, not a perimeter ring
  - **TIPS unlock:** "Many ARC rules radiate outward from an anchor (BFS, flood-fill)"
    nudged Opus and Sonnet to BFS from seed on iter 1

- **B2. Per-cell reasoning when per-component is needed**
  - Seen in: Gemini iter 4 (pruned individual 1-cells of a wall component instead
    of treating the whole wall as one unit)
  - Pruning interior cells of the staircase broke pair 3
  - **What unlocked the fix:** transformation grid mismatch list pointed precisely
    at the cells that should have been preserved as `=` but became `-`

- **B3. Halo around all walls instead of edge-touching only**
  - Seen in: Gemini iter 3-4, Opus iter 1, Sonnet iter 1-5 (4-conn variant)
  - Doesn't distinguish structural barriers from internal obstacles
  - **What unlocked the fix:** mechanistic feedback's cluster classification
    explicitly labels each cluster as `EDGE-TOUCHING` or `INTERNAL` — the
    LLM picked up that vocabulary in fix iter ("edge_touching_wall_mask")

- **B4. Missing the third wall category (unreachable walls → removed)**
  - Seen in: Original solver code from Grok+GPT (yesterday, before validator caught it)
  - Code preserved all walls touching the reachable region; expected output
    *removed* unreachable walls entirely
  - **What unlocked the fix:** training-3/3 gate caught it; the operation
    diagnosis showed `1 -> 8: 28 cells` in expected vs `0 cells` in your output

- **B5. 4-connectivity halo where 8-connectivity needed** (recurring)
  - Seen in: Sonnet iter 1-4
  - Halo only triggered for cardinal neighbors of walls; diagonal-positioned
    halo cells in expected output were missed (cells like (3,1) when the wall
    is at (4,0))
  - **What unlocked the fix:** TIPS hint `When checking adjacency, consider whether
    the rule includes diagonals (8-connectivity) or only cardinal neighbors
    (4-connectivity)` — Sonnet immediately diagnosed and fixed it
  - **Generic principle:** ARC rules often use 8-conn for halo/expansion even
    though 4-conn is the typical default in flood-fill code

- **B6. Over-extending a scoped fix to a global rule** ⚠ NEW
  - Seen in: Sonnet iter 6 (regression)
  - Mechanistic feedback identified ONE cluster as `INTERNAL` (rows 9-11, cols
    9-10 in Pair 3); fix should have been "if cluster is INTERNAL, no halo"
  - Sonnet rewrote the boundary rule globally: "kept 1s don't trigger boundary"
  - This broke Pair 1's structural col-6 wall (also a kept 1, but EDGE-TOUCHING,
    so it SHOULD trigger halo) → regression from 2/3 to 0/3
  - **Pattern:** smaller models conflate "specific subset" with "all members of
    larger category." When mechanistic feedback distinguishes types, the fix
    must preserve the type distinction in code.

### C. False positives (test passes but training fails — lucky guess)

- **C1. Code happens to produce correct test output despite incomplete rule**
  - Seen in: GPT iter 1, Opus iter 1 (the test happens to match canonical
    output even with the `INTERNAL`-halo bug because test has no internal
    clusters), hand-computed grids from Gemini and Grok
  - The test case lacks the configuration that exposes the bug
  - **Mitigation:** training-3/3 submit gate is the only deterministic catch

### D. Drift / regression patterns ⚠ NEW SECTION

- **D1. Anchor block ignored — full rewrite breaks passing pairs**
  - Seen in: Sonnet iter 6 (had explicit `PAIR 1 - PASSING` and `PAIR 2 - PASSING`
    anchor blocks in iter 5 feedback, regressed at iter 6 anyway)
  - Smaller models read the diagnostic for the failing pair, then refactor the
    boundary check globally instead of adding a scoped condition
  - **Mitigation candidate:** stronger language in PASSING blocks (e.g. "the
    exact lines of code producing this output must remain unchanged"); model-
    size-aware feedback intensity; or output-diff-aware feedback that flags
    "you changed line X which was the boundary check that produced PAIR 1's
    correct output"

- **D2. Identical-code resubmission with reworded reasoning**
  - Seen in: Sonnet iter 4 (sent character-for-character identical code to iter 3
    with different prose)
  - Model interprets feedback as "reword your explanation" rather than "change
    your code"
  - **Mitigation candidate:** validator should detect identical code and fail
    with a stronger instruction ("your code is unchanged from iter N — modify
    the algorithm, not the prose")

## What unlocked the fix (per signal)

Which substrate framework feature contributed most to each model's convergence:

| Signal | Gemini | GPT | Grok | Opus 4.7 (TIPS) | Sonnet 4.6 (TIPS) |
|---|---|---|---|---|---|
| Side-by-side grid comparison | localised | — | — | — | — |
| Diff map (X = error) | visual locator | — | — | — | localised diagonals (B5) |
| Transformation grid (`. = + - ~`) | iter 4 → 5 unlock | iter 1 → 2 unlock | — | — | — |
| Mechanistic cluster classification (`EDGE-TOUCHING` / `INTERNAL`) | **iter 5 unlock** | vocab in iter 2 | iter 3 unlock | iter 2 unlock | iter 6 input (over-extended) |
| Operation diagnosis (`1 -> 8: 28 cells`) | missing-op signal | iter 1 → 2 | — | — | — |
| Test self-inspection block | what would submit | flagged iter 1 lucky | — | — | — |
| **Lock-down PASSING anchor blocks** | **iter 4 → 5 stability** | n/a (single iter) | held across iters | **held all iters** | **failed at iter 6** ⚠ |
| Iteration history table | self-arc context | — | — | — | — |
| `UPDATE YOUR PYTHON` language | stopped no-code mode | — | — | — | — |
| **TIPS: anchor cells + flood-fill** | n/a (pre-TIPS) | n/a | n/a | **iter 1 unlock** | **iter 1 unlock** |
| **TIPS: 4-conn vs 8-conn** | n/a | n/a | n/a | (already used 8-conn) | **iter 5 unlock** |

## Fine-tuning takeaways

### Anti-patterns to penalise heavily during fine-tuning

1. **Returning a literal grid as the function body** (response `return [[7,7,...], ...]` with no loops, no `input_grid` references)
2. **Hardcoded dimensions or indices** (any `== 10`, `[0:12]`, etc. that depends on a specific grid shape)
3. **Drawing perimeter frames as default behaviour** (the model's first instinct shouldn't be to ring the grid edge unless evidence says so)
4. **Per-cell processing of color-1 regions when component-level is needed** (model should default to BFS/connected-components)
5. **No-code responses** (description without `def solve`)
6. **Resubmitting unchanged code with new prose** — code must change between iters when feedback is non-trivial
7. **Over-extending a scoped fix to a global rule** ⚠ — when feedback distinguishes a subset (e.g. INTERNAL vs EDGE-TOUCHING), the fix must be a CONDITION on that subset, not a rewrite of the parent rule
8. **Breaking passing-pair behavior while fixing failing-pair** — anchor blocks must be respected; previous logic stays intact, new logic is ADDITIVE not REPLACEMENT

### Pro-patterns to reinforce

1. **Always locate the seed first** if the puzzle has a unique marker color
2. **Classify connected components** before deciding what to do with them
3. **Use the substrate symbol vocabulary** (`+ = - . ~`) when describing what the rule does
4. **Distinguish edge-touching vs interior** for any structural element — these often have different roles
5. **Apply the rule, don't enumerate the answer** — the function must be a transformation, not a lookup
6. **8-connectivity for halos** (cardinal + diagonal) — default to 8-conn for adjacency checks unless evidence points to 4-conn
7. **Scoped fixes** — when adding a new condition, scope it to the specific subset the feedback identified (`if cluster.is_internal:`), don't refactor the parent rule
8. **Anchor preservation** — when feedback shows PASSING blocks, the code path producing those outputs must remain functionally identical

### Substrate vocabulary the fine-tuned model should know

- `seed`, `marker`, `anchor` — the unique starting point
- `reachable region`, `active room`, `connected component` — what the flood produces
- `edge-touching cluster` vs `interior cluster` — the key distinction this puzzle needs
- `barrier`, `wall`, `obstacle` — cells that block the flood
- `contour`, `halo`, `boundary trace` — the 7 painting around the region
- `prune`, `remove unreachable` — cleanup of disconnected structures
- `4-connectivity` (cardinal) vs `8-connectivity` (cardinal + diagonal)
- `scoped predicate` (subset condition) vs `global rule` (rewrite of parent rule)
- Substrate symbols: `.` background unchanged, `=` colored unchanged, `+` activated, `-` deactivated, `~` recolored

### Training data composition hint (specific to this puzzle's lessons)

When building fine-tuning data, include examples where:
- Wall components have varying connectivity to the seed (forces the model to learn the 3-category split)
- Test grids deliberately omit certain configurations present in training (forces the model to generalise rather than memorise)
- Multiple valid framings exist (edge-barrier vs 3-category) — reward conciseness when both produce the same correct output
- **Iter N had passing pair, iter N+1 broke it via global rewrite** — show the diff and label it as anti-pattern; the correct fix is a scoped predicate
- **8-conn vs 4-conn switch** — show puzzles where the only difference between 1/3 and 3/3 is the connectivity choice for halo

## Cross-model size signal

| Model | Iters with TIPS+lockdown | Anchor-block respected? |
|---|---|---|
| Opus 4.7 | 2 | ✅ all iters |
| Sonnet 4.6 | 6+ | ❌ broke at iter 6 (over-extended fix) |

**Implication for smaller models:** the anchor-block format alone won't keep
weaker models from regressing. Likely needs:
- Stronger language ("THE EXACT LINES PRODUCING THIS OUTPUT MUST REMAIN UNCHANGED")
- Or a code-diff feedback layer ("you modified line X — that line produced
  PAIR 1's correct output")
- Or model-size-aware feedback intensity (more verbose anchor preservation
  for smaller models)

This is the canonical case study for "lock-down format necessary but not
sufficient" — important for the fine-tuning data to teach scoping discipline.
