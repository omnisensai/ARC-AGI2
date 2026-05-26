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
Easy:    ray_to_edge ✅  complete_line  fill_enclosed  component_recolor
Medium:  ray_until_blocker  u_cup_fill  boundary_mask  mirror
Hard:    periodic_extension  periodic_repair  gravity_water  rotate_translate
```

`ray_to_edge` is the proven reference (60/60 tasks validated across tiers 0–2,
240 cycled records). Build the remaining families on the same pattern, one at a
time, gating each before scaling counts.
