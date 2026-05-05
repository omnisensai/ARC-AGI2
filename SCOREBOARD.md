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
| [135a2760](https://arcprize.org/tasks/135a2760) | [✅](Substrate%20Prompts/135a2760.txt) | — | — | — | — | — | — |

## Framework version this scoreboard reflects

**v6 substrate prompt + run_feedback with 6 CODE PITFALLS section.**

Big jump on 8f3a5a89 vs prior v5 baseline:
- Sonnet 4.6 (v5 + lockdown only): 9 iters
- Sonnet 4.5 (v6 + 6 pitfalls): **3 iters** (3x improvement)
- Grok (v5 baseline): 3 iters
- Grok (v6 + 6 pitfalls): **1 iter** (3x improvement)

Same model class, same puzzle. The pitfalls list operates as a checklist:
each iter eliminates one pitfall, exits when checklist empty. No model regression.

## Update protocol

When running a puzzle through a model:

1. Copy the substrate prompt from `Substrate Prompts/<puzzle_id>.txt` into a fresh chat with the model.
2. Save each iteration's response to `Model Results/<Model>/<puzzle_id>/<variant>/iter_N_response.txt`.
3. Run the validator (`substrate/run_feedback.py`) and save feedback to `Model Results/<Model>/<puzzle_id>/<variant>/iter_N_feedback.txt`.
4. Repeat until SUBMIT or budget exhausted.
5. Update this scoreboard with the iteration count (or DNF).
6. If a clean solver emerges, add it to `Solvers/` and link in the row.
