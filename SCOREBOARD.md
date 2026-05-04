# Scoreboard

Tracks LLM performance on ARC-AGI-2 puzzles solved via the substrate framework.

Each row records how many iterations each model needed to reach training 3/3
(SUBMIT verdict). The `Solver` column links to the canonical Python rule in
`Solvers/` once a generalizable algorithm is extracted.

## Legend

- **Number** = iterations to reach 3/3 training (SUBMIT)
- `—` = not yet attempted
- `DNF` = did not finish within iteration budget
- `WIP` = currently iterating
- **Solver** = filename in `Solvers/` (rule name) once a clean Python solver is extracted

## Puzzles

| Puzzle ID | Substrate prompt | GPT | Claude | Gemini | Grok | Solver |
|---|---|---|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [✅](Substrate%20Prompts/8f3a5a89.txt) | — | — | — | — | [seeded_reachable_floodfill_trace](Solvers/seeded_reachable_floodfill_trace.py) |

## Update protocol

When running a puzzle through a model:

1. Copy the substrate prompt from `Substrate Prompts/<puzzle_id>.txt` into a fresh chat with the model.
2. Save each iteration's response to `Model Results/<Model>/<puzzle_id>/iter_N_response.txt`.
3. Run the validator (`run_feedback.py`) and save the feedback to `Model Results/<Model>/<puzzle_id>/iter_N_feedback.txt`.
4. Repeat until SUBMIT or budget exhausted.
5. Update this scoreboard with the iteration count (or DNF).
6. If a clean solver emerges, add it to `Solvers/` and link in the row.
