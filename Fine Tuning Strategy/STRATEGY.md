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

**Data source:** every iter response across all models on all puzzles. Each
trajectory file is one training example. Currently we have ~50-200 examples
across the bake-off; need to industrialise iter loop to scale to thousands.
Probably better as DPO/RFT preference data than full SFT, given small N.

**This is the most valuable signal you cannot easily get from web data.**
Pretraining doesn't contain "iterate Python solutions to ARC puzzles without
regressing on prior tests."

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
| Substrate fluency | 30% | Low (programmatic) |
| Topology vision | 30% | Low (programmatic) |
| Rule → code synthesis | 20% | Medium (Opus bootstrap + validate) |
| Iteration meta-skill | 15% | High (manual collection + industrialised iter loop) |
| Bug-pattern library | 5% | Medium (per-puzzle case studies) |

**Rationale for substrate at 30%:** it's the lowest-coverage-in-pretraining
skill, so each example carries more information than topology or code (which
have web representation). 30% is a hypothesis; could be 40-50% if substrate
fluency proves to dominate scoring gains.

---

## What's tractable to actually train

### Open models (recommended starting point)

- **Llama-3-8B / 70B**, **Qwen-2.5-Coder-7B / 32B**, **Mistral**, etc. —
  fully fine-tunable.
- **LoRA / QLoRA** via Unsloth, Together AI, or similar: ~$50-200 for a
  small model with ~50K-100K examples; ~$2-5K for 70B-class with ~500K
  examples.
- **Compute:** consumer hardware works for 7B; rented A100s for larger.
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

## First concrete step (cheap validation)

1. **Generate 50K substrate-fluency + topology-vision examples** using
   existing tooling. ~1 day of code.
2. **LoRA fine-tune Qwen-2.5-Coder-7B** via Unsloth on those examples.
   ~$50-200, runs in <1 day on rented GPU.
3. **Bake-off on 5-10 ARC puzzles** vs base model and vs Sonnet 4.6.
4. **If signal is positive,** scale up data (add rule→code, trajectory) and
   model size (32B or 70B).
5. **If signal is null,** the bottleneck isn't capacity — it's prompt design.
   Go back to the prompt substrate.

This is a weekend project to validate the hypothesis cheaply before
committing real resources.

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
  DPO might work with hundreds of (good_iter, bad_iter) pairs. Worth piloting.
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
