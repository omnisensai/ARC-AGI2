# Fine Tuning Strategy — Synthesis

Cross-puzzle synthesis of what to fine-tune. Aggregates insights from per-puzzle
notes (`8f3a5a89.md`, etc.) and from the iteration arcs of 4-5 models on each
puzzle. This is the spec for "what data, in what proportions, on what model."

When the per-puzzle catalog grows past ~10 puzzles, this doc is what gets
revised. Until then, treat the proportions below as hypotheses, not gospel.

---

## TL;DR

Five skill clusters to train, in descending leverage order:

1. **Substrate fluency** — reading and writing the `+ = - . ~` transformation
   grid encoding. **Highest leverage** because pretraining has zero coverage of
   this notation. Every model is decoding it on the fly via in-context inference.
2. **Topology vision** — classifying connected components with cluster-level
   properties (edge-touching, internal, line-shaped) as first-class objects,
   not as per-cell tests.
3. **Rule → code synthesis** — given a rule (in NL, in substrate, or as 2-3
   transformation grids), produce idiomatic Python that implements it.
4. **Iteration meta-skill** — patch failing pairs without breaking passing
   pairs. The most underrated skill; small models lack it almost entirely.
5. **Bug-pattern library** — recognise common failure shapes (per-cell-when-
   cluster, wrong-connectivity, hardcoded-dims) and apply the matching fix.

**Key insight on data generation:** ~80% of training data can be generated
with pure Python from the 2000 ARC-AGI 1+2 puzzles. No LLM API calls required
for the bulk of the dataset. See "Data generation pipeline" section below.

**Key insight on infrastructure:** you don't need a local GPU. Free Google
Colab T4 GPU is enough to validate the hypothesis. First experiment is a
weekend project for $10–50.

---

## Why fine-tune at all

The framework has shown that **small models can solve hard ARC puzzles** when
the prompt + feedback substrate gives them the right scaffolding. Sonnet 4.6
went from 0/3 to 3/3 on 8f3a5a89 in a single iter once a 6-line worked example
landed. So the question isn't "can the model do this" — it's "can we get the
model to do this *without* hand-crafted scaffolding per puzzle?"

That's what fine-tuning is for. The framework teaches; the SFT bakes in.

**Honest caveat:** before fine-tuning, exhaust prompt-side levers. The cluster
worked example (one paragraph in TIPS) outperformed 8 iters of mechanistic
per-cell feedback. Fine-tuning makes sense after the prompt substrate is at
its ceiling, not before.

---

## What to train, in detail

### 1. Substrate fluency (NEW for LLMs)

The transformation grid encoding (`. = + - ~` arranged as cell-aligned grids)
is **not in any pretraining corpus**. Every model that uses it is doing
in-context inference of the grammar from the prompt. Native fluency would
compound with everything else — substrate would become a thinking medium, not
an interface to decode.

**Training tasks (all have free ground-truth via `transformation_grid.py`):**

- **Substrate decoding** — input: input grid + transformation grid. Output:
  output grid. Pure mechanical translation. Forces internalisation of the
  symbol algebra cell-by-cell.
- **Substrate encoding** — input: (input grid, output grid). Output:
  transformation grid. Lets the model self-verify by encoding its own
  predictions and comparing against the rule pattern.
- **Substrate → rule (NL)** — input: 2-3 transformation grids from training
  pairs. Output: 1-paragraph natural-language description of the rule.
  Bridges substrate to verbal reasoning.
- **Substrate → code** — input: transformation grid pattern across pairs.
  Output: `solve()` Python. The most direct path to ARC scoring.
- **Substrate completion / few-shot** — input: 2 (input, substrate) pairs.
  Output: predict substrate for a 3rd input. Trains pattern induction *in
  substrate space*, where patterns are denser than in raw grids.

**Why this is the highest-leverage skill:** substrate is lossy compression of
transformations — it discards color identity and keeps only the *operation*
per cell. That's the right abstraction level for ARC rules. Reading at the
right abstraction level is the single biggest leverage point.

