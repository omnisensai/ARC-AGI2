Yes. Here is a Phase 2 strategy markdown you can save as:

```bash
Fine Tune Run 2/PHASE2_CODE_STRATEGY.md
```

````markdown
# Run 2 Phase 2 — Code Strategy

## Purpose

Phase 1 teaches the model to infer and express transformation rules using `T`.

Phase 2 teaches the model to compile those rules into reliable Python code.

The target capability is:

```text
given ARC train pairs + optional T substrates + test input
→ write one valid def solve(input_grid): function
→ function passes all train pairs
→ function generalizes to test input
````

The model must learn two separate skills:

1. **Find the rule**
2. **Write correct code for the rule**

Run 1 showed partial rule transfer on same-size puzzles, but many failures were code-contract failures, shape-contract failures, syntax errors, runtime errors, or near-miss semantic bugs. Diff-size puzzles failed especially hard because Run 1 never trained diff-size substrate or shape-changing code. 

Phase 2 fixes that.

---

# Core Thesis

A model cannot solve ARC by “writing code” alone.

The correct pipeline is:

```text
transformation evidence → rule / T → code pattern → validated solve()
```

Phase 2 should therefore train code in layers:

```text
Code primitives
→ single-pair T-to-code
→ two-pair invariant code
→ all-pair puzzle code
→ direct solver
→ repair with validator feedback
```

Do not jump directly from Phase 1 to full puzzle solving.

---

# System Messages

Use one system message for code generation:

```text
Code Solver
```

Use one system message for repair:

```text
Code Repair
```

Do not expose many artificial task IDs to the model.

The user prompt structure defines the task.

---

# Code Solver Non-Negotiables

Every Code Solver record should reinforce this contract.

```text
Return only valid Python code.

Define exactly one function:
def solve(input_grid):

The function must return a non-empty rectangular list[list[int]].

Every cell must be an int from 0 to 9.

Do not print.
Do not return None.
Do not return a scalar.
Do not return list[int].
Do not read files.
Do not use network.
Do not use eval or exec.
Do not use subprocess.

Allowed imports:
math
collections
itertools
functools
copy

First determine whether the output shape equals the input shape.

If output shape equals input shape:
  copy input_grid before editing.

If output shape differs from input shape:
  do not start from a copy of input_grid.
  compute output height and width first.
  allocate a new output grid.
  then fill it.
```

The code targets must obey this style consistently.

Prompt rules alone are not enough.
The training targets must teach the same habits.

---

# Phase 2 Failure Targets

Run 1 failure analysis implies Phase 2 must directly target these buckets:

| Failure bucket          | Meaning                                             | Phase 2 response         |
| ----------------------- | --------------------------------------------------- | ------------------------ |
| `train_no_grid`         | returns None/scalar/list[int]/bad object            | Code Contract            |
| `exec_error`            | runtime crash                                       | Safe Python patterns     |
| `syntax_major`          | invalid Python                                      | Code Contract            |
| `wrong_shape`           | returns grid but wrong dimensions                   | Shape Contract           |
| `near_miss_90/95`       | mostly correct cells                                | Code Repair              |
| `wrong_training`        | runnable but wrong logic                            | Semantic Repair          |
| `diff-size wrong-shape` | returns input-shaped grid for shape-changing puzzle | Diff-size Shape Contract |

The most important Run 1 lesson:

```text
same-size failures often show partial rule transfer;
diff-size failures show missing shape-changing code curriculum.
```

So Phase 2 must overweight shape-changing code.

---

# Phase 2 Stages

## Phase 2.0 — Code Primitives / Code Contract

### Goal

Teach reliable Python mechanics before full ARC solving.

The model must learn:

```text
valid def solve
valid grid return
safe loops
safe indexing
shape-aware output allocation
same-size vs diff-size code skeletons
```

### Data source

Use synthetic examples + simple ARC-1/easy ARC-derived examples.

Each record:

```text
INPUT
OUTPUT
T
CODE
```

Assistant target:

```python
def solve(input_grid):
    ...
