# Scoreboard

Tracks LLM performance on ARC-AGI-2 puzzles solved via the substrate framework.

Each row records how many iterations each model needed to reach training 3/3
(SUBMIT verdict). The `Solver` column links to the canonical Python rule in
`Solvers/` once a generalizable algorithm is extracted.

## Legend

- **Number** = iterations to reach 3/3 training (SUBMIT)
- `—` = not yet attempted
- `DNF` = did not finish within iteration budget
- `WIP N` = currently iterating, on iter N
- **Solver** = filename in `Solvers/` (rule name) once a clean Python solver is extracted

## Puzzles

| Puzzle ID | Substrate prompt | GPT | Claude | Gemini | Grok | Solver |
|---|---|---|---|---|---|---|
| [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [✅](Substrate%20Prompts/8f3a5a89.txt) | **2** ✅ | **2** ✅ | **5** ✅ | **3** ✅ | [seeded_reachable_wall_contouring](Solvers/seeded_reachable_wall_contouring.py) |
| [135a2760](https://arcprize.org/tasks/135a2760) | [✅](Substrate%20Prompts/135a2760.txt) | **4** ✅ | **2** ✅ | **2** ⚠️ | **1** ⚠️ | [periodic_motif_repair](Solvers/periodic_motif_repair.py) |

### 135a2760 notes

- **GPT iter 4**: TRUE SOLVE (training 2/2, test 0 cells off). Code archived as `Solvers/periodic_motif_repair.py`.
- **Claude iter 2**: TRUE SOLVE (training 2/2, test 0 cells off). Iter 1 was a false negative (1/2 training, but test was already 0 cells off). Iter 2 added a `min_votes >= 3` constraint without regressing.
- **Gemini iter 2**: FALSE POSITIVE — passed training 2/2 but 43 cells wrong on test. Hedge iter 3 reduced to 8 cells wrong (still no exact match). Algorithm correct but code under-fit. Hand-grid would have been correct (motivated the dual-candidate hedge).
- **Grok iter 1**: HARDCODED — `if bg == X: output[r][c] = Y` dispatcher. Passed training and test, but algorithm doesn't generalize. Counted as ✅ for scoreboard, NOT added to operation menu.

⚠️ on Gemini and Grok rows = passed framework gate but doesn't reflect substrate-quality intent. See `COMP_PIPELINE_STRATEGY.md` for hedge strategies that mitigate these classes.

## Operation menu

Solvers extracted as named, generalizable operations:

1. **seeded_reachable_wall_contouring** (8f3a5a89) — flood fill from anchor, classify clusters by edge contact, halo with 8-connectivity around reachable boundary-touching clusters.
2. **periodic_motif_repair** (135a2760) — separator-grid panel detection, binary-period search with additive cost (errors + 0.4 × tile_size).

## Update protocol

When running a puzzle through a model:

1. Copy the seed prompt from `Seed Prompts/<puzzle_id>_seed.txt` into a fresh chat with the model.
2. Paste the response into `Pastes/<puzzle_id>_<model>.txt` (R1). The workflow runs `paste_helper.py` and saves artifacts to `Model Results/<Model>/<puzzle_id>/R1.*`.
3. If training partially passes, `F1.txt` is auto-emitted. Paste that into a NEW chat; paste the resulting response into `Pastes/<puzzle_id>_<model>_R2.txt`.
4. Repeat with R3/F2, R4/F3, etc. until SUBMIT or budget exhausted.
5. Update this scoreboard with the iteration count (or DNF).
6. If a clean solver emerges, add it to `Solvers/` and link in the row.
