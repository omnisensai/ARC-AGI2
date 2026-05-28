# Solver-LoRA Playbook / Spec (PINNED before any dataset build)

Status: **spec only**. Do NOT build the merged dataset or train until this is agreed.
Authority order: this doc > convenience. The biggest danger is hidden ambiguity
(in the data AND in the eval); pin both before building.

## Goal

Train ONE LoRA so that, given ARC-style example pairs, the model emits an
**executable Python solver**:

```python
def solve(input_grid):
    ...
    return output_grid
```

This is a **solver-generation** LoRA, NOT a grid-transduction LoRA. The golden
LoRA is kept as a baseline only.

## Core principles (locked)

1. **T is prompt-side EVIDENCE, not the target output.**
   The per-cell T diff-map (and the diff-size SIZE facts) appear in the *prompt*
   to convey the perceived transformation. The *target* is always solver code.
   Verified: 100% of the current 8,400 micro records target `def solve(...)`,
   0% are raw grids. Never train a record whose answer is a grid.

2. **Joint, balanced training — never sequential staging.**
   One run over a shuffled UNION of micro + real records. The smaller corpus is
   upsampled/weighted to a deliberate ratio (do not use raw counts). Sequential
   micro→real (or real→micro) forgets the other; joint training makes the micro
   primitives a regulariser/scaffold for the harder real puzzles.

3. **Canonical solver ONLY for the first run.**
   One canonical solver per task is a FEATURE here: the model first learns the
   clean invariant skeleton (`infer_T`/`apply_T`). Do NOT inject alternate
   solver styles yet — early style diversity blurs the target. Diversity is a
   later experiment, only if coverage demands it.

4. **Best-of-N is an INFERENCE/eval harness, not a training assumption.**
   Train the model to emit ONE correct solver. Best-of-N (sample K, run each on
   the train pairs, keep one that passes) is a runtime amplifier only — it must
   never be used to justify noisy/loose training targets.

5. **Execution-based eval ONLY.**
   Score by running the generated `solve()` against held-out pairs and checking
   exact grid match. No token-overlap scoring. Always also report the **hardcode
   rate** (AST audit: BIG_LITERAL / EQ_GRID / FINGERPRINT) — reference: raw
   Qwen-2.5-7B-Instruct is 0% solve / 47.5% hardcode.

6. **Inference-time faithfulness guard.**
   At inference, reject any solver that passes the train pairs only by hardcoding
   (same AST audit). Protects against code bias regardless of base model.

7. **The layering thesis is a HYPOTHESIS, not a belief.**
   The substrate goal is: **ARC task = latent operator graph → code.** We claim
   a stack on the way there:
     - Layer 1 — **alphabet** = micro primitives (one rule, clean contract).
     - Layer 2 — **words** = composed synthetic puzzles (2–4 known primitives
       chained, contract still known). **REQUIRED BRIDGE**, not optional.
     - Layer 3 — **sentences** = real ARC puzzles (messy natural composition).
   "Positive transfer between layers" is not assumed — it is *tested* by the
   bucketed eval below. Without Layer 2, alphabet may stay isolated toy skill
   AND sentences may be memorised stylistically without stable operators.

8. **Repair / constraint-checking (Phase D).**
   Train on plausible-but-wrong solvers paired with corrected ones so the model
   learns: *"this solver looks fluent but violates the contract — fix it."*
   This is the antidote to fluent code bias (the 47.5% hardcode reflex on raw
   Instruct). Two implementations possible:
     (a) SFT contrastive — wrong/right pairs in the SFT mix.
     (b) Post-SFT DPO — preference pairs (right preferred over wrong).
   Partial groundwork already exists (`data_sft/phase3_dpo.jsonl`, 7,221 pairs).
   Decision deferred to after run 1 reads, but the contract for the data lives
   here.

## Curriculum policy (resolves a potential contradiction with principle 2)

