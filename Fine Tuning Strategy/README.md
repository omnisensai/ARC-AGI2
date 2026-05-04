# Fine Tuning Strategy

Per-puzzle notes summarizing the **failure modes** observed across LLM
iterations and the **substrate-aligned vocabulary** that helped models
converge. Aggregated across puzzles, this becomes the spec for fine-tuning
a smaller model on the substrate framework.

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
   Claude, Gemini, Grok), including iters-to-solve
3. **Failure modes observed** — categorised list of LLM bugs from this puzzle
4. **What unlocked the fix** — which substrate signal (transformation grid,
   mechanistic cluster analysis, lock-down format, etc.) finally moved the
   model to the correct rule
5. **Fine-tuning takeaways** — specific behaviours to penalise (anti-patterns)
   and reinforce (pro-patterns) when training a smaller model

## Aggregation

When the catalog grows (~10+ puzzles), build a top-level `STRATEGY.md` that
dedups the takeaways across puzzles into a coherent fine-tuning spec:
  - Universal anti-patterns (rank by frequency)
  - Universal pro-patterns
  - Substrate vocabulary frequency map (which terms unlock the most fixes)
  - Recommended training data composition (e.g. 30% wall-classification
    puzzles, 20% symmetry puzzles, etc.)

## Index

| Puzzle | File | Models solved | Failure modes |
|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [8f3a5a89.md](8f3a5a89.md) | GPT (2), Gemini (5) | hardcoded grid, no-code response, generic perimeter, per-cell pruning, missing edge/interior wall split |
