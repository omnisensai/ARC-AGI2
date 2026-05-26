# Phase 2 V2 — Stage Prompts & Curriculum

Companion to `Phase2_V2.md`. That doc says *why* we train latent-T generators.
This doc is the *how*: the exact prompts, the curriculum order, the pair-cycling
that hammers in code-invariance, and the strategy for micro-primitives and
not-same-size puzzles.

Prompts here reuse the **Phase-1 substrate serialization byte-for-byte** (see
`Fine Tune Run 2/phase1_prompts.py` + `PROMPTS.md`). That is deliberate: the
model is already fluent at reading `INPUT`/`T` in this format. Phase 2 V2 only
changes the *target* — from "emit the next T/OUTPUT" to "emit the code that
generates T."

---

## 0. The one-line thesis

> The puzzle instance is the variable. **The code is the invariant.**
> Train: *these (cycled, varied) pairs → THIS code.* Thousands of times.

We never ask the model to guess an output grid. We ask it to write a `solve`
whose `infer_T` reproduces the **diffs we can actually see**. Supervision and
grading are defined entirely by the visible pairs — the held-out test pair is
never needed to build a training example, and is never leaked into one. It is
only ever the generalization check.

The danger this guards against (Phase 2 V1's failure): "guess the output" is a
search over all possible grids. "Write the diff map + the Python that produces
the seen outputs" is a search over *rules*, and Python does the mechanics once
the rule is named.

---

## 1. Curriculum philosophy

Three rules, applied at every stage:

1. **Start easy, ramp difficulty.** Order tasks by a computable difficulty
   score (§6). Early stages: tiny grids, single mechanism, short code. Late
   stages: simulation, multi-step rules, long code.

2. **Cycle pairs at every step.** For one verified solver, emit *many* records
   that vary which train pairs are shown, in what order (and, gated, under color
   permutation). **The target code is identical across all of them.** This is
   the invariance hammer: the model sees "puzzle-shaped-thing A → CODE", "subset
   B of the same pairs → the same CODE", "reordered C → the same CODE" … and
   latently learns that the code is keyed to the *rule*, not to any particular
   set of grids.

3. **The code is invariant; the instance is not.** Micro-primitives make this
   explicit — one generator code, hundreds of parameter instances, all mapping
   to that one code. Real puzzles make it concrete. Both teach the same lesson.

Why this works: a model that has seen 50 distinct (visible-pairs → same code)
rotations for a task can no longer treat the mapping as "memorize these grids."
The only stable thing across the rotations is the rule, expressed as code.

---

## 2. Substrate format (reused from Phase 1 — do not change)

**Grid** — rows separated by `\n`, each row is digits with no separator:

```
INPUT:
0007000
0070700
0007000
```

**Same-size T** — per-cell, lossless. `.` = cell unchanged, `0-9` = cell
overwritten with that color. Same dimensions as INPUT:

```
T:
.......
..8.8..
.......
```

**Diff-size T** — aggregate, lossy (cannot rebuild OUTPUT from INPUT alone).
`SIZE / BG / PALETTE / ROWS / COLS / BBOX` summary with relation tags
(`= ×N ÷N Δ±N new dropped`). See `phase1_prompts.py:_FACTS_LEGEND_BODY`.

The same-size/diff-size split is already a first-class Phase-1 concept, which is
exactly why we treat them as two tracks below.

---

## 3. The canonical contract

### 3a. Same-size track (the spine — all 739 corpus solvers)

```python
def solve(input_grid):
    T = infer_T(input_grid)        # read structure, return the change map
    return apply_T(input_grid, T)  # copy input, overwrite only T's cells
```

Invariant: *cell not selected by T → keep input cell; cell selected → overwrite.*
T may be a dict `{(r,c): color}`, a 2D `None`/int grid, or a set + value logic.
Acceptance/breakage rules are enforced by `scripts/validate_canonical.py`
(runs the solver vs ground truth on every pair + AST hardcoding audit).

Because same-size T is **lossless**, the USER turn shows `INPUT` + `T` only —
OUTPUT is redundant and omitting it keeps T as the interface.

### 3b. Diff-size track (separate contract — NO corpus yet)

When OUTPUT dimensions ≠ INPUT, you cannot overwrite a copy of the input. The
contract extends to *construct a canvas, then paint*:

```python
def solve(input_grid):
    T = infer_T(input_grid)        # T carries: output (h, w) + how to fill it
    return apply_T(input_grid, T)  # build a fresh h×w grid, fill from T

def apply_T(input_grid, T):
    out = [[T["bg"]] * T["w"] for _ in range(T["h"])]
    for (r, c), v in T["cells"].items():     # or: out[r][c] = input_grid[sr][sc]
        out[r][c] = v
    return out
```

The model must infer **geometry** (crop / tile / scale / extract / concat) *and*
**content**. Because diff-size T is lossy, the USER turn shows `INPUT`, `OUTPUT`,
**and** the aggregate T-facts (the model needs OUTPUT to learn geometry).

> Status: the current corpus is **739/739 same-size**. Diff-size needs its own
> verified corpus before it can be trained — see §7.

---

## 4. Stage prompts

These are the literal `system` / `user` strings. (When wired, mirror them into a
`phase2_prompts.py` source-of-truth with a doc-sync check, exactly like
`phase1_prompts.py` ↔ `PROMPTS.md`.) The `assistant` target is always the
**verified canonical solver** for that puzzle, code only, no prose.

### 4a. SAME-size code — system prompt

**System prompt:**
```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
Each T encodes exactly one transformation rule that applies across all pairs.

When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless — OUTPUT can be rebuilt exactly from INPUT via T.

T encoding (per cell [r,c]):
  .       INPUT -> OUTPUT cell unchanged
  0-9     INPUT -> OUTPUT cell changed to this color

Task:
Each pair below is shown as INPUT and its T. The same rule produced every T. Write Python that regenerates T for any input of this task, then applies it:

    def solve(input_grid):
        T = infer_T(input_grid)
        return apply_T(input_grid, T)

infer_T reads structure from input_grid alone and returns the latent change map. apply_T copies the input and overwrites only the cells T selects; unselected cells are kept. Infer the rule from the pairs. Do not hardcode a grid, do not compare against a known input, do not look up an output. Return only the code.
```

### 4b. Variant A — all train pairs (max evidence)

**User turn:**
```
PAIR 1:
INPUT:
<grid_to_str(input_1)>
T:
<per_cell_T(input_1, output_1)>

PAIR 2:
INPUT:
<grid_to_str(input_2)>
T:
<per_cell_T(input_2, output_2)>

... (all train pairs) ...

Write def solve(input_grid).
```

### 4c. Variant B / C — 3-pair / 2-pair cycle (fewer-evidence robustness)

Identical to Variant A but show only a *subset* of 3 (B) or 2 (C) train pairs.
Requires ≥3 / ≥2 train pairs respectively. **Same target code.** This is the
core invariance hammer.

### 4d. Variant D — competition-shaped (matches real inference)

**User turn:**
```
PAIR 1:
INPUT:
<grid_to_str(input_1)>
T:
<per_cell_T(input_1, output_1)>

... (all train pairs as INPUT + T) ...

TEST INPUT:
<grid_to_str(test_input)>

Write def solve(input_grid).
```

No test T, no test output. **Same target code.**

### 4e. Variant E — upper-bound diagnostic (NOT in main training)

Train pairs + the *solved* test INPUT/T shown. Diagnostic only — measures
whether all-evidence prompts make generation easier. Never mixed into main
training (it leaks test-derived T).

### 4f. DIFF-size code — system prompt

**System prompt:**
```
Transformation dynamics:
T encodes how the INPUT grid becomes the OUTPUT grid.
Each T encodes exactly one transformation rule that applies across all pairs.

When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy — OUTPUT cannot be rebuilt exactly from INPUT via T.

T encoding (aggregate summary):
  SIZE     H x W -> h x w   with relation tags
  BG       in_bg -> out_bg   with relation tag
  PALETTE  per-color count change
  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)
  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)
  BBOX     per-color bounding box (INPUT and OUTPUT)

Task:
The output grid has DIFFERENT dimensions from the input. Write Python that infers the output geometry and content from the input and constructs the output:

    def solve(input_grid):
        T = infer_T(input_grid)        # output (h, w) + how to fill it
        return apply_T(input_grid, T)  # build a fresh h x w grid, fill from T

Because T is lossy here, each pair is shown as INPUT, OUTPUT, and T-facts. Derive the geometry rule (crop / tile / scale / extract / concat) and the content rule from the pairs. Do not hardcode an output grid. Return only the code.
```

**User turn** shows `INPUT`, `OUTPUT`, `T:` (facts) per pair, then `Write def solve(input_grid).`

### 4g. apply_T mechanics warm-up (Stage M0, optional)

**User turn:** one INPUT + an explicit T (dict or 2D), ask for `apply_T` or the
resulting OUTPUT. Teaches the keep/overwrite primitive in code before any
inference. Tiny; a few hundred records.

### 4h. Repair stage — system + user (Stage X)

**System prompt** (delta from 4a): "You are given the pairs, a WRONG solver, and
the validator's failure diff. Return a corrected canonical solver. Code only."

**User turn:**
```
PAIR 1:
INPUT:
<...>
T:
<...>
... (pairs) ...

WRONG CODE:
<candidate solver>

VALIDATOR FAILURE:
failed pair: 2
(r,c): expected X, got Y
...

Return corrected code only.
```

---

## 5. Pair-cycling & augmentation

### 5a. Always-safe (no re-validation needed)

**Pair subset + ordering.** The target code is unchanged when you show a
different subset of the train pairs or reorder them. With `n` train pairs you
get `Σ_{k=2..n} C(n,k)` subset choices × orderings — plenty even at `n=3..4`
(corpus median train pairs ≈ 3). Cap per solver to avoid drowning (see mix
below). This is the primary invariance signal and is free.

### 5b. Re-validation-gated (expands data, must be checked)

**Color permutation** and **dihedral (rotate/flip)** of the whole puzzle produce
a *different* (INPUT, T) but should keep the *same* code — **only if** the
solver is equivariant. Many corpus solvers derive colors/geometry from
structure and are equivariant; some encode a color constant that *is* the rule
(consensus templates) and would break. **Rule:** apply the augmentation, re-run
`validate_canonical.py` against the SAME solver; keep the variant only if it
still passes. Never assume equivariance.

### 5c. Mix per solver per stage (from `Phase2_V2.md` §5.5)

```
50%  Variant A (all train pairs)
20%  Variant B (3-pair cycle)     [if ≥3 train pairs]
15%  Variant C (2-pair cycle)     [if ≥2 train pairs]
15%  Variant D (competition-shaped)
```

Target ~6–10 cycled records per solver in the same-size real stages.

---

## 6. Difficulty ordering (computable)

Score each task to order the curriculum. Grounded in corpus stats
(739 same-size; max-dim median 16, p90 29; solver LOC median 60, p90 107):

```
difficulty(task) = z(solver_LOC) + z(max_grid_dim) + 0.5·z(num_change_regions)
```

Bucket into 5 tiers by **solver-LOC quintile** (primary proxy for rule
complexity), tie-broken by grid dim:

```
T1 easiest   LOC ≤ 39      (~148 solvers)   recolor / keep-overwrite, small grids
T2           40–53                          single-pass masks, simple geometry
T3           54–68                          components / rays / fills
T4           69–90                          multi-step, symmetry repair
T5 hardest   LOC > 90      (~148 solvers)   simulation, BFS, mirror-lattice, etc.
```

---

## 7. Micro-primitive strategy

Micro-primitives are the **purest invariance lesson**: one generator code,
hundreds of parameterized instances → that one code. They also install the
reusable `infer_T` operators the real solvers compose.

- **Each family is a parameterized generator** producing
  `(INPUT, OUTPUT, T, canonical_solver)`. The solver code is **fixed per family**;
  parameters vary grid size, colors, marker position, orientation, distractors,
  background, and the number of generated pairs.
- **Every micro solver passes the same gate** (`validate_canonical.py` style:
  runs vs ground truth on all generated pairs + AST audit). Reject any micro
  solver that builds the output directly without an explicit T/mask.
- **Same prompts as real** (§4a–4d) — micro is just an easy data *source*, same
  contract, same format, same cycling.

Families (from `Phase2_V2.md` §6.3), grouped by difficulty:

```
Easy  (Stage M1):  ray_to_edge · complete_line · fill_enclosed · component_recolor
Med   (Stage M2):  ray_until_blocker · u_cup_fill · boundary_mask · mirror
Hard  (Stage M3):  periodic_extension · periodic_repair · gravity_water · rotate_translate
```

Counts: start 100–300 records/family (~2.7k total), evaluate, scale to 500–2000
later. Generate diff-size micro variants too (e.g. crop-to-bbox, tile k×) once
the diff-size track opens (§3b/§8).

---

## 8. Master learning order

One pass, monotonic difficulty, cycling at every stage. (Maps to the Run
schedule in `Phase2_V2.md` §8; adapter chain starts from the golden
`phase1_same_lit`.)

```
Stage   Source / content                              Difficulty   Cycling
-----   -------------------------------------------   ----------   -------------------
M0      apply_T mechanics (INPUT+T -> code/output)    trivial      light
M1      easy micro families                           T1           subset+order
M2      med micro families                            T2           subset+order (+ gated color-perm)
R1      real same-size solvers, tier T1–T2            T1–T2         full mix (§5c)
R2      real same-size solvers, tier T3               T3            full mix
R3      real same-size solvers, tier T4–T5            T4–T5         full mix
X       repair (wrong code + validator diff -> fix)   interleave    after R1–R3
D1      diff-size track (extended contract)           late          full mix  [needs corpus]
```

Recommended first training run (per `Phase2_V2.md` §8 "Run A/B"): **M1+M2+R1+R2+R3
same-size only, heavy cycling, no repair, no diff-size** — i.e. prove the
canonical target fixes Phase 2 before adding micro-heavy mixes, repair, or the
diff-size track. Compute-tight fallback: `golden same_lit → mixed micro+real →
repair`.

Hold-out: evaluate every run on `Locked_Eval/` (frozen 34 / dev 30 /
latentT_probe 43) — never trained, 0 overlap with the corpus.

---

## 9. Build hooks (to create next)

This doc is the spec; the builders that consume it are not written yet:

```
Phase2_V2/scripts/phase2_prompts.py            machine source-of-truth (mirror of §4, doc-sync checked)
Phase2_V2/scripts/build_phase2_latentT_code.py same-size SFT (real solvers, cycled per §5/§8)
Phase2_V2/scripts/build_micro_latentT.py        micro-family generators + validation (§7)
Phase2_V2/scripts/audit_canonical_shape.py      canonical-shape audit on generated code (eval)
Phase2_V2/scripts/build_phase2_repair.py        repair records (§4h)
Phase2_V2/scripts/run_phase2_latentT_probe.py   execution eval on Locked_Eval (code funnel, pass@k)
```

Hard rule baked into every builder: **supervise on visible-pair T only; never
put a test-output-derived T into a main-training prompt** (`Phase2_V2.md` §5.5).
```