**Analogy:** training on LaTeX makes models better at math because the notation
IS the abstraction. Same idea here. Substrate is to transformation patterns
what LaTeX is to math.

**Caveat — finalise the alphabet first.** Currently 5 symbols (`. = + - ~`).
Any future change (e.g. adding `~_dim` for dim-recolor, splitting `+` into
thickness variants) requires retraining. Lock the alphabet to a stable v3
before committing to a fine-tune.

---

### 2. Topology vision (cluster-level properties)

Sonnet's 8-iter failure on 8f3a5a89 was a single bug repeated: testing
"edge-touching" per cell instead of per cluster. The validator was telling it
*which output cells were wrong*; it never told the model *which line of code
was wrong*. A worked example fixed it instantly. Train this directly so
models don't need the worked example.

**Training tasks (all programmatically generable):**

- **Cluster classification** — input: grid + color. Output: list of clusters
  with structural properties: `{cells, size, edge_touching, vertical_line,
  horizontal_line, bounding_box, neighbors_4conn, neighbors_8conn}`. Forces
  the model to compute cluster-level properties as structured output.
- **Connectivity disambiguation** — input: two grids (before/after a flood-
  fill or BFS). Output: which connectivity was used (4 vs 8). Trains the
  model to *notice* the distinction instead of defaulting to one.
- **Anchor identification** — input: grid. Output: the cell most likely to be
  the seed (unique color, distinct count, lone marker). Trains the
  "scan for anchor" reflex many ARC rules require.
- **Halo / boundary computation** — input: grid + region. Output: cells in
  the halo, with explicit halo thickness and connectivity choice.
- **Property propagation** — input: grid + a property predicate at the
  cluster level (e.g. "any cell on edge"). Output: the set of all cells
  inheriting that property. Directly trains the cluster-vs-cell granularity
  Sonnet kept getting wrong.

**Data source:** programmatic — `mechanistic_feedback_generator.py` flipped
into a labeler. Generate millions of examples cheaply.

---

### 3. Rule → code synthesis

Pair every topology fact with the Python that computes it. Models tend to
reinvent code structure each time; train them to use canonical scaffolding.

**Training tasks:**

- **Rule (NL) → code** — input: natural-language rule. Output: idiomatic
  Python implementing it. Library of canonical patterns: `bfs_from(seed,
  barrier)`, `flood_fill(grid, color, conn)`, `cluster_classify(cells,
  predicate)`, `propagate_property(cluster, prop)`, `paint_halo(region,
  thickness, conn)`.
- **Bug-pattern → fix** — input: a `solve()` with a known bug pattern + the
  failing pair's mechanistic feedback. Output: the corrected `solve()`. Bug
  categories from the per-puzzle catalog.
- **Code skeleton → completion** — input: a 5-line skeleton (`def solve:
  bfs from anchor; classify clusters; paint halo`). Output: filled-in code.
  Forces use of canonical scaffolding instead of ad-hoc structure.

**Data source:** bootstrap with Opus 4.7 generating (rule, code) pairs;
filter by `validate_solution_complete(puzzle, code)` returning training 3/3.
Keep only validated pairs. Maybe 10K-50K examples after filtering.

---

### 4. Iteration meta-skill (preserve mechanism, scope fixes)

What Sonnet really lacked wasn't topology or code — it was **not breaking
working logic when patching new bugs**. Its iter trajectory was
1→1→1→1→2→0→1→0 on 8f3a5a89. The "2" came from a real fix; the "0" came from
over-extending that fix to a global rule. This isn't a knowledge gap, it's an
iteration discipline gap.

**Training tasks:**

- **Trajectory replay** — input: iter N feedback (failing pair diagnostics +
  passing pair anchors) + iter N's `solve()`. Output: iter N+1's `solve()`
  that fixes the failing pair WITHOUT changing the lines that made other
  pairs pass. Force diff-based reasoning, not full rewrites.
- **Regression detection** — input: two `solve()` versions + which pair
  regressed between them. Output: identify the lines that changed and broke
  the pair. Trains the introspection the v2 reminder asks for in plain text.
