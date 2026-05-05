# Scoreboard

Tracks LLM performance on ARC-AGI-2 puzzles solved via the substrate framework.

Each row records how many iterations each model needed to reach **TRUE SOLVE**
(training 3/3 + test 1/1). The `Solver` column links to the canonical Python
rule in `Solvers/` once a generalizable algorithm is extracted.

## Legend

- **Number** = iterations to reach TRUE SOLVE (training 3/3 + test correct)
- `—` = not yet attempted
- `DNF` = did not finish within iteration budget
- `WIP N` = currently iterating, on iter N
- **Solver** = filename in `Solvers/` (rule name) once a clean Python solver is extracted

## Puzzles

| Puzzle ID | Substrate prompt | GPT | Claude (Opus) | Claude (Sonnet) | Gemini | Grok | Solver |
|---|---|---|---|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [✅](Substrate%20Prompts/8f3a5a89.txt) | **2** ✅ | **2** ✅ | **3** ✅ | **5** ✅ | **1** ✅ | [seeded_reachable_wall_contouring](Solvers/seeded_reachable_wall_contouring.py) |
| [135a2760](https://arcprize.org/tasks/135a2760) | [✅](Substrate%20Prompts/135a2760.txt) | **4** ✅ | — | — | — | — | — |

## Framework version this scoreboard reflects

**v6 substrate prompt + run_feedback with 7 CODE PITFALLS section.**

Pitfall list (canonical, applies to every puzzle):
1. Cluster property tested per cell
2. 4-conn vs 8-conn adjacency
3. 8-neighborhood iteration (diagonal sandwich)
4. Hardcoded grid dimensions
5. Mutating grid while iterating
6. Aliasing / forgetting deep copy
7. Binary reduction loses multi-color info ⚠ (added from 135a2760 GPT run)

Each iter the model walks down the checklist. We've consistently seen:
each iter eliminates one pitfall, framework converges within ≤10 iters.

## Iteration budget reality check

Across every model run on every puzzle so far: **converged within ≤9 iters** (Sonnet 4.6 v5 baseline ceiling). With v6+pitfalls this dropped to ≤4 iters in most cases. This is competitive with public ARC solvers and cheap (~$1.50/puzzle in API costs).

## Update protocol

When running a puzzle through a model:

1. Copy the substrate prompt from `Substrate Prompts/<puzzle_id>.txt` into a fresh chat with the model.
2. Save each iteration's response to `Model Results/<Model>/<puzzle_id>/iter_N_response.py`.
3. Run the validator: `python substrate/run_feedback.py puzzle_<id>.json`
4. Save feedback to `Model Results/<Model>/<puzzle_id>/iter_N_feedback.txt`.
5. Repeat until SUBMIT or budget exhausted.
6. Update this scoreboard with the iteration count (or DNF).
7. If a clean solver emerges, add it to `Solvers/` and link in the row.
