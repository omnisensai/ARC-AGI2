# Closeness Analysis: Run 2 (240-attempt probe on locked arc2_eval)

_Run: 2026-05-22, FT-Run-2-augmented puzzles disabled; this analysis is on the 240-attempt locked-eval probe (`eval_runs/20260522_204417_failure_probe`)._

Companion to [`arc_lora_run1_locked_eval.md`](./arc_lora_run1_locked_eval.md). Same model (`Omnisensai/arc-lora-run1`), same vLLM config, fresh sampling.

## Methodology

The `failure_bucket` labels from `eval_collect_failures.py` distinguish *whether code ran*. The **closeness** classification reorders those same 240 attempts along a *how close was the model to the right rule* axis, using:

- **Exception type** for failed code (e.g. `NameError` = trivial fix; `IndexError` / `TypeError` = logic bug).
- **Cell-accuracy on training pairs** when code ran (≥95% = near-miss, ≥50% = partial rule, <50% = wrong rule).
- **Syntax-error line location** (in last 3 lines = likely token-budget truncation; earlier = structural).

See [`scripts/closeness_analyzer.py`](../../scripts/closeness_analyzer.py) for the exact mapping.

## Results: 240 attempts, full distribution

| Closeness | Count | % | Interpretation |
|---|---|---|---|
| `near_miss` (≥90% cells) | 15 | 6.2% | Model got the rule, off by a handful of cells |
| `partial_rule` (50–89%) | 28 | 11.7% | Right idea, broken execution |
| `wrong_rule_runnable` (<50%) | 16 | 6.7% | Code ran, output is mostly garbage |
| `trivial_fix_repair` | 14 | 5.8% | One-line fix away (e.g. forgot `from collections import ...`) |
| `semantic_bug_repair` | 81 | 33.8% | Real logic bug — `TypeError`, `IndexError`, etc. |
| `exec_other` | 10 | 4.2% | Other exec failures |
| `shape_contract` | 38 | 15.8% | Wrong output shape — model never computed output dims |
| `contract_other` | 4 | 1.7% | Returned non-grid / bad cells |
| `syntax_minor` | 1 | 0.4% | Tiny syntax error near end (truncation-ish) |
| `syntax_major` | 30 | 12.5% | Major parse failure from the start |
| `timeout` | 3 | 1.2% | Algorithmic blowup |

## Split by same-size vs diff-size puzzle

| Closeness | same-size | diff-size | mixed |
|---|---|---|---|
| `near_miss` | **15** | 0 | 0 |
| `partial_rule` | **28** | 0 | 0 |
| `wrong_rule_runnable` | 16 | 0 | 0 |
| `trivial_fix_repair` | 8 | 6 | 0 |
| `semantic_bug_repair` | 61 | 19 | 1 |
| `exec_other` | 7 | 3 | 0 |
| `shape_contract` | **0** | **31** | **7** |
| `contract_other` | 3 | 1 | 0 |
| `syntax_minor` | 0 | 1 | 0 |
| `syntax_major` | 22 | 8 | 0 |
| `timeout` | 2 | 1 | 0 |
| **TOTAL** | **162** | **70** | **8** |

### Key observations

1. **Diff-size puzzles produce ZERO near-misses and ZERO partial-rule attempts.** When the puzzle requires `output.shape != input.shape`, the model has *no recoverable signal*. Either the code crashes (44%), produces wrong-shape output (44%), or produces a syntax error (11%).
2. **Same-size puzzles produce 43 attempts (26.5%) of `near_miss + partial_rule`.** This is the LoRA's actual zone of competence.
3. **`shape_contract` is exclusively a diff-size failure mode.** Of the 38 shape-contract attempts, 31 are pure diff-size and 7 are mixed; zero are same-size.
4. **`semantic_bug_repair` is the largest single bucket (33.8%)** — code that ran but had logic bugs. Of those, 61 (~75%) are same-size puzzles where the model had a flawed but executable idea of the rule.

## Top per-pair exception types

| Exception | Count | Type | Likely root cause |
|---|---|---|---|
| `TypeError` | 113 | semantic | `'int' object is not subscriptable` etc — wrong type assumption |
| `IndexError` | 70 | semantic | off-by-one in grid indexing |
| `NameError` | **33** | **trivial** | **forgot to `import` Counter / deque** |
| `ValueError` | 20 | semantic | bad argument to a function (e.g. `max([])`) |
| `UnboundLocalError` | 16 | trivial-ish | variable used before assignment in a branch |
| `AttributeError` | 10 | semantic | wrong type assumed (e.g. `.tolist()` on a list) |
| `KeyError` | 8 | semantic | missing dict key |
| `TimeoutError` | 6 | — | per-pair 2-sec wall-clock exceeded |
| `ZeroDivisionError` | 3 | semantic | divided by len(comp) when comp is empty |

## Highest-leverage Phase 2 training fixes (ranked by ROI)

### 1. Always-on imports in phase2 training records

**Symptom**: 33 `NameError` + ~half of 16 `UnboundLocalError` = ~40 exec failures of the form "forgot to `from collections import Counter`".

**Fix**: every phase2 assistant body should begin with:
```python
def solve(input_grid):
    from collections import Counter, deque
    H, W = len(input_grid), len(input_grid[0])
    ...
```

**Estimated impact**: -20% on `exec_error` bucket, near-zero training cost.

### 2. Output-shape computation step for shape-changing puzzles

**Symptom**: 38 `shape_contract` attempts (15.8% of the eval). The model initializes `out = [[bg]*W for _ in range(H)]` using INPUT dimensions, then returns it.

**Fix**: phase2 records for shape-changing puzzles should explicitly compute the output shape from training-pair dimensions before constructing the output grid:
```python
def solve(input_grid):
    from collections import Counter
    H_in, W_in = len(input_grid), len(input_grid[0])
    # output shape inferred from training pairs (this puzzle: 9x4)
    H_out, W_out = 9, 4
    output = [[0]*W_out for _ in range(H_out)]
    ...
```

**Estimated impact**: turns the entire `shape_contract` bucket from doomed → fixable. ~16% of eval recoverable. Biggest single unlock.

### 3. Phase 3 corrector training, expanded

**Symptom**: 124 same-size attempts in the `semantic_bug_repair + partial_rule + near_miss + trivial_fix_repair` range — code that's wrong but close. Existing phase3 already does this for the corpus's wrong-codes; the locked-eval probe shows it generalizes.

**Fix**: feed *these* wrong codes into phase3 alongside the corpus ones. Each has:
- `extracted_code` (the wrong code)
- structured feedback in `train_results[]` (per-pair cell_diff, exception_type, diff_map)
- corresponding right code in `research/agent_corpus/by_puzzle/<pid>.json`

**Estimated impact**: with tonight's 11.5k-attempt sweep on the FT-Run-2 puzzles, this becomes ~3000-5000 additional Code Repair training triples.

## Files

- Analyzer: [`scripts/closeness_analyzer.py`](../../scripts/closeness_analyzer.py)
- Raw run: HF dataset [`Omnisensai/arc-lora-eval-runs/eval_runs/20260522_204417_failure_probe/`](https://huggingface.co/datasets/Omnisensai/arc-lora-eval-runs/tree/main/eval_runs/20260522_204417_failure_probe)