- **Scoped-fix training** — input: a passing `solve()` + a failing pair +
  the mechanistic-feedback bug name. Output: a `solve()` with an *additive
  scoped condition* (e.g. `if cluster.is_internal: skip_halo`), NOT a rewrite
  of the parent rule. Directly counters the over-extension anti-pattern.
- **Identical-code detection** — input: iter N code + iter N+1 code that's
  byte-identical with reworded prose. Output: the model recognising this is
  not a valid iter and producing actual changes. Counters Sonnet's iter 4
  pattern.

**This is the most valuable signal you cannot easily get from web data.**
Pretraining doesn't contain "iterate Python solutions to ARC puzzles without
regressing on prior tests."

**Two paths to data — see "Iteration meta-skill data: Path A vs Path B"
section below.** Spoiler: programmatic bug mutation (Path B) beats real
trajectory scraping (Path A) for v1.

---

### 5. Bug-pattern library (cross-cuts other categories)

Indexed by failure signature, each entry contains:
- The bug pattern name (e.g. `cluster_vs_cell_granularity`)
- A 5-line minimal reproducer (input + buggy code + correct code)
- The mechanistic-feedback signature that detects it (which cluster
  properties / cell coordinates are mis-classified)

Training the model to **recognise the bug pattern from the feedback signature**
turns the bug library into a real reasoning step: "I see missed activations
clustered along a column inside an edge-touching wall — this is the
`cluster_vs_cell_granularity` pattern, fix is to lift the edge test to
cluster level."

**Library coverage (extend as catalog grows):**

| Pattern name | Source puzzle | Signature |
|---|---|---|
| `cluster_vs_cell_granularity` | 8f3a5a89 | missed activations along a single column/row inside an edge-touching cluster |
| `wrong_connectivity_4_vs_8` | 8f3a5a89 | missed diagonal-position halo cells |
| `hardcoded_grid_dimensions` | 8f3a5a89 | training pairs all fail; test passes |
| `generic_perimeter_framing` | 8f3a5a89 | output has `+` ring around grid edge regardless of seed |
| `over_extended_scoped_fix` | 8f3a5a89 | regression after 2/3; passing pair P broke when fixing different pair |
| `identical_code_resubmission` | 8f3a5a89 | byte-equal code across iters |
| ... | ... | ... |

---

## Recommended training data composition

For the multi-task SFT mix, hypothesised proportions:

| Skill cluster | % of data | Cost to generate |
|---|---|---|
| Substrate fluency | 30% | $0 (pure Python) |
| Topology vision | 30% | $0 (pure Python) |
| Rule → code synthesis | 20% | $5-30 (Opus bootstrap + validate) — or skip in v1 |
| Iteration meta-skill | 15% | $0 (Path B: bug mutation) — or $300-1K (Path A: real trajectories) |
| Bug-pattern library | 5% | $0 (pure Python via mutation) |

**Rationale for substrate at 30%:** it's the lowest-coverage-in-pretraining
skill, so each example carries more information than topology or code (which
have web representation). 30% is a hypothesis; could be 40-50% if substrate
fluency proves to dominate scoring gains.

---

## Data generation pipeline (where examples come from)

### Pure Python vs LLM-needed breakdown

| Skill cluster | Pure Python? | Source | Effort |
|---|---|---|---|
| Substrate decoding/encoding/completion | ✅ Yes | `transformation_grid.py` + 2000 ARC puzzles | Trivial — afternoon |
| Topology vision (cluster classification) | ✅ Yes | `mechanistic_feedback_generator.py` flipped to labeler | Trivial — afternoon |
| Property propagation | ✅ Yes | Synthetic random grids | Trivial — hours |
| Rule → code | ⚠ LLM helpful | Existing solvers + Opus generation + framework validation | Medium — $5-30 in API |
| Iteration meta-skill (Path B mutation) | ✅ Yes | Canonical solvers + bug library + framework | Medium — 1-2 days code |
| Iteration meta-skill (Path A real trajectories) | ❌ Needs API | Industrialised bake-off harness | Hard — 2 weeks + $300-1K |
| Bug-pattern recognition | ✅ Yes | Bug-mutation pipeline | Same as iteration Path B |