```

### Primitive families

#### 1. Return contract primitives

* identity
* copy input
* constant grid
* allocate H×W grid
* allocate h×w grid
* return rectangular `list[list[int]]`

#### 2. Same-size edit primitives

* replace color A with B
* replace background with color
* edit cells selected by T
* fill marked positions
* preserve unchanged cells

#### 3. Shape-changing primitives

* crop non-background bounding box
* remove empty rows
* remove empty columns
* compress non-zero cells
* extract object
* project rows
* project columns
* tile input 2× / 3×
* grow canvas and place object

#### 4. Component/object primitives

* find all non-background cells
* find bounding box
* 4-connected components
* 8-connected components
* largest component
* smallest component
* component by color
* object touching border
* object not touching border

#### 5. Geometry primitives

* draw horizontal line
* draw vertical line
* draw diagonal line
* fill rectangle
* mirror horizontally
* mirror vertically
* rotate 90
* translate object
* extend line to boundary
* draw between two markers

#### 6. Selection/counting primitives

* most frequent color
* least frequent non-background color
* color appearing once
* select marker color
* select center object
* select enclosed cell
* select object by size

### Recommended mix

```yaml
phase2_0_code_primitives_mix:
  return_contract:          0.15
  same_size_edits:          0.15
  shape_change_primitives:  0.25
  object_components:        0.20
  geometry:                 0.15
  selection_counting:       0.10
```

### Validation

Every code target must pass:

```text
syntax ok
defines solve(input_grid)
returns list[list[int]]
rectangular
all cells int 0-9
matches expected output
```

No unvalidated code enters training.

---

## Phase 2.1 — Single-Pair T-to-Code

### Goal

Teach the model to compile a known transformation into code.

This is not full ARC solving yet.

It teaches:

```text
given INPUT + OUTPUT + T
write a valid solve() that reproduces the transformation family
```

### Prompt format

```text
INPUT:
<grid>

OUTPUT:
<grid>

T:
<substrate>

CODE:
```

### Assistant target

```python
def solve(input_grid):
    ...
```

### Important

The target code should not merely return the shown output unless the rule is truly constant-output.

Bad:

```python
def solve(input_grid):
    return [[2, 2], [2, 2]]
```

Good when rule is “crop non-zero cells”:

```python
def solve(input_grid):
    out = []
    for row in input_grid:
        vals = [x for x in row if x != 0]
        if vals:
            out.append(vals)
    return out
```

### Purpose

Train code patterns from simple evidence.

This reduces:

```text
syntax_major
train_no_grid
exec_error
wrong_shape
```

---

## Phase 2.2 — Two-Pair Invariant Code

### Goal

Teach that one `solve()` must implement the shared rule, not memorize one pair.

### Prompt format

```text
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P1 T:
<substrate>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

P2 T:
<substrate>

CODE:
```

### Assistant target

```python
def solve(input_grid):
    ...
```

The code must pass both pairs.

### Why

One pair allows many fake rules.

Two pairs force the code to capture a more general transformation.

---

## Phase 2.3 — All-Pair T-to-Code

### Goal

Teach full puzzle-level code synthesis with T scaffolding.

### Prompt format

```text
P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P1 T:
<substrate>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

P2 T:
<substrate>

P3 INPUT:
<grid>

P3 OUTPUT:
<grid>

P3 T:
<substrate>

TEST INPUT:
<grid>

TEST T:
<substrate>

CODE:
```

### Assistant target

```python
def solve(input_grid):
    ...
```

### Purpose

This is the main substrate-to-code bridge.

The model learns:

```text
T expresses the rule.
Code implements the rule.
One solve() must work for all train pairs and test input.
```

---

## Phase 2.4 — Direct Puzzle-to-Code

### Goal

Train the final direct solving interface.

### Prompt format

```text
TRAIN PAIRS:

P1 INPUT:
<grid>

P1 OUTPUT:
<grid>

P2 INPUT:
<grid>

P2 OUTPUT:
<grid>

TEST INPUT:
<grid>

CODE:
```

### Assistant target

```python
def solve(input_grid):
    ...