Principle 2 says "joint, not sequential." That stands. "Phases" of the layering
thesis (atoms → words → sentences → repair) refer to **the conceptual stack**,
not to discrete training stages. If we ever introduce a curriculum, it is
**shifting EMPHASIS within a single joint mix — atoms never disappear** (replay).
Default for run 1: **uniform joint mix**, no curriculum (simpler, lower-risk).
Add curriculum-with-replay only if the bucketed eval shows a specific failure
mode the simpler mix cannot fix. Do not bake speculative complexity into run 1.

## Eval taxonomy (FIVE distinct categories — do not conflate)

The first four buckets test the layering thesis directly; #5 is the orthogonal
extrapolation test (can the model learn a *new* operator from examples).

| # | bucket | what it measures | how to build |
|---|---|---|---|
| 1 | **micro primitive (seen-family, unseen-seed)** | invariant ROBUSTNESS — same operator, new surface form | fresh seeds outside the training seed range for families IN training |
| 2 | **mapped real** | TRANSFER of a primitive to its messy real instances | real puzzles **tagged** as exercising one of our primitives (requires the coverage map) |
| 3 | **composed-known-primitive (synthetic bridge)** | COMPOSITION — chaining trained operators in a new way | new generators that chain 2–4 known primitives (e.g. flood-then-fence, crop-then-flip) |
| 4 | **unmapped real ARC** | TRANSFER to puzzles that do NOT cleanly map to any primitive | real puzzles the coverage map could not tag |
| 5 | **held-out family** *(orthogonal)* | primitive EXTRAPOLATION — can it write a solver for a rule it NEVER saw? | hold a few whole families out of training; test on their tasks |

Decision rule for the layering thesis (buckets 1–4):
- **1, 2, 3 improve together** → layering works; alphabet → words → sentences holds.
- **1 improves, 2 and 3 do not** → micro is isolated toy skill (alphabet stays alphabet).
- **2 and 3 improve, 1 drops** → real training is overwriting primitives (forgetting).
- **Only 4 moves** → memorised style, no operators.

This is the "truth, not vibes" criterion: don't assume layering helped — read the buckets.

## Base model

- Primary: **Qwen-2.5-7B-Instruct** — trusted, fully wired (config, vLLM eval,
  OpenRouter baseline, golden-LoRA comparison), fluent-enough code, honest
  (coherent) failures.
- Coder (Qwen2.5-Coder-7B-Instruct): a **deferred, cheap A/B** — run the same
  baseline through `baseline_bias_eval.py` and compare solve rate AND hardcode
  rate. Switch ONLY if it clearly wins on both. **Before any switch, verify
  pipeline compatibility** (tokenizer, `qwen2` chat template, context length,
  training stack) — do not switch casually if compatibility breaks.

## Build order (gated — only after this spec is agreed)

1. **Primitive coverage map (HARD PREREQUISITE).** Auto-tag every real solver by
   the micro primitive(s) it uses. Without this we cannot split bucket 2
   (mapped real) from bucket 4 (unmapped real), so the layering thesis is
   untestable.
2. **Held-out split.** Designate: unseen-seeds for #1, held-out families for #5,
   mapped-real holdouts for #2, unmapped-real holdouts for #4.
3. **Composed-puzzle generators (Layer 2 — the BRIDGE).** Build a small set of
   composed synthetic generators that chain 2–4 known primitives (e.g.
   flood-then-fence, crop→detect-tile→repair, select-largest→recolor-by-marker
   →move-to-target). Each composed task's canonical solver chains seen
   `infer_T` steps. Required for both training and bucket #3 eval — without it,
   alphabet stays toy.
4. **`mixed_arc_sft_train.jsonl`.** Balanced micro + composed + real, EXCLUDING
   all held-out items. Coverage map drives the balance so each primitive has
   clean (Layer 1), composed (Layer 2), and messy (Layer 3) representation.
5. **Execution-based eval harness** covering all five buckets + hardcode metric.
6. **Train on Qwen-2.5-7B-Instruct; read the buckets** (apply the decision rule
   above to declare whether layering worked).

Yes to the direction; no to building the merged set before the coverage map +
composition layer are in place. "Mixing helps" without the map is a hope;
with the map and the bucketed read, it becomes a testable substrate hypothesis.
