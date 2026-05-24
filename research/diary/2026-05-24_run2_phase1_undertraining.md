# Run 2 Phase 1 — session diary & handoff (2026-05-24)

**Branch:** `claude/gifted-mayer-3ITc1` (also merged to `main` by the user).
**For the next Claude:** read this top-to-bottom, then `Fine Tune Run 2/RUNBOOK.md`
§2.5 (startup pitfalls) and `PROMPTS.md`. Everything below is committed.

---

## TL;DR

We restructured Phase 1 to a clean 5-stage curriculum, debugged the entire
RunPod training stack, and ran a **1-epoch baseline of all stages overnight**.
Result: **the model learned the substrate structure but is under-trained** —
held-out probe exact-match is low (same_lit pair_to_substrate ~2%,
substrate_to_output ~51%; same_rule overall 23%). Failure analysis (and a
concurring GPT review) shows it's **spatial-precision underfit + specific data
gaps**, NOT a language/format failure. The fix is **more optimizer steps on
same_lit first**, judged by **new richer probe metrics**, then targeted data
(dot/zero contrast + sparse-edit oversampling) only if needed. Do **not** stack
stages until same_lit is solid. Pod is **stopped** (not terminated) — adapters
safe on `/workspace`.

---

## Project context (quick)

- Goal: fine-tune **Qwen2.5-7B-Instruct + LoRA** to solve ARC-AGI. Run 1 (similar
  approach) hit **18–24% pass@2** held-out.
- Core thesis: LLMs can't hand-draw exact grids, so the real solve is via **code**
  (`def solve()` run by a validator). The **substrate** (T = transformation rep)
  is a *reasoning scaffold*, not the final answer. Phase 1 = substrate literacy;
  Phase 2 = code; Phase 3 = repair.
- Substrate: same-size pairs → **pixel T** (`.`=unchanged, digit=new color);
  diff-size pairs → **aggregate facts block** (SIZE/BG/PALETTE/ROWS/COLS/BBOX).

## Phase 1 = 5-stage curriculum (this session's restructure, from 4 stages)

```
same_lit  → diff_lit → same_rule → diff_rule → mixed   (one LoRA, chained)
```
- Prompts are a single source of truth: `Fine Tune Run 2/phase1_prompts.py`
  (self-checks against `PROMPTS.md`). `build_phase1_dataset.py` and
  `verify_records.py` import from it.
- ~71k train records, seq_len 8192, sample_packing. Data verified clean
  (72,109 records pass `verify_records.py`; 0 held-out leaks).

---

## What happened this session

### 1. Restructure (done, committed)
4→5 stages, prompts as source of truth, regenerated all data, 5 axolotl configs,
verifier wired to the prompts module. All green.

### 2. The RunPod setup saga (all fixes now in RUNBOOK §2.5)
Fresh bare PyTorch pod → hours lost to a chain of bugs, **all now documented &
scripted** (`Fine Tune Run 2/train_preflight.sh` does them in one command):
- `pip install axolotl` bumps torch 2.4→2.8, **orphans torchvision/torchaudio**
  → `axolotl --help` crashes (`torchvision::nms does not exist`). Fix:
  `pip uninstall -y torchvision torchaudio`.
- axolotl 0.16.1 ships **without `telemetry/whitelist.yaml`** → crash. Fix: opt
  out (`AXOLOTL_DO_NOT_TRACK=1`) + drop the file in.