```

### Note

This should come after T-to-code stages.

Direct solving is harder because the model must infer the rule and write code in one pass.

---

## Phase 2.5 — Code Repair

### Goal

Teach the model to fix wrong code using validator feedback.

### Input

```text
PUZZLE:
<train pairs + test input>

WRONG CODE:
<generated code>

VALIDATOR FEEDBACK:
<contract error / shape error / exec error / cell_diff / diff_map>

CORRECTED CODE:
```

### Assistant target

```python
def solve(input_grid):
    ...
```

### Feedback types

Use factual feedback only:

```text
syntax error
exception type
traceback
returned type
actual shape
expected shape
cell_diff
diff_map
bad cell values
non-rectangular grid
timeout
```

No LLM judge.

### High-value repair examples

Prioritize:

```text
near_miss_95
near_miss_90
wrong_shape
same-size exec_error
diff-size shape_contract
syntax_major
train_no_grid
```

---

# Pair Cycling Augmentation

For each puzzle with a validated correct code target, recycle the puzzle into multiple training views.

## Pair permutation

Same puzzle. Same code. Different order.

```text
P1 P2 P3 → code
P2 P3 P1 → same code
P3 P1 P2 → same code
```

## Leave-one-pair-as-test

For a puzzle with N train pairs, show N-1 pairs and hide one output.

```text
P1 INPUT/OUTPUT/T
P2 INPUT/OUTPUT/T

TEST INPUT: P3 input
TEST T: P3 T

CODE:
```

Assistant target:

```python
same validated solve()
```

Repeat by cycling which pair is held out.

## Why

This teaches:

```text
the code is the invariant rule
not pair order
not one memorized example
not one prompt surface
```

This is better than oversampling the exact same prompt.

## Guardrail

Do not show too little evidence.

Default:

```text
show N-1 pairs
hold out 1 pair
```

Avoid training from one pair only for complex puzzles unless it is in Phase 2.1 primitive training.

---

# Same-Size vs Diff-Size Code Skeletons

## Same-size default

Use when output shape equals input shape.

```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])
    out = [row[:] for row in input_grid]

    # edit out safely

    return out
```

## Diff-size default

Use when output shape differs from input shape.

```python
def solve(input_grid):
    H = len(input_grid)
    W = len(input_grid[0])

    out_h = ...
    out_w = ...
    out = [[0 for _ in range(out_w)] for _ in range(out_h)]

    # fill out

    return out
```

## Non-negotiable

For shape-changing puzzles, avoid:

```python
out = [row[:] for row in input_grid]
return out
```

unless the code later intentionally constructs and returns a different shape.

---

# Connectivity Curriculum

The model must learn the difference between 4-connected and 8-connected components.

## 4-connected

```python
def neighbors4(r, c):
    return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
```

## 8-connected

```python
def neighbors8(r, c):
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr != 0 or dc != 0:
                out.append((r + dr, c + dc))
    return out
```

Train tiny contrastive examples where the answer changes depending on 4-connected vs 8-connected.

---

# Geometry Helpers

Train stable helpers instead of letting the model improvise fragile geometry.

## Sign

```python
def sign(x):
    return (x > 0) - (x < 0)
```

## Draw line

```python
def draw_line(out, r1, c1, r2, c2, color):
    dr = sign(r2 - r1)
    dc = sign(c2 - c1)
    r, c = r1, c1
    while True:
        out[r][c] = color
        if r == r2 and c == c2:
            break
        r += dr
        c += dc