**Bottom line: 80%+ of training data is pure Python from the 2000 puzzles.**
You don't need an LLM to bootstrap v1.

### Concrete training example formats (JSONL)

The standard is JSONL — one JSON object per line, each with a `messages`
array containing user prompt + assistant target. Examples per skill cluster:

#### 1a. Substrate decoding (substrate → output)

```jsonl
{"messages": [
  {"role": "user", "content": "Apply this transformation rule to the input grid.\n\nINPUT:\n[8, 8, 8, 8]\n[8, 1, 1, 8]\n[8, 8, 8, 8]\n[6, 8, 8, 8]\n\nTRANSFORMATION RULE:\n[+, +, +, +]\n[+, =, =, +]\n[+, ., ., +]\n[=, +, +, +]\n\nReturn the output grid."},
  {"role": "assistant", "content": "[7, 7, 7, 7]\n[7, 1, 1, 7]\n[7, 8, 8, 7]\n[6, 7, 7, 7]"}
]}
```

#### 1b. Substrate encoding ((input, output) → substrate)

```jsonl
{"messages": [
  {"role": "user", "content": "Encode the transformation between these grids using substrate symbols (. = + - ~).\n\nINPUT:\n[8, 8, 8]\n[8, 1, 8]\n[6, 8, 8]\n\nOUTPUT:\n[7, 7, 7]\n[7, 1, 7]\n[6, 7, 7]\n\nReturn the transformation grid."},
  {"role": "assistant", "content": "[+, +, +]\n[+, =, +]\n[=, +, +]"}
]}
```

#### 2a. Topology vision — cluster classification

```jsonl
{"messages": [
  {"role": "user", "content": "Classify all clusters of color 1 in this grid. For each cluster, return: cells, size, edge_touching, vertical_line, horizontal_line.\n\nGRID:\n[8, 8, 8, 8, 8, 8]\n[8, 1, 1, 8, 8, 8]\n[8, 8, 8, 8, 8, 8]\n[1, 8, 8, 8, 8, 1]\n[1, 8, 8, 8, 8, 1]\n[1, 8, 8, 8, 8, 1]"},
  {"role": "assistant", "content": "Cluster 1: cells=[(1,1),(1,2)], size=2, edge_touching=False, vertical_line=False, horizontal_line=True\nCluster 2: cells=[(3,0),(4,0),(5,0)], size=3, edge_touching=True, vertical_line=True, horizontal_line=False\nCluster 3: cells=[(3,5),(4,5),(5,5)], size=3, edge_touching=True, vertical_line=True, horizontal_line=False"}
]}
```

#### 2b. Topology vision — property propagation (the cluster-vs-cell skill)

```jsonl
{"messages": [
  {"role": "user", "content": "A cluster contains cells [(0,6), (1,6), (2,6), ..., (15,6)]. Cells (0,6) and (15,6) are on the grid edge (grid is 16x16). Which cells inherit the 'edge_touching' property?"},
  {"role": "assistant", "content": "All 16 cells of the cluster inherit edge_touching=True. The property applies at the cluster level — once any member cell touches the grid edge, the entire connected component is classified as edge-touching, regardless of whether individual cells are on the boundary."}
]}
```

This is the *exact* concept that flipped Sonnet 0→3/3 on 8f3a5a89.

#### 3. Rule → code synthesis

```jsonl
{"messages": [
  {"role": "user", "content": "Implement this rule in Python:\n\n'For each connected component of color 1 that touches the grid edge, mark it as a barrier. Flood-fill from the unique 6 marker through cells of color 8. Paint the boundary of the reachable region in color 7 (using 8-connectivity). Preserve the 6 marker and any 1-clusters adjacent to the reachable region.'\n\nReturn a `def solve(input_grid):` function."},
  {"role": "assistant", "content": "def solve(input_grid):\n    from collections import deque\n    grid = [row[:] for row in input_grid]\n    H, W = len(grid), len(grid[0])\n    seed = next((r,c) for r in range(H) for c in range(W) if grid[r][c] == 6)\n    # ... full canonical implementation ...\n    return output"}
]}
```

