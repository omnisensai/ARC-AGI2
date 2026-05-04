# Solvers

Deterministic Python solvers for ARC-AGI-2 puzzles, organized by transformation rule.

Each solver is named after the rule it encodes (not the puzzle ID), so the
library grows as a catalog of generalizable transformations. The puzzle ID it
was derived from is recorded in the module docstring.

Validation gate: every solver here passes **all training pairs and the test
pair** of its source puzzle.

## Index

| Rule | Source puzzle | File |
|---|---|---|
| `seeded_reachable_floodfill_trace` | [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | [seeded_reachable_floodfill_trace.py](seeded_reachable_floodfill_trace.py) |