```

Use for:

```text
horizontal lines
vertical lines
diagonal lines
between two markers
sandwich patterns
line extension
```

---

# Phase 2 Data Sources

## 1. Synthetic primitives

Generated mechanically.

Use for Phase 2.0 and 2.1.

## 2. ARC-AGI-1 / easier puzzles

Use if validated code targets exist.

Good for:

```text
simple rule families
clean coding patterns
primitive composition
```

## 3. ARC-AGI-2 hard train split

Use for:

```text
all-pair T-to-code
direct puzzle-to-code
repair
```

## 4. Model-generated attempts

Only use after validator labeling.

```text
model proposes
validator labels
human/data pipeline decides training role
```

Validated correct code can become target data.

Wrong code can become repair data only if paired with factual feedback and a correct target.

---

# Failure Trace Collection

Before building repair data, run diagnostic eval to collect:

```text
generated code
exception / traceback
returned type
returned shape
expected shape
cell_diff
diff_map
failure bucket
```

Failure buckets:

```text
correct
near_miss_95
near_miss_90
wrong_training
wrong_shape
train_no_grid
exec_error
syntax_error
timeout
non_rectangular
bad_cell_values
```

Save each attempt as JSON.

The purpose is observability, not leaderboard score.

---

# Phase 2 Evaluation

Use separate evals for each capability.

## Code Contract eval

Metrics:

```text
syntax_ok %
has_solve_function %
valid_grid_return %
exec_error %
train_no_grid %
wrong_shape %
```

## T-to-Code eval

Given T scaffold:

```text
train-pair pass rate
test-output pass rate if known
same-size vs diff-size split
```

## Direct Solver eval

Raw puzzle → code.

Metrics:

```text
pass@1
pass@2
exec_error
wrong_shape
near_miss_90/95
```

## Repair eval

Wrong code + feedback → corrected code.

Metrics:

```text
repair lift
D-only pass
D→R pass
near_miss conversion rate
shape-error conversion rate
exec-error conversion rate
```

---

# Recommended Phase 2 Mix

Initial training mix:

```yaml
phase2_mix:
  code_primitives_contract: 0.20
  single_pair_t_to_code:    0.20
  two_pair_t_to_code:       0.20
  all_pair_t_to_code:       0.20
  direct_puzzle_to_code:    0.10
  code_repair:              0.10
```

After Code Contract stabilizes, shift toward:

```yaml
phase2_later_mix:
  code_primitives_contract: 0.05
  single_pair_t_to_code:    0.10
  two_pair_t_to_code:       0.15
  all_pair_t_to_code:       0.30
  direct_puzzle_to_code:    0.15
  code_repair:              0.25
```

---

# Done Criteria

Phase 2 is working when:

```text
train_no_grid sharply decreases
exec_error sharply decreases
wrong_shape sharply decreases on diff-size
same-size near-misses become exact passes
T-scaffolded code beats direct code
repair loop adds measurable lift
```

Target gates:

```text
Code Contract:
  valid grid return > 95%
  exec_error < 5%
  wrong_shape < 5% on contract set

T-to-Code:
  clear lift over direct code

Repair:
  D→Repair score > D-only score
```

---

# Final Principle

Phase 2 is not “make the model smarter.”

Phase 2 is:

```text
teach the model to compile transformation rules into safe, exact Python
```

The model proposes code.

The validator decides correctness.

Only validator-approved code becomes truth.

```