#### 4. Iteration meta-skill — scoped fix

```jsonl
{"messages": [
  {"role": "user", "content": "Your code currently passes Pair 1 and Pair 2 but fails Pair 3. The mechanistic feedback says: 'Cluster at rows 9-11, cols 9-10 is INTERNAL but your code applied halo around it.' Update your solve() to fix Pair 3 WITHOUT changing Pair 1 or Pair 2 behavior.\n\nCURRENT solve():\n```python\nfor cell in kept_ones:\n    output[cell] = 1\n    paint_halo_around(cell)\n```\n\nReturn updated solve()."},
  {"role": "assistant", "content": "The fix is a SCOPED predicate, not a rewrite. Add a condition that excludes INTERNAL clusters from halo painting; leave the rest of the logic intact:\n\n```python\nfor cluster in kept_clusters:\n    is_internal = not any_cell_touches_edge(cluster)\n    if is_internal:\n        continue  # scoped skip\n    for cell in cluster:\n        output[cell] = 1\n        paint_halo_around(cell)\n```"}
]}
```

#### 5. Bug-pattern recognition

```jsonl
{"messages": [
  {"role": "user", "content": "Identify the bug pattern in this code given the failure feedback.\n\nCODE:\n```python\nfor r, c in cluster:\n    if r == 0 or r == H-1 or c == 0 or c == W-1:\n        is_edge_touching = True\n```\n\nFEEDBACK: 'Pair 1 fails. Missed activations at cells (2,5), (3,5), ..., (13,5). These cells are inside cluster X which spans (0,5)-(15,5). Cluster X touches grid edge at (0,5) and (15,5) but cells (2,5)-(13,5) are not on grid boundary.'"},
  {"role": "assistant", "content": "Bug pattern: `cluster_vs_cell_granularity`. The code tests edge-touching per cell instead of per cluster. Cells in the middle of an edge-touching cluster fail the per-cell test even though their cluster IS edge-touching.\n\nFix: lift the test to cluster level using `any()`:\n```python\nis_edge_touching = any(r == 0 or r == H-1 or c == 0 or c == W-1 for r, c in cluster)\n```"}
]}
```

### Realistic data volumes from 2000 ARC puzzles

| Skill | Source | Examples | LLM API needed? |
|---|---|---|---|
| Substrate decode/encode/completion | 2000 puzzles × pairs × 3 task types × augmentation | **~96K** | No |
| Topology vision (cluster classification) | 2000 puzzles + synthetic | **~150K** | No |
| Property propagation | Pure synthetic | **~50K** | No |
| Rule → code | Existing canonical solvers + Opus bootstrap (optional) | **~1K** | Optional |
| Iteration meta-skill (Path B mutation) | Canonical solvers × bug patterns × puzzles that expose | **~20K** | No |
| Bug-pattern recognition | Same mutation pipeline | **~10K** | No |

**Total without ANY LLM API calls: ~326K examples.** Generated in a few hours
of Python on a MacBook.

### Data generator script outline

```python
# data_generator.py
import json, glob
from transformation_grid import generate_transformation_grid
from mechanistic_feedback_generator import find_clusters, classify_cluster

def generate_substrate_fluency_data(puzzles):
    examples = []
    for puzzle in puzzles:
        for pair in puzzle['train'] + puzzle['test']:
            substrate = generate_transformation_grid(pair['input'], pair['output'])[0]
            # Decode task
            examples.append(format_decode_example(pair['input'], substrate, pair['output']))
            # Encode task
            examples.append(format_encode_example(pair['input'], pair['output'], substrate))
            # Completion task (multi-pair)
            # ... augmentations: rotate, flip, color-permute ...
    return examples

def generate_topology_vision_data(puzzles):
    examples = []
    for puzzle in puzzles:
        for pair in puzzle['train']:
            grid = pair['input']
            for color in set(c for row in grid for c in row):
                clusters = find_clusters(grid, color)
                labels = [classify_cluster(c, grid) for c in clusters]
                examples.append(format_classification_example(grid, color, labels))
    return examples

