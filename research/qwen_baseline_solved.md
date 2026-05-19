# Qwen-2.5-7B Pre-Fine-Tune Baseline — Solved Puzzles

**Run**: `bulk_collect_runs/20260518_215135_raw`
**Date**: 2026-05-18
**Setup**: 706 unlocked same-size puzzles × 10 runs = 7060 calls, temp=0.7
**Result**: 24 correct runs total (0.3% pass@1), **10 puzzles solved ≥1× (1.4% pass@10)**

## The 10 puzzles Qwen got right

| puzzle_id | pass rate | notes |
|-----------|-----------|-------|
| 68b16354  | 7/10      | strongest — likely simple shift/recolor |
| b1948b0a  | 5/10      | robust |
| c8f0f002  | 5/10      | robust |
| 25ff71a9  | 1/10      | lucky |
| 332efdb3  | 1/10      | lucky |
| 496994bd  | 1/10      | lucky |
| ce22a75a  | 1/10      | lucky |
| d037b0a7  | 1/10      | lucky |
| d511f180  | 1/10      | lucky |
| e9afcf9a  | 1/10      | lucky |

## What this tells us

- Baseline pass@10 = **10/706 = 1.4%**. This is the bar to beat post-fine-tune.
- Qwen has basic grid IO (read/write pixels accurately) — the failures aren't tokenization issues.
- The 3 puzzles with ≥5/10 pass rate suggest Qwen has reliable handling for trivial transformations (shifts, simple recolors). Phase 1 substrate doesn't need to teach those.
- The other 696 puzzles need actual pattern recognition — that's where phase 2/3 training kicks in.

## Win condition

- Post-SFT target: pass@10 ≥ 25% on same-size held-out (~2× current pass@1 ceiling)
- True benchmark: arc2_eval (locked, 114 puzzles) — never used in training
