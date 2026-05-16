# Model Results

Per-model, per-puzzle iteration history. This is the dataset we'll use later
to fine-tune small models on substrate-aligned reasoning.

## Folder structure

```
Model Results/
  GPT/
    <puzzle_id>/
      iter_1_response.txt   # raw text returned by the model (code + narrative)
      iter_1_feedback.txt   # substrate feedback fed back into iter 2 (if needed)
      iter_2_response.txt
      iter_2_feedback.txt
      ...
      summary.json          # final outcome: solved/dnf, iter count, total tokens
  Claude/
    <puzzle_id>/
      ...
  Gemini/
    <puzzle_id>/
      ...
  Grok/
    <puzzle_id>/
      ...
```

## summary.json schema

```json
{
  "puzzle_id": "8f3a5a89",
  "model": "GPT",
  "model_version": "gpt-5.x",
  "iterations": 3,
  "verdict": "SUBMIT",
  "training_pairs_passed": 3,
  "final_solver": "seeded_reachable_floodfill_trace"
}
```

`verdict` is one of `SUBMIT`, `DNF`, `WIP`.