def generate_iteration_data_via_mutation(canonical_solvers, bug_library, puzzles):
    examples = []
    for solver_path in canonical_solvers:
        canonical = open(solver_path).read()
        for bug_pattern in bug_library:
            buggy = inject_bug(canonical, bug_pattern)
            failing_pair = find_pair_exposing_bug(puzzles, buggy)
            if failing_pair:
                feedback = run_validator_feedback(buggy, failing_pair)
                examples.append(format_scoped_fix_example(buggy, feedback, canonical))
    return examples

def main():
    puzzles = [json.load(open(f)) for f in glob.glob("arc_puzzles/*.json")]
    solvers = glob.glob("Solvers/*.py")
    bugs = json.load(open("Fine Tuning Strategy/bug_patterns.json"))
    
    all_examples = []
    all_examples += generate_substrate_fluency_data(puzzles)
    all_examples += generate_topology_vision_data(puzzles)
    all_examples += generate_property_propagation_data()
    all_examples += generate_iteration_data_via_mutation(solvers, bugs, puzzles)
    all_examples += generate_bug_pattern_data(solvers, bugs)
    
    with open("training_data.jsonl", "w") as f:
        for ex in all_examples:
            f.write(json.dumps(ex) + "\n")
```

~500 lines of code total. One week to build.

---

## Iteration meta-skill data: Path A vs Path B

The trickiest cluster. Two ways to generate it; very different difficulty.

### Path A — Real trajectories from LLM bake-offs (hard, small N)

Scrape actual iter responses from running models:
- Sonnet's iter 1-9 on 8f3a5a89 = 9 trajectory examples
- Across 4-5 models × N puzzles = small but real

**Pros:** real LLM behavior, real mistakes, real recoveries.
**Cons:** small N (hundreds-low-thousands), expensive to generate, manual
quality-check needed, scaling requires industrialised harness.

### Path B — Programmatic bug mutation (easy, high N)

Take a canonical solver, inject known bugs from the library, generate the
training pair synthetically:

```python
canonical = "Solvers/seeded_reachable_wall_contouring.py"
for bug in BUG_PATTERNS:  # cluster_vs_cell, wrong_4conn, hardcoded_dim, ...
    buggy_code = mutate(canonical, bug)
    failing_pair = find_pair_exposing_bug(puzzles, buggy_code)
    feedback = run_validator(buggy_code, failing_pair)
    examples.append({
        "user": f"{buggy_code}\n{feedback}\n\nFix without breaking other pairs.",
        "assistant": canonical  # the fix is "revert the bug"
    })
```

**Pros:** unlimited N, $0 cost, deterministic, every example is by-construction
correct, covers exactly the bug patterns we want to penalise.
**Cons:** synthetic — bugs are ones we already know about (creative new
mistakes won't appear).

### Industrialised bake-off harness (Path A — only if pursuing)

Required to scale Path A beyond ~50 examples. Pseudocode:

```python
for puzzle in puzzles:                          # ~120 puzzles
    for model in [opus, sonnet, gpt4o, grok]:   # 4 models
        prompt = generate_substrate_prompt(puzzle)
        code = call_model_api(model, prompt)
        save(f"convos/{puzzle}/{model}/iter_1_response.txt", code)
        
        for iter_n in range(2, MAX_ITERS):
            result = validate(puzzle, code)
            if result.passes_3_of_3:
                save_metadata({"solved_at_iter": iter_n})
                break
            feedback = run_feedback_pipeline(puzzle, code)
            save(f"convos/{puzzle}/{model}/iter_{iter_n}_feedback.txt", feedback)
            code = call_model_api(model, feedback)
            save(f"convos/{puzzle}/{model}/iter_{iter_n}_response.txt", code)