This is the clean Phase 2 bridge: **T-language → robust code → repair loop**.
```

Yes — for **Phase 2**, assume **8k will not fit the full “all pairs + all T + code + repair” format**.

So Phase 2 must be designed as **context-budgeted**, not just “raise sequence_len.”

## My call

Use **two Phase 2 lanes**:

```text
Lane A — 8k main curriculum
Lane B — 16k long-context specialist
```

Do not force everything into one format.

## Why

Phase 2 has much bigger records:

```text
train pairs
outputs
T substrates
test input
test T
Python code
wrong code
validator feedback
diff maps / tracebacks
corrected code
```

That will blow up fast.

So we should split by record type.

---

## Lane A — 8k main curriculum

Use this for most training:

```text
code primitives
single-pair T→code
two-pair T→code
compact all-pair records
short repair records
```

This lane teaches:

```text
valid Python
shape discipline
safe loops
primitive code patterns
small/medium rule compilation
```

Keep it fast and cheap.

## Lane B — 16k long-context specialist

Use only for records that truly need context:

```text
all-pair T→code on large puzzles
multi-pair diff-size prompts
repair with wrong code + feedback + corrected code
hard examples with long code
```

This lane teaches:

```text
full puzzle synthesis
long-context repair
large-grid rule application
```

Run it after Lane A or as a short continuation.

---

## Better than just 16k: make the generator adaptive

For every Phase 2 record, compute token length and route it:

```text
<= 8192       → phase2_train_8k.jsonl
8193–16384    → phase2_train_16k.jsonl
> 16384       → compress / split / skip
```

This avoids making the whole training slow because of the long tail.

## Compression rules before 16k

Before routing to 16k, try:

```text
1. Drop redundant OUTPUT when same-size T is present.
2. Use only N-1 or 2 representative pairs.
3. Use pair cycling instead of all pairs.
4. Use compact feedback instead of full traceback.
5. Use cropped diff maps, not full diff maps.
6. Keep only relevant failure info.
```

If still over 8k, then 16k.

---

## Phase 2 prompt policy

For code training, do not always include every field.

### Short single-pair

```text
INPUT
T
OUTPUT
CODE:
```

### Two-pair

```text
P1 INPUT / OUTPUT / T
P2 INPUT / OUTPUT / T
CODE:
```

### All-pair compact

For same-size, because T is lossless:

```text
P1 INPUT / T
P2 INPUT / T
TEST INPUT / TEST T
CODE:
```

Output can be omitted if T is present.

### Diff-size

Because diff-size T is lossy:

```text
P1 INPUT / OUTPUT / T
P2 INPUT / OUTPUT / T
TEST INPUT / TEST T
CODE:
```

Need outputs for grounding.

### Repair compact

```text
PUZZLE SUMMARY
WRONG CODE
VALIDATOR FEEDBACK:
- exception or shape error
- cell_diff per pair
- cropped diff map if useful
CORRECTED CODE:
```

Avoid giant tracebacks unless the task is specifically exec-error repair.

---

## Training recommendation

Start Phase 2 with:

```yaml
sequence_len: 8192
```

for Lane A.

Then separately:

```yaml
sequence_len: 16384
micro_batch_size: 1
gradient_accumulation_steps: higher
```

for Lane B.

Do a 5-step smoke test first.

## Actual risk of 16k in Phase 2

The risk is acceptable **if it is isolated**.

Bad:

```text
Everything at 16k
```

Good:

```text
Only long-context examples at 16k
```

Because the latter keeps the main curriculum fast.

---

## Bottom line

You are right: **Phase 2 full records will barely fit or not fit at 8k.**

So the answer is not “just 16k.”

The answer is:

```text
Phase 2 must be token-routed:
8k for code primitives and compact T→code,
16k for long all-pair and repair examples,
split/compress anything above 16k.
```

That gives us both speed and full-context capability.

Yes — but **not mid-run safely**.

## If training has not started

Yes. Change the Axolotl config before launching:

```yaml
sequence_len: 16384
micro_batch_size: 1
gradient_accumulation_steps: 32
sample_packing: true
gradient_checkpointing: true
flash_attention: true
bf16: true
```

Then run a tiny smoke test first:

```bash
axolotl train "Fine Tune Run 2/phase2_16k_axolotl.yaml" --max-steps 5
```

## If training is already running

Do **not** edit `sequence_len` inside the same running job.

Stop it cleanly, then restart from checkpoint with the new config only if needed.

Changing context length mid-run can break prepared dataset/cache assumptions and make results hard to interpret.

## Best Phase 2 design

Use two separate configs:

```text
phase2_8k_axolotl.yaml
phase2_16k_axolotl.yaml
```

And two routed datasets:

```text
phase2_train_8k.jsonl.gz
phase2_train_16k.jsonl.gz
```

Routing rule:

```text
<= 8192 tokens     → 8k dataset
8193–16384 tokens  → 16k dataset
> 16384 tokens     → compress/split/skip
```

Then train:

```bash
axolotl train "Fine Tune Run 2/phase2_8k_axolotl.yaml"
```

Probe.

Then continue with the long-context specialist:

```bash
axolotl train "Fine Tune Run 2/phase2_16k_axolotl.yaml"
```

using the 8k LoRA as the starting adapter.

So yes, we can change it in training strategy — but treat 16k as a **separate continuation run**, not a live mid-run change.