- `chat_template: qwen2` **not found** in new axolotl → use `tokenizer_default`
  (uses the model's own Qwen2.5 template = our pinned one; train==eval).
- `flash_attention: false` with nothing else → fell back to **eager attention**
  → ~25× slowdown at 8192 ctx. Fix: `pip install flash-attn` (compiles, ~few min,
  works) → `flash_attention: true`. **sample_packing without flash-attn is both
  slow AND numerically off** (eager packed-mask handling gave a wrong baseline
  eval_loss of 3.5; with flash-attn the correct baseline is ~0.58).
- Private-repo `git clone` → **403 with no prompt**; pre-seed credentials.
- HF cache must go to `/workspace` + `HF_HUB_DISABLE_XET=1` (overlay disk small).

### 3. The 1-epoch baseline run (overnight)
Ran `same_lit → … → diff_rule` (mixed killed before training, on purpose). Each
stage trained, probed, attempted HF push. Adapters saved to
`/workspace/ARC-AGI2/outputs/phase1_{same_lit,diff_lit,same_rule,diff_rule}`.

### 4. THE KEY FINDING — under-trained, not broken
- **eval_loss (val carve) looked great** (0.15–0.6) — BUT that's a 2% slice of the
  *training* distribution (and likely sibling-augmentation leaky). It is **NOT a
  generalization metric.** Do not trust it as "the score."
- **Held-out probe (the real metric) is low:**
  - same_lit (foundation): pair_to_substrate **~2%** exact, substrate_to_output **~51%**.
  - same_rule overall **23%**: pair_to_substrate 10.8%, substrate_to_output 52.9%,
    multi_pair_to_rule 15.4%, test_substrate_prediction **0%**, direct_output 2.8%.
- **Failure analysis (inspected ~15 examples, both stages):** the model produces
  the **right structure but not exact pixels**:
  - **Positional drift** — `.2..2..2..` → `.2..2...2.` (stripe off by a column).
  - **Drops sparse/thin edits** — `...2...\n...2...\n.33.` → `.......\n.......\n.33.`
    (kept the obvious `33`, dropped the thin vertical `2`). → **changed-cell recall weak.**
  - **`.` vs `0` confusion** — emits `0` where `.` expected (`.......`→`......0`).
    `.`=unchanged, `0`=changed-to-black; model conflates them.
  - test_substrate_prediction = plausible-but-wrong pattern (reasoning not there at 1 epoch).

### 5. Diagnosis (mine + GPT, in agreement)
- **Primary cause: under-training.** 1 epoch ≈ only ~37–59 optimizer steps because
  `sample_packing` packs ~14 records/sequence → few, fat updates. (Last good run
  was ~422 steps.) Fewer updates = less convergence, even on the same data.
- **Secondary: a freehand-grid spatial-precision ceiling** (LLMs are bad at exact
  2D placement) — which is *why the architecture uses code (Phase 2) for the real
  solve*. So Phase-1 freehand exact-match is partly the wrong gate to obsess over.
- GPT's concurring read: "format ✅, rough pattern ✅, exact placement ❌, dot/0 ❌,
  rule-transfer exactness ❌. Next lever is more same_lit updates + better metrics
  + dot/zero contrast + sparse-edit exactness — NOT Phase 2 yet."

---

## What was changed/committed this session (all pushed)

- `phase1_prompts.py` — single source of truth for the 5 prompts (self-checks doc).
- `build_phase1_dataset.py`, `verify_records.py` — 5-stage, import prompts.
- 5 `phase1_*_axolotl.yaml` — set to: `flash_attention: true`,
  `chat_template: tokenizer_default`, **`num_epochs: 3`**, **`gradient_accumulation_steps: 4`**
  (→ same_lit ~440 steps, in GPT's 300–500 target; ~same wall-clock).
- `run_probe.py` — **added metrics**: `cell_accuracy`, `changed_cell_recall`,
  `zero_dot_confusion` (printed per-format + in JSON). Gating still on exact_match;
  these are the diagnostics for judging "understanding".
- `save_adapter_to_hf.sh` — **fixed the HF-push bug**: strips axolotl's auto
  `README.md` before upload (its dataset-path frontmatter made the Hub reject the
  whole push → all overnight pushes failed; adapters are only on `/workspace`).
- `train_preflight.sh` — **one-command env setup** (all the saga fixes). Run from
  repo root after cloning.
- `tokenizer_config.json` — pinned Qwen2.5 chat template (source of truth).
- RUNBOOK §2.5 — every pitfall above, with fixes + symptom→cause table.

## Known issues still open
- **1-epoch adapters never reached HF** (push bug, now fixed). They're on
  `/workspace` only — fine, they're throwaway baselines.
- **Probe is SLOW** (~0.04 rec/s, ~25 s/record → mixed's 407-record probe ≈ 2.8 hr).
  Speed this up before heavy iteration: batch generation / vLLM / probe a 50-record
  subset.
- **~1–2% of rule/mixed records exceed 8192 tokens** → axolotl **drops** them
  (confirmed in log: "Dropped 15 sequences…"), does NOT truncate (safe). Those
  puzzles still train via shorter pair-subset variants. **RESOLVED:** same_rule /
  diff_rule / mixed now set to `sequence_len: 16384` + `micro_batch_size: 1`
  (1×16384 ≈ 2×8192, ~48 GB, memory-safe). Their max record is ~14.2k tokens, so
  at 16384 **zero records drop** — all big multi-pair examples are trained.
  same_lit / diff_lit stay 8192 (no over-length records). NOTE: 16384 + packing
  yields fewer packed sequences → fewer optimizer steps/epoch; if a rule stage
  looks under-trained, bump its `num_epochs` or drop `grad_accum` further.

---

## NEXT STEPS (do this, in order)

1. **Restart the SAME pod** (RunPod console → blue "Start"; do NOT Terminate —
   that deletes the volume). Then:
   ```bash
   cd /workspace/ARC-AGI2
   git fetch origin && git reset --hard origin/claude/gifted-mayer-3ITc1
   rm -rf outputs/phase1_*          # clean from base, no accidental resume
   bash "Fine Tune Run 2/train_preflight.sh"   # one-command setup, ~10 min, no debugging
   # hf auth login   (if preflight says NOT logged in)
   ```
2. **Train ONLY same_lit** (3 epochs / ~440 steps), then probe:
   ```bash
   axolotl train "Fine Tune Run 2/phase1_same_lit_axolotl.yaml"
   python3 "Fine Tune Run 2/run_probe.py" --adapter outputs/phase1_same_lit \
     --probe "Fine Tune Run 2/data_sft/phase1_same_lit_probe.jsonl"
   ```
3. **Read the new metrics** and apply this DECISION TREE (agreed by Claude+GPT).
   The three failure modes are independent — diagnose by which metric stays bad:

   | After 3-epoch same_lit probe | Interpretation | Action |
   |---|---|---|
   | `zero_dot_confusion` drops sharply | was under-training | **keep `.`**, don't change symbol |
   | `zero_dot_confusion` stays high | real format ambiguity | **`.`→`K`** swap + shrink legend, regen, rerun literacy (decision B) |
   | `changed_cell_recall` stays low, zero_dot fine | drops sparse/thin edits | **add sparse-edit contrast data** (single cell, thin V/H line, diagonal, endpoint, isolated marker); do NOT change symbol |
   | positional drift stays high (low cell_acc on stripes) | spatial precision | **train longer / add spatial-precision contrast**; more steps |
   | all improve (recall↑, zero_dot↓, cell_acc↑, exact↑) | under-training confirmed | **continue the chain** (diff_lit → … → mixed), gating each stage |

   Note: positive prediction if under-training is the cause — `substrate_to_output`
   rises fast, `pair_to_substrate` rises meaningfully, `zero_dot_confusion` drops,
   `changed_cell_recall` rises. Diagnose with `changed_cell_recall`,
   `changed_cell_precision` (not yet implemented — add if useful), `cell_accuracy`,
   `zero_dot_confusion`, `exact_match`.
4. **Do NOT stack stages until same_lit is solid** on the new metrics. same_rule
   was failing because it's reasoning on an alphabet not yet mastered.
5. Longer term: the real verdict is **Phase 2 (code) solve rate**, not Phase-1
   freehand exact-match. Consider gating Phase 1 on cell-accuracy/changed-recall,
   not exact-match.

## Pending decisions (left for the user)

**(A) Pre-build Steps 3–4** (dot/zero contrast + sparse oversampling) now vs
wait for the Step-2 metrics. Recommendation: **run Step 2 first** (cheap, GPT's
predictions are testable), add Steps 3–4 only if the metrics show the specific
problems persist — avoids changing the data distribution blindly and avoids
confounding "did epochs or data help."

**(B) Replace `.` with `K` in the same-size pixel T** (GPT proposal). Rationale:
`.`=keep vs `0`=write-black are easy to conflate; a distinct letter token `K`
for "keep" removes the ambiguity. **Assessment: good but gate it on the metric,
do NOT do it pre-emptively.** Reasons:
  - It only targets the *secondary* failure (`.`/`0` confusion). The dominant
    failures (positional drift, dropped sparse edits) are NOT fixed by `K`.
  - May already be under-training — we now have a `zero_dot_confusion` metric;
    measure it AFTER the more-epochs run before changing the format.
  - Cost: it's a core substrate-format change (substrate.py encode/decode, full
    data regen, prompts, verifier). And `.` gives useful sparsity/salience that
    a dense `K` grid loses.
  - **Rule:** run more-epochs same_lit → if `zero_dot_confusion` stays high,
    THEN do `.`→`K` (+ shrink the legend, per GPT). If it drops, leave it.
  - If implemented: change `encode`/`decode` in `substrate.py` (top of repo),
    update `phase1_prompts.py` legend (e.g. "K = keep, 0-9 = write color; K is
    an operation not a color; 0 is a color not keep"), regen all stages, update
    `verify_records.py`/`run_probe.py` (the `grid_diagnostics` `.`/`0` logic).

## Pod / cost facts
- RunPod A100-SXM4-80GB, region **us-wa-1**, **Volume disk** (survives Stop,
  DELETED on Terminate — never click Terminate). Stopped = ~$0.03/hr storage.
- ~80 s/optimizer-step at grad_accum 16; with grad_accum 4 expect more steps,
  ~same wall-clock per epoch (epoch time ~fixed by data size).
- HF backup target repo: `Omnisensai/arc-lora-run2` (subfolder per stage).

## Operational lessons that bit us AFTER the first run (also worth a RUNBOOK note)
- **A stopped pod may refuse to restart**: "not enough free GPUs on the host
  machine to start this pod." A *Volume disk* is tied to that host, so if the
  host's A100s are taken you're stuck waiting. **Fix: just spin up a NEW pod**
  — everything important is on GitHub (repo, data, configs, scripts); the only
  thing on the old volume is the throwaway 1-epoch adapters + re-downloadable
  Qwen cache. New pod → clone → `train_preflight.sh` → go. **Lesson: use a
  NETWORK volume next time** (host-independent, attaches to any free GPU).
- **Private-repo `git clone` auth**: GitHub does NOT accept the account password
  (removed 2021). The clone prompt's "Password" must be a **PAT** (fine-grained,
  `omnisensai/ARC-AGI2`, Contents:Read), OR just **make the repo public** for the
  clone (fastest; flip back after). Pre-seeding `/workspace/.git-credentials`
  (RUNBOOK P6) avoids the prompt entirely on a persistent volume.
- **Fresh-pod setup is now ONE command** (`bash "Fine Tune Run 2/train_preflight.sh"`)
  — ~15–25 min of *waiting* (axolotl install + flash-attn compile + Qwen
  download), **zero debugging**. The 2-hr saga was bug-discovery; that's done.