```

**Output:** ~120 puzzles × 4 models × ~5 avg iters = ~2400 trajectory pairs.

**Cost:**
- ~150K tokens per trajectory (puzzle×model)
- ~480 trajectories × 150K = ~72M tokens
- Mixed-model API pricing: **~$300-1000** total
- Wall clock: 2-3 days running in parallel

**Engineering:** ~500-1000 lines of orchestration. API keys, rate limiting,
retries, partial-failure recovery. **1-2 weeks of build.**

### Recommendation

**Start with Path B.** It generates ~20K examples in an afternoon for $0 with
no orchestration. v1 dataset doesn't need real trajectories.

**Add Path A in v2** if v1 shows positive signal AND you want the diversity
of real LLM mistake patterns. Even then, don't run on all 2000 puzzles —
~50-120 puzzles is plenty.

---

## What's tractable to actually train

### Open models (recommended starting point)

- **Llama-3-8B / 70B**, **Qwen-2.5-Coder-7B / 32B**, **Mistral**, etc. —
  fully fine-tunable.
- **LoRA / QLoRA** via Unsloth, Together AI, or similar.
- **Compute:** consumer hardware works for 7B; rented GPUs for larger.
- **Time:** weekend project to validate hypothesis on 7B; 1-2 weeks for
  full-scale 70B run.

### Closed models with retail SFT

- **GPT-4o-mini** and **GPT-3.5** support fine-tuning via OpenAI API. Cheap
  to iterate. Smaller capacity than Sonnet, but the gap might be closed for
  ARC-shaped tasks specifically.
- **Anthropic does not offer retail fine-tuning** of Claude models. Sonnet,
  Haiku, Opus — not retail-tunable. Enterprise/partnership path exists but
  isn't accessible to most users.

### What this means

If the goal is "improve a specific Claude model's ARC score," **don't
fine-tune** — invest in prompt + feedback substrate. If the goal is "train a
domain-tuned ARC solver from scratch," use open models or GPT-4o-mini.

---

## Where to actually train (no local GPU required)

You don't need a beefy GPU on your own machine. Cloud GPU options ranked by
beginner-friendliness:

### 1. Google Colab (most beginner-friendly, free tier exists)

- **Browser-based Python notebooks.** No installation.
- **Free tier:** T4 GPU, ~12-hour sessions before disconnect. Enough for 7B
  QLoRA fine-tunes with small datasets.
- **Colab Pro: $10/month.** Better GPUs (A100 sometimes), longer sessions,
  more memory. Recommended once you're past initial validation.
- **Path:** open a Colab notebook → upload `training_data.jsonl` → run a
  ready-made Unsloth fine-tune template → download fine-tuned model.

### 2. Together AI fine-tuning API (no GPU management at all)

- Upload JSONL dataset → pick base model → click "fine-tune."
- Together handles all GPU orchestration.
- **~$5-30 per fine-tune** for a 7B model on 50-100K examples.
- Fastest "I just want a fine-tuned model" path. Less learning, more outcome.

### 3. Modal (good middle ground)

- Write Python; it runs in cloud on whichever GPU you specify.
- **$30 free credits to start.**
- More control than Together; less abstraction than Colab.

### 4. RunPod / Vast.ai (cheapest per-hour, full control)

- Rent literal GPU machine for $0.30-$0.50/hour.
- SSH in like a Linux server, install everything, run scripts.
- **Cheapest sustained training**, but you manage everything.

### Cost ladder (realistic, calibrated to MacBook Air user)

| Setup | Cost | Time | What you get |
|---|---|---|---|
| **Colab free + LoRA 7B + 50K examples** | **$0** | 1 weekend | Validation: does fine-tuning help at all? |
| Colab Pro + LoRA 7B + 200K examples | $10 | 1-2 days | Real v1 candidate |
| Together AI + LoRA 7B + 100K examples | $5-30 | 1 day | Ready-to-use fine-tuned model |
| RunPod + LoRA 32B + 200K examples | $200-500 | 1 day | Larger capacity model |
| RunPod + LoRA 70B + 500K examples | $2-5K | 2-3 days | Sonnet-competitive scale |

**First experiment recommendation: $0 on free Colab.**

---

## First concrete step (cheap validation)

1. **Build `data_generator.py`** for substrate fluency + topology vision +
   property propagation. ~3-4 days of code on your MacBook.
2. **Generate ~50K examples** by running the script on the 2000 ARC puzzles.
   ~1 hour of execution.
3. **Open a Colab notebook** with an Unsloth Llama-3-8B QLoRA template.
4. **Upload `training_data.jsonl`** to Colab.
5. **Train for ~4-8 hours** on the free T4 GPU.
6. **Bake-off the fine-tuned model on 5-10 ARC puzzles** vs base Llama-3-8B
   and vs Sonnet 4.6 baseline.
7. **If signal is positive,** add rule→code + iteration data and scale up.
8. **If signal is null,** the bottleneck isn't capacity — it's prompt design.
   Go back to the prompt substrate.

**Total cost of step 1-7: $0-10.** **Total time: ~1 week.**

This validates the hypothesis cheaply before committing real resources.

---

## Cross-puzzle anti-patterns (rank by frequency, growing list)

These are the failure modes that recur across multiple puzzles. Treat
recurrence as a signal of "high-priority to penalise in fine-tuning."

| Anti-pattern | Puzzles | Severity |
|---|---|---|
| Hardcoded grid dimensions / indices | 8f3a5a89 (multiple models) | High — easy to detect, common |
| Per-cell when cluster-level needed | 8f3a5a89 (Sonnet 8 iters) | High — root cause of small-model ceiling |
| Over-extending scoped fix to global rule | 8f3a5a89 (Sonnet iter 6) | High — explains regression cycles |
| 4-conn defaulted when 8-conn needed | 8f3a5a89 (Sonnet iter 1-4) | Medium — single-flag fix once recognised |
| Generic perimeter framing as default | 8f3a5a89 (Gemini, Opus pre-TIPS) | Medium — pretraining bias |
| No-code response | 8f3a5a89 (Gemini early) | Low — easy prompt fix |
| Identical-code resubmission | 8f3a5a89 (Sonnet iter 4) | Medium — needs validator detection |
| Hardcoded test output as literal grid | 8f3a5a89 (multiple) | High — caught by training-3/3 gate, but wastes iter |

(Extend as catalog grows.)

---

## Cross-puzzle pro-patterns

Behaviours to reinforce during fine-tuning (recurring across models that
solve quickly):

| Pro-pattern | Source |
|---|---|
| Scan for unique-color anchor first | Opus iter 1 (8f3a5a89), Grok iter 2 |
| BFS / flood-fill from anchor as default | Opus, Sonnet (post-TIPS) |
| Classify components before deciding what to do with them | Gemini iter 5 unlock |
| Use substrate vocabulary in narration (`+ = -`) | All models post-substrate-prompt |
| Distinguish edge-touching vs interior for structural elements | All models that solved 8f3a5a89 |
| Prefer 8-connectivity for halo / expansion | Grok iter 3 unlock, Sonnet iter 5 |
| Apply a *condition* on the failing subset, don't rewrite the parent rule | All models that solved without regression |

---

## Open questions

- **What's the minimum substrate fluency dataset size for measurable gain?**
  Hypothesis: 10K examples. Need empirical validation.
- **Does substrate fluency transfer to non-ARC pattern tasks?** If so, the
  notation has broader value. Could test on grid-based reasoning benchmarks.
- **Can iteration meta-skill be trained without thousands of trajectories?**
  Path B (mutation) might be enough; DPO with hundreds of (good_iter, bad_iter)
  pairs is also worth piloting.
- **What's the right substrate alphabet for a fine-tune?** v2 (`. = + - ~`)
  vs proposed extensions (`~_thin`, `+_diagonal`, etc.). Lock in before
  training.

---

## See also

- Per-puzzle notes: `Fine Tuning Strategy/<puzzle_id>.md`
- Lockdown v2 design notes: top-level `README.md` → "Lockdown v2 Findings"
- Substrate prompt: `arc_prompt_generator_v5.py`
- Feedback substrate: `run_feedback.py`, `complete_substrate_feedback.py`
- Mechanistic labeling (data source): `mechanistic_feedback_generator.py`
