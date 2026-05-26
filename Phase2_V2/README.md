# Phase2_V2 — self-contained latent-T finetune workspace

Everything needed to build, validate, and (later) train/eval the canonical
latent-T solver LoRA lives in this folder. Everything outside it is being
retired to Legacy.

## Layout

```
Phase2_V2/
  Phase2_V2.md                 strategy doc (the plan: INPUT/T examples -> infer_T -> apply_T)
  canonical/                   the verified training corpus
    solvers/                   739 verified ALL-PASS canonical solvers (one .py per golden_train id)
    _tasks/                    740 per-puzzle data files {puzzle_id, train[], test[]}
    _validation.json           per-solver verdict (status / pass X/Y / audit flags)
    _anomaly/                  quarantined puzzles NOT in the corpus (1b8318e3, see NOTE.txt)
    _AGENT_SPEC.md             the canonical-solver contract agents followed
  scripts/
    validate_canonical.py      the acceptance gate: runs each solver in a subprocess vs
                               ground-truth output for every train+test pair + AST audit
    build_canonical_solvers.py corpus/data builder (regeneration tool; raw puzzle pool is in Legacy)
  splits/                      id-lists (golden_train + the 3 clean held-out + canonical_build)
  Locked_Eval/                 clean held-out eval puzzles — NEVER train on these (see MANIFEST.txt)
```

## Corpus status

739 / 740 golden_train ids have a verified canonical solver
(`solve -> infer_T -> apply_T`, exact on all train+test pairs, no hardcoding).
The 1 gap is `1b8318e3`, quarantined in `canonical/_anomaly/` (self-contradictory
train data — unsolvable at 4/4).

Re-verify any time:

```
python3 Phase2_V2/scripts/validate_canonical.py
# corpus: 740 target | 739 solvers written | accepted 739 | rejected 0 | TODO 1
# (TODO 1 = the quarantined anomaly, intentionally not in the folder)
```

## Still to build (per Phase2_V2.md §10)

The latent-T SFT dataset builder + train/eval/probe scripts are not yet written:
`build_phase2_latentT_code.py`, `audit_canonical_shape.py`,
`run_phase2_latentT_probe.py`, and the axolotl configs.
