# Solvers

Deterministic Python solvers for ARC-AGI-2 puzzles, organized by transformation rule.

Each solver is named after the rule it encodes (not the puzzle ID), so the
library grows as a catalog of generalizable transformations. The puzzle ID it
was derived from is recorded in the module docstring.

**Validation gate:** every solver here passes **all training pairs and the test
pair** of its source puzzle, verified by `run_feedback.py`.

## Index

| Rule | Source | One-line description |
|---|---|---|
| [`seeded_reachable_floodfill_trace`](seeded_reachable_floodfill_trace.py) | [8f3a5a89](https://arcprize.org/tasks/8f3a5a89) | Flood-fill from a unique seed; classify wall components into structural (edge-touching, halo'd), interior (preserved without halo), or unreachable (removed); paint a halo on the exposed perimeter of the reachable region. |

## Solver structure

Every solver file follows the same shape:

```python
"""
Puzzle: <id>
Rule name: <snake_case_name>

Transformation rule:
<plain-English statement of what the algorithm does, including every case
the rule must handle. This is the LLM-readable specification of the rule.>

Validation: training N/N + test pass on the official puzzle JSON.
"""

# Named color constants (no magic numbers).
# Helper functions (BFS, etc.) shared across solvers when useful.

def solve(input_grid):
    ...
    return output_grid
```

## Why a catalog

This directory is the foundation for fine-tuning a small model on the
transformation algebra (`+ = - .` plus `~`). Each solver is a worked example
of how a substrate-encoded rule maps to executable Python. The set grows
incrementally; we don't add a solver until it clears the validator on its
source puzzle.
