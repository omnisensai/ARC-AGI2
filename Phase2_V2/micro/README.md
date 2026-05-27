# Micro-primitive corpus

**Locked definition.** A micro generator is a parameterized primitive factory. It
creates many ARC-shaped task instances for one transformation family, all solved
by one verified canonical latent-T solver. The point is to teach the model that
*instances vary while the code-level transformation generator remains invariant.*

```
1 solver  ↔  N generated tasks  ↔  (with pair-cycling) thousands of records
```

## Generator contract (`generators/<family>.py`)

```python
FAMILY = "ray_to_edge"
def canonical_solver() -> str: ...        # the ONE fixed solver for the family
def generate(seed, difficulty) -> dict:   # one task; instance params vary within the family
def family_prompt_hint() -> str: ...      # debug/docs ONLY — never in a training prompt
```

All pairs in a task share the same **family + solver contract**; instance
parameters (size, colour, position, edge, #pairs) vary. The same solver holds.
The generator builds each output **independently of the solver**, so the gate is
a real cross-check, not circular.

## The loop

```
python Phase2_V2/micro/build_micro.py     <family> --n 60     # generate + GATE + emit tasks
python Phase2_V2/micro/build_micro_sft.py <family>            # pair-cycled SFT records
```

`build_micro.py` runs every generated task through the **same acceptance gate as
the real corpus** (`scripts/canonical_gate.py`: solver run vs ground truth on
every pair + AST audit). No pass → no task on disk. Validate-before-emit is the
authority boundary.

### Two validation layers (sample correctness is NOT enough)

Per-sample verification proves the emitted tasks are correct; it does NOT prove
the family CONTRACT is well-specified. If the generator never emits a dangerous
case, thousands of samples pass while the solver's assumptions stay unproven
(this is exactly how the `boundary_mask` bg-majority bug hid until the RNG
happened to make a shape larger than the background).

So there are two gates:

1. **`build_micro.py`** — per-sample: solver reproduces every pair + AST audit +
   subprocess timeout. (correctness, gates 1-3)
2. **`validate_contracts.py`** — per-FAMILY:
   - **precondition audit** over a fresh batch: the properties each solver
     relies on actually hold (background is the unique mode; exactly one ray
     source; unique-largest component; collinear line endpoints; recoverable
     minimal period; each blocker-task demonstrates a blocker on the path).
   - **adversarial probes**: hostile inputs the generator avoids (non-collinear
     endpoints, zero/multiple markers, ties, all-bg, 1×1, solid). Each must
     terminate within a hard timeout and return a well-formed grid OR raise a
     controlled exception — never HANG / MALFORMED / NON-DETERMINISTIC.

  Generation runs in a timeout-guarded subprocess (`--gen-timeout`, default 30s),
  so a hanging/slow generator is reported as `GENERATOR TIMEOUT` rather than
  stalling the validator itself (the failure mode the extract_largest_recolor
  hang first exposed — the validator caught the bug by hanging; now it reports it).

  `python micro/validate_contracts.py --dir micro` (or `--dir micro_diff`).
  On its first run it caught two real bugs sample-checking missed: `complete_line`
  hung forever on non-collinear endpoints (unbounded loop, now bounds-guarded),
  and `ray_until_blocker` could emit whole tasks with no on-path blocker
  (degenerate `ray_to_edge`, now guaranteed ≥1 per task).

## Layout

```
micro/
  generators/<family>.py    family module (solver + generate + hint)
  solvers/<family>.py        the one verified canonical solver
  tasks/<family>/*.json      validated tasks {family, seed, difficulty, params, train[], test[]}
  sft/<family>.jsonl         SFT records {system, user, assistant, meta}
  _validation.json           per-family gate report (kept/failed/by_tier)
  MANIFEST.txt
```

Metadata (`family/seed/difficulty/params`) lives in the task JSON for audit. The
SFT **prompt carries only ARC-shaped evidence** — never that metadata.

## Difficulty tiers (per family; reference uses 0–2, no distractors)

```
0  simplest (fixed size, bg 0, fixed colour/edge; position varies)
1  + varied colour + varied background
2  + varied size + any edge
3  + harmless distractors — ONLY once the solver provably handles them
```

## Family roster & curriculum order

```
ALL 17 families DONE — each 60/60 across tiers 0-2, 240 records (4080 total):

  rays:        ray_to_edge ✅  ray_until_blocker ✅
               ray_diag_to_edge ✅  ray_diag_until_blocker ✅  (corner -> diagonal)
  lines/fill:  complete_line ✅  sandwich_fill ✅ (H/V/diag)  u_cup_fill ✅
               fill_enclosed ✅  (any closed outline — rect + irregular blob)
  selection:   extract_largest_recolor ✅  (select-by-size + recolour to seed colour)
               component_4conn ✅  component_8conn ✅  (matched pair: 4- vs 8-connectivity)
  contour:     boundary_mask ✅
  symmetry:    symmetry_complete ✅  (vertical + horizontal axes)
  periodic:    periodic_extension ✅  periodic_repair ✅
  simulation:  gravity_water ✅  drop_to_floor ✅ (rigid drop)
  seed-flood:  flood_from_seed ✅  flood_from_seed_8 ✅  (matched pair: 4- vs 8-conn)
  seed-radiate: cross_from_seed ✅  star_from_seed ✅  (matched pair: 4- vs 8-direction)
  markers:     move_to_marker ✅  copy_to_markers ✅  recolor_by_marker ✅
               (seed-as-trigger: anchor / replicate / colour-bind)
```

Ray mechanic covered in both forms (edge->perpendicular, corner->diagonal).
Next: scale counts toward ~300/family (`--n 300`), enable tier-3 distractors,
and/or fold the micro SFT into the training mix.

component_4conn/8conn share one construction (diagonal staircase + solid block)
so they give DIFFERENT outputs on look-alike inputs — the pairs reveal which
connectivity applies. Build remaining families on the same pattern, gating each
before scaling counts (current default --n 60; doc target ~300/family).
