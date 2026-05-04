# Fine Tuning Strategy

Per-puzzle notes summarizing the **failure modes** observed across LLM
iterations and the **substrate-aligned vocabulary** that helped models
converge. Aggregated across puzzles, this becomes the spec for fine-tuning
a smaller model on the substrate framework.

> **See [STRATEGY.md](STRATEGY.md)** for the cross-puzzle synthesis: the
> 5 skill clusters to train (substrate fluency, topology vision, rule→code,
> iteration meta-skill, bug-pattern library), recommended data mix, what's
> actually fine-tunable, and a concrete first-step (cheap LoRA validation
> on Qwen-2.5-Coder-7B).

## Why per-puzzle

Each puzzle exposes a different shape of LLM mistake. Some are universal
(hardcoded dimensions, no-code responses, per-cell vs per-component
reasoning). Others are puzzle-specific (e.g. confusing 'frame the grid' with
'frame the seeded region'). Tracking them per puzzle shows which mistakes
repeat across puzzles — those are the ones worth aggressively penalising in
fine-tuning.

## File format

Each `<puzzle_id>.md` file contains:

1. **Canonical rule** — what the substrate framework discovered
2. **Per-model arc** — iter-by-iter summary of each model attempted (GPT,
   Claude, Gemini, Grok, Opus, Sonnet), including iters-to-solve
3. **Failure modes observed** — categorised list of LLM bugs from this puzzle
4. **What unlocked the fix** — which substrate signal (transformation grid,
   mechanistic cluster analysis, lock-down format, TIPS worked example, etc.)
   finally moved the model to the correct rule
5. **Fine-tuning takeaways** — specific behaviours to penalise (anti-patterns)
   and reinforce (pro-patterns) when training a smaller model
6. **Direct fine-tune signals** — concrete training examples this puzzle
   contributes to each skill cluster in `STRATEGY.md`

## Aggregation

`STRATEGY.md` aggregates the takeaways across all per-puzzle files:
  - Universal anti-patterns (rank by frequency)
  - Universal pro-patterns
  - Substrate vocabulary frequency map (which terms unlock the most fixes)
  - Recommended training data composition (e.g. 30% substrate fluency,
    30% topology vision, 20% rule→code, 15% iteration, 5% bug library)

Revise `STRATEGY.md` whenever a new per-puzzle file is added or a recurring
pattern crystallises.

## Index

| Puzzle | File | Models solved | Failure modes |
|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [8f3a5a89.md](8f3a5a89.md) | GPT (2), Grok (3), Gemini (5), Opus 4.7 (2), Sonnet 4.6 (9) | hardcoded grid, no-code response, generic perimeter, per-cell pruning, missing edge/interior wall split, 4-vs-8 connectivity, over-extended scoped fix, **cluster-level property tested per cell** ⚠ |
