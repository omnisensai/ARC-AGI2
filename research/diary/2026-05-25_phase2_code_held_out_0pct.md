# 2026-05-25 — Phase 2 (code-solver) held-out eval: 0% generalization

## Headline

| Set | n (same-size) | pass@2 | buckets |
|---|---|---|---|
| api_eval (held out from all training) | 34 | **0%** | 34 wrong_training, 0 correct, 0 wrong_test |
| training puzzles (sanity, memorized) | 5 | 80% (4/5) | proves adapter applied + reproduces targets |

Adapter: `Omnisensai/arc-lora-run2/phase2_code` (Qwen2.5-7B + LoRA r32/a64, 3 epochs, final train loss ~0.005). Eval: `run_phase2_eval_local.py` (transformers+peft, no vLLM), `--no-test-input`, temp 0.7, pass@2, functional scoring (exec solve() vs ground truth).

## The number is trustworthy (every measurement bug ruled out)

This took a long debugging chain; recording so we don't re-litigate:
- **Adapter applied** — 196 LoRA modules bound, `lora_B` norm ~1.17 (not zero).
- **Chat template** — the first ~0% run used the *base* tokenizer (wrong template) → OOD prompt → garbage. Fixed by loading the adapter's pinned `tokenizer_config.json`. Sanity then went 0→4/5 on training puzzles, proving the fix.
- **Validator sane** — known-correct training target → train_pass+test_pass True; grids_eq verified (identical True, off-by-one/wrong-dims False).
- **Training labels correct** — disproven as a bug by memorization itself: the model reproduces training solvers, which is impossible unless loss was on the assistant code.
- **Training data sound** — 100/100 sampled targets reproduce all their pairs (train+test).
- **Prompt format** — eval prompt is byte-identical to training (INPUT/T blocks + `Write def solve(input_grid):`).

So 0% is a real generalization result, not a pipeline artifact.

## What the model actually writes (read 17 failed solvers)

Every failure is a **genuine, structured, input-derived ARC algorithm** — bounding boxes, 4-/8-connected components, separator bands, color grouping, symmetry/reflection, 3×3 block detection, center-finding. **No hardcoding, no grid literals, no lookups, no memorization.** The AST audit on the 4 *correct* (training) solvers also came back clean.

→ Phase 2 taught **code style/format excellently** but **rule synthesis on unseen puzzles not at all**. The model is a competent *coder* and a failed one-shot *guesser*. It gets **literally 0 pairs** on held-out — its hypotheses are systematically misaligned with the true transformations, not near-misses.

## The regression vs Run 1 (18-24% held-out)

Same base model, similar task, yet Run 2 collapses to 0 where Run 1 got 18-24%. Leading suspects, in priority:
1. **INPUT+T vs input→output.** Run 1 showed before/after grids; Run 2 shows the compact *diff* (T) and drops OUTPUT. The model may anchor on "what changed" and mis-induce, rather than reasoning from actual outputs. Biggest design delta; lead suspect.
2. **Over-memorization.** 3 epochs to 0.005 loss may have made it snap to memorized-shaped hypotheses instead of inducing fresh. Run 1 was undertrained (8% on D) and generalized more — classic undertrained-generalizes / overtrained-memorizes.
3. **pass@k parity.** Confirm whether Run 1's 18-24% was pass@10 vs our pass@2 (partial explanation only — Run 2 is a hard 0, not just lower).

## Next moves (no live pod needed; data on HF)

- **A/B the prompt: input→output vs INPUT+T.** The single highest-value experiment; would require a Phase-2 retrain in the input→output format.
- **Earlier checkpoint / fewer epochs** to test the over-memorization hypothesis.
- **Repair loop (Phase 3).** The failures are runnable, structured near-the-neighborhood code = ideal repair fuel: feed back failing-pair diffs and let the model fix its hypothesis using the train-pair oracle. Won't fix a systematically-misaligned base on its own, but is the natural recovery lever once 1-2 above lift one-shot above zero.

## Artifacts (on HF: `Omnisensai/arc-lora-run2`)
- `phase2_code/` — the adapter (byte-verified).
- `phase2_eval_runs/` — all generations, summaries, funnel.
- `logs/phase2_code_run.log`, `logs/loss_history.txt` — training loss curve.
