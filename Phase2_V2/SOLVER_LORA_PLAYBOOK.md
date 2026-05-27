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

## Eval taxonomy (FOUR distinct categories — do not conflate)

| # | category | what it measures | how to build |
|---|---|---|---|
| 1 | **seen-family, unseen-seed** | invariant ROBUSTNESS — same operator, new surface form | generate fresh seeds (outside the training seed range) for families that ARE in training |
| 2 | **held-out family** | primitive EXTRAPOLATION — can it write a solver for an operator whose RULE it never trained on? | hold a few whole families OUT of training; test on their tasks |
| 3 | **composed (known primitives, new combination)** | COMPOSITION — chaining trained operators in a new way | build composed tasks (e.g. flood-then-fence, crop-then-flip) whose solver composes seen `infer_T` steps. **NOT YET BUILT.** |
| 4 | **real ARC-like** | TRANSFER to messy natural tasks | held-out real-corpus puzzles (and locked_arc2_eval) |

Note: #2 (held-out family) is NOT composition — it is operator extrapolation.
Composition (#3) specifically requires *known* primitives recombined. These are
different capabilities and must be reported separately.

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

1. Build the held-out split FIRST (decide which families are #2, generate the
   unseen seeds for #1, designate real holdout for #4).
2. Build composed-puzzle generators for #3.
3. Build `mixed_arc_sft_train.jsonl` (balanced micro + real, EXCLUDING all
   held-out families/puzzles).
4. Build the execution-based eval harness covering all four categories +
   hardcode metric.
5. Train on Qwen-2.5-7B-Instruct; measure all four categories.

Yes to the direction; no to building the merged set before the eval taxonomy is
pinned.
