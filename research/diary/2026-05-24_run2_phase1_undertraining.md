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
  `zero_dot_confusion` (printed per-format + in JSON), plus a **grid-size split**
  (`small <=10x10` / `large >10x10` / `aggregate`) reporting cell% + changed-recall
  per bucket. **REFRAME (key):** gate Phase 1 on **small-grid understanding**, not
  large-grid freehand exact-match. Past ~10x10 the LLM drifts on *rendering* even
  when the rule is right (operator-confirmed); that drift is the **code path's**
  job, not a Phase-1 failure. So: small-grid cell% high + large-grid low = GOOD
  (understood, move to code). `.`→`K` is a reasoning issue not a symbol issue
  (renaming won't fix "did this cell change to 0 or was it already 0") — contrast
  data is the real lever if needed.
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
- **Probe is SLOW** (~25 s/record, one-at-a-time → a full 200–400 record probe ≈
  1.5 hr/stage; 5 stages ≈ ~6 hr just probing). **For GATE checks use a subset:**
  ```bash
  python3 "Fine Tune Run 2/run_probe.py" --adapter outputs/phase1_<stage> \
    --probe "Fine Tune Run 2/data_sft/phase1_<stage>_probe.jsonl" \
    --limit 80 --max-new-tokens 1500
  ```
  `--limit 80` (enough to gate) + `--max-new-tokens 1500` (T grids are ≤~1000
  tokens; default 4096 lets it ramble) → ~10–15 min instead of ~1.5 hr. Run the
  FULL probe only for the final headline number. (Real fix later: batch the
  generation in run_probe.py, or serve via vLLM.)
- **SPEED/COST**: at default settings Phase 1 ≈ ~13–15 hr train + ~6 hr probe ≈
  ~20 hr (~$30). Cut it ~in half with: (1) the subset-probe above, and (2) drop
  `gradient_checkpointing` on the **8192** stages (same_lit/diff_lit) — 40 GB GPU
  free, ~30% faster; **keep it ON for the 16384 rule/mixed stages** (they need the
  memory). ~80 s/step is dominated by the 7B fwd+bwd + grad-checkpointing, not
  attention, so flash-attn helps ~30%, not 20×. You can run stages one at a time
  (gated); keep the pod UP between them (do NOT stop — restart hits the
  GPU-availability lottery).
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
2. **Train ONLY same_lit** (3 epochs / ~440 steps), then probe (subset = fast gate):
   ```bash
   nohup bash -c '
     source /root/.env_train; cd /workspace/ARC-AGI2
     axolotl train "Fine Tune Run 2/phase1_same_lit_axolotl.yaml" \
     && python3 "Fine Tune Run 2/run_probe.py" --adapter outputs/phase1_same_lit \
          --probe "Fine Tune Run 2/data_sft/phase1_same_lit_probe.jsonl" \
          --limit 80 --max-new-tokens 1500
   ' > /workspace/same_lit.log 2>&1 &
   disown; tail -f /workspace/same_lit.log
   ```
   (No auto-stop — keep the pod UP so you can continue without the restart-GPU
   lottery. Watch for single-digit-ish `s/it` = flash-attn working, ~3 hr train.)
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

   ⚠️ **CRITICAL — `git pull` BEFORE running same_rule / diff_rule / mixed.**
   Those 3 configs are set to **`sequence_len: 16384` + `micro_batch_size: 1`**
   (committed) so the big multi-pair records (~1–2% are >8192 tokens, max ~14.2k)
   are **kept, not dropped**. BUT the live pod was cloned BEFORE that commit, so
   its local rule/mixed configs are still 8192 — if you run them without pulling,
   the big examples get dropped again. So:
   ```bash
   cd /workspace/ARC-AGI2 && git pull origin claude/gifted-mayer-3ITc1
   grep -HE "sequence_len|micro_batch_size" "Fine Tune Run 2/"phase1_{same_rule,diff_rule,mixed}_axolotl.yaml
   # confirm: sequence_len 16384, micro_batch_size 1 for all three
   ```
   (same_lit / diff_lit stay 8192 — they have no over-length records, no pull
   needed for them. Note: 16384 + packing → fewer steps/epoch; if a rule stage
   looks under-trained, bump its `num_epochs` or lower `grad_accum`.)
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

---

## RESOLUTION — 3-epoch same_lit run + held-out probe (2026-05-24)

The more-epochs hypothesis is **confirmed**. Re-ran same_lit at 3 epochs / 444
steps (vs the 1-epoch / ~37-step under-trained run). Trained from base Qwen,
flash-attn, grad_accum 4. Run was SIGKILLed during the checkpoint-400 save by a
**disk-quota-exceeded** condition (the provisioned Volume quota filled; the
optimizer.pt truncated at 335/646 MB, no traceback). The adapter weights for
checkpoint-400 (`adapter_model.safetensors`, 323 MB) were already flushed and
are intact — checkpoint-400 is epoch 2.69, fully usable for inference. Did NOT
reach the final step-444 save; checkpoint-300 (epoch 2.0) is the clean
resume point.

### In-flight eval_loss (leaky 2% carve — convergence signal, not generalization)
    step 100 (ep 0.67): eval_loss 0.0363  ppl 1.037
    step 200 (ep 1.34): eval_loss 0.0104  ppl 1.010
    step 300 (ep 2.01): eval_loss 0.00429 ppl 1.004
    step 400 (ep 2.69): eval_loss 0.00388 ppl 1.004   <- plateaued 300->400
Baseline (step 0, untrained-this-stage): eval_loss 0.5987 ppl 1.82.

### Held-out probe — checkpoint-400, 80 records, greedy, max_new_tokens 1500
(run_probe.py; whole puzzles never trained, no augmentation = the honest metric)

    Overall:  exact 97.5%  |  cell 99.9%   (78/80 exact)

    format|size                     n   exact   cell%  chgR%  chgP%  .0cf%  pass
    pair_to_substrate|same_size    40  100.0%  100.0% 100.0% 100.0%   0.0%  PASS
    substrate_to_output|same_size  40   95.0%   99.8%  99.8%  99.8%   0.0%  PASS

    grid size            n   exact   cell%  chgR%  chgP%  .0cf%
    small(<=10x10)      36  100.0%  100.0% 100.0% 100.0%   0.0%
    large(>10x10)       44   95.5%   99.9%  99.9%  99.9%   0.0%

    Verdict: ALL THRESHOLDS PASSED.

### Reading
- **Memorization fear dismissed.** Held-out (no-augmentation, unseen puzzles)
  generalization is ~perfect. It learned the skill, not a lookup table.
- **Small-grid understanding gate = 100%** (exact + cell + recall). This is the
  verdict metric per the rendering-ceiling framing.
- **`.0cf` = 0.0%** across the board. The `.`-vs-`0` confusion that dominated the
  1-epoch run is GONE. Confirms it was an under-training artifact, not a format
  problem. => `.`->`K` change is NOT needed. Pending decision B is CLOSED (no K).
- The under-training diagnosis (packing collapsing 1 epoch to ~37 steps) was
  correct; 444 steps fixed both the loss and the held-out quality.
- eval_loss plateaued 300->400, and held-out at ckpt-400 is ~ceiling, so ~2-2.7
  epochs is sufficient for a literacy stage. Calibration for rule stages: start
  at 2-3 epochs, watch held-out, don't over-bake.

### Root-cause carry-forward: DISK QUOTA (not OOM)
The kill was `[Errno 122] Disk quota exceeded`, NOT system-RAM OOM. The Volume's
provisioned quota (separate from the 334T MooseFS cluster `df` reports) filled
from accumulated checkpoints + HF cache. **This WILL kill the longer rule stages
at their first checkpoint unless space is freed first.** Before diff_lit:
free quota (delete superseded checkpoint-100/200 and the truncated
checkpoint-400/optimizer.pt; consider lowering save_total_limit), and back up
checkpoint-400's adapter (Run-1 LoRA-loss trauma). Use a NETWORK volume / larger
quota next time.

### Next
1. Free pod disk quota (REQUIRED — else diff_lit dies the same way).
2. Back up checkpoint-400 adapter.
3. Wire checkpoint-400 as the diff_lit input (top-level outputs/phase1_same_lit
   has only the 07:59 pre-save config, NOT the trained weights — point
   diff_lit's lora_model_dir at checkpoint-400, or copy the adapter up).
4. Launch diff_lit (stage 2).

---

## HARDENED LESSON — Stop/Pause is unreliable; back up per stage (2026-05-24)

Confirmed TWICE in one session: a *stopped* pod refused to restart ("GPU no
longer available" / "not enough free GPUs") because a pod (non-network) volume
is tied to one host, and that host's A100 gets taken while you're stopped. So:

- **Do NOT rely on Stop/Pause to save money mid-run.** Treat stopping as
  "probably losing this pod."
- **Durable safety = HF backup after EACH stage** (save_adapter_to_hf.sh,
  byte-verified), NOT stop/resume. If the pod dies, restore the last completed
  stage from HF onto a fresh pod; you lose only the in-progress stage.
- **Operating rule: keep the pod running continuously through the whole chain**
  (diff_lit -> same_rule -> diff_rule -> mixed), running stages back-to-back.
- **Next-run fix: use a NETWORK volume** (host-independent; attaches to any free
  GPU, so stop/restart actually works).

Also discovered the disk-quota saga's real cause: TWO pods existed — work landed
on a **20 GB** pod (constant quota kills) while an empty **100 GB** pod sat
unused. Moving the run to a 100 GB box; restoring stage 1 from HF (the local
same_lit top-level save never completed). Cost of a wrong-sized/duplicate pod:
hours. Verify volume size + that there's only ONE pod before training.

---

## GUARDRAIL — protect passed LoRAs (immutable artifacts)

phase1_same_lit is a precious passed artifact (97.5% exact / 99.9% cell / 0%
dot-zero confusion, held-out parent-level probe, saved on HF). Rule for the rest
of the run:

- **Treat each passed LoRA as immutable.** Continue FROM it; never train INTO
  its dir or overwrite its HF folder.
- Each stage: own output_dir (outputs/phase1_<stage>), own HF subfolder
  (arc-lora-run2/phase1_<stage>); chain via lora_model_dir from the prior stage.
- Restoring an adapter from HF is read-only (hf download) — cannot overwrite it.
- **train -> probe (held-out) -> back up to HF -> only then continue.** Don't
  stack stages blindly; promote a stage only after its probe passes.
- Watch optimizer STEPS, not just epochs (the good same_lit run was ~400 steps).
- Disk: save_only_model + save_total_limit small (the crash was disk quota on a
  20GB volume, not model failure). Now on a 200GB container disk.
- If ever re-training a passed stage, version it (e.g. phase1_same_lit_rerun_v2)
  — do NOT replace the known-good adapter in place.

---

## STAGE 2 — diff_lit training stats (2026-05-24)

Diff-size literacy (facts-T alphabet: SIZE/BG/PALETTE/ROWS/COLS/BBOX). Chained
from same_lit (restored from HF into outputs/phase1_same_lit). Ran on a fresh
200GB pod, container disk /root (the 200GB volume was a glitched RunPod mount —
reported 100% full while empty; preflight auto-fell back to /root).

Config: seq_len 8192, micro_batch 2, grad_accum 4, 3 epochs, lr 1.2e-4 cosine,
save_only_model, save_total_limit 2, flash-attn. 7394 train records (max input
2217 tokens, ZERO dropped at 8192 — no truncation).

### eval_loss curve (leaky 2% carve — convergence signal, not generalization)
    step 100 (ep 1.01):  eval_loss 0.1479  ppl 1.159
    step 200 (ep 2.02):  eval_loss 0.0862  ppl 1.090
    step 294 (ep 2.98):  eval_loss 0.0700  ppl 1.073
    final train_loss 0.1555 | train_runtime 5879s (~98 min) | 294 steps | ~20s/it

### Reading
- Converges cleanly but to a HIGHER floor than same_lit (0.07 vs 0.0038). This
  is EXPECTED, not weakness: facts-T is NOT a 1:1 lossless copy-with-edits like
  pixel-T. It requires COMPUTE-and-summarize (counts, ratios via relate(),
  per-row/col dominants, bounding boxes) over the grid — many independent fields,
  each must be exactly right. Counting/aggregation is intrinsically harder for an
  LLM than copying a changed cell, so the loss floor is naturally higher. The two
  numbers aren't comparable (different target type).
- Pre-train data audit: recomputed the facts block from the raw INPUT/OUTPUT for
  ALL 7394 train + 52 probe records and compared to the trained label — 100%
  match, ZERO mismatches. The facts labels are correct (no corruption); the
  encoder logic was also hand-verified field-by-field on a worked example.

### Backup
HF: Omnisensai/arc-lora-run2/diff_lit (byte-verified, 323,014,168 bytes).
(NB folder naming: stage 1 is phase1_same_lit, stage 2 is diff_lit — passed
different stage-name args; harmless.)

### Held-out probe (run_probe.py, phase1_diff_lit_probe.jsonl, 52 records)

    Overall:  exact 21.2%  |  cell 95.7%   (11/52 exact)
    format|size                    n   exact   cell%   pass
    pair_to_substrate|diff_size   52   21.2%   95.7%   FAIL(threshold artifact)
    (all records bucket = "aggregate"; chgR/chgP/.0cf are N/A for facts blocks)

### Reading — the "almost correct" signature, and it's BENIGN
Low exact (21%) + high cell (95.7%) = strict-cliff vs slope. Pulled per-failure
expected-vs-got line diffs (41 failures). **Every error is a COUNTING/ARITHMETIC
slip. Not one is structural.** Concrete:
  - PALETTE `0 4 -> 24 ×6` -> got `0 4 -> 28 Δ+24`  (input count right; MIScounted
    output 24->28, so relation tag flipped)
  - PALETTE `0 91 -> 0 dropped` -> `0 89 -> 0 dropped`  (off by 2; "dropped" right)
  - PALETTE `4 15 -> 60 ×4` -> `4 14 -> 56 ×4`  (counts off by 1, ×4 STILL right)
  - ROWS/COLS `...4 8 4...` -> `...4 9 4...`  (one per-row non-bg count off by 1)

NEVER wrong: SIZE, BG, field structure, dominant colors, mostly the relations.
The model learned the transformation STRUCTURE perfectly; it just can't COUNT
exactly (165 cells -> says 169). Facts-block analogue of same_lit's positional
drift: comprehension present, LLM-can't-count limit bites on magnitudes. Failures
cluster on big/dense grids — ONE puzzle (2697da3f) = 4 of 6 sampled failures.

### Verdict: diff_lit PASSES on the understanding interpretation. Proceed.
- The 0.90 EXACT-MATCH threshold is the WRONG gate for facts blocks (set for the
  pixel substrate). cell 95.7% + all-structural-correct is the real result;
  "FAIL" is a threshold artifact, not a comprehension gap.
- facts-T is a LOSSY scaffold, not the answer. "165 vs 169" doesn't break
  reasoning about the transform; in Phase 2 CODE EXECUTION is the truth, not the
  model's counts. Model-emitted facts can even be internally inconsistent (count
  28 with tag Δ+24 when 4->28 is ×7) — fine for a scaffold, but DON'T trust
  model-emitted facts as ground truth.
- More SFT will NOT fix this — same limit as freehand-rendering huge grids.
  Diminishing returns; alphabet learned. Don't over-train chasing exact counts.

### TODO / design note (revisit, not now)
facts-T asks for EXACT COUNTS (PALETTE, per-row/col NZ) — the LLM's weakest skill.
Mild tension: we train on labels the model structurally can't reproduce
token-perfectly. Tolerable (lossy + code-validated), but a future facts-T v2
could de-emphasize raw counts in favor of relations/structure (which it gets
right), or drop the longest per-cell count lines on big grids.

---

## STAGE 3 — same_rule training stats (2026-05-25)

Multi-pair RULE INDUCTION on same-size pairs (test_substrate_prediction +
multi_pair_to_rule + literacy carry). Chained from diff_lit. Ran on the 200GB
pod (container disk /root). seq_len 16384, micro_batch 1, grad_accum 4, 3 epochs,
save_only_model. 16,364 train records; max_input_len 9442 (ZERO dropped at
16384 — the seq-len bump from 8192 was justified: longest example > 8192).

### eval_loss curve (leaky 2% carve — convergence, not generalization)
    baseline ep0:  0.8943  ppl 2.446   (untrained-this-stage: rule induction is NEW)
    ep 0.25:       0.2126
    ep 0.50:       0.1755
    ep 1.00:       0.1421
    ep 1.51:       0.1211
    ep 2.01:       0.1073
    ep 2.51:       0.1009
    ep 2.76:       0.0999   <- min
    ep 2.99:       0.1002   (flat; +0.0003 = noise, NOT a rise)
    final train_loss 0.1329 | train_runtime ~25,070s (~6.96 h) | 1191 steps | ~21 s/it

### Reading
- Dropped ~9x from baseline (0.89 -> ~0.10) and PLATEAUED in the last epoch.
  Converged; epoch 3 added little (same diminishing-returns pattern as same_lit).
- The ~0.10 floor is HIGHER than same_lit (0.004) and diff_lit (0.07), and that's
  EXPECTED: rule induction (infer the rule from pairs, predict a held-out T) is
  intrinsically harder than literacy (transcribe a given pair). Higher floor !=
  worse — different, harder task. The high baseline (0.89) confirms the model
  started NOT knowing the task; the drop is the rule-learning signal.
- ~2-2.5 epochs would likely have sufficed (plateau by ep 2.5). Calibration for
  diff_rule/mixed: 2-3 epochs, watch for plateau.
- This is the leaky carve; the held-out probe is the real verdict.

### Backup
HF: Omnisensai/arc-lora-run2/same_rule (byte-verified, 323,014,168 bytes).

### Held-out probe (run_probe.py, phase1_same_rule_probe.jsonl, 302 records)

    Overall: exact 64.6% | cell 95.6% (195/302)  <- MISLEADING; carried by literacy
    format                         n    exact  cell%  chgR%   tests
    substrate_to_output          102   89.2%  99.9%    -      decode T->output (literacy)
    multi_pair_to_rule            26   88.5%  99.7%  99.5%    compute T GIVEN output (transcription)
    pair_to_substrate            102   77.5%  99.4%  98.5%    transcribe T (literacy)
    direct_output_grid            36    5.6%  85.3%    -      freehand full output (render ceiling)
    test_substrate_prediction     36    0.0%  80.1%  34.3%   INFER rule -> predict held-out test T  <-- THE test
    by size: small exact 77.6%/cell 96.8% ; large exact 57.4%/cell 94.9%

### Reading — literacy ACED, true rule-induction FAILED
- The model knows the T language cold: transcribe T (77.5%/99.4%), decode T->output
  (89.2%/99.9%), compute T when the output is shown (multi_pair_to_rule 88.5%). The
  64.6% overall is carried by these.
- But test_substrate_prediction (infer the rule, predict the held-out TEST pair's T
  with NO output given) = 0% exact, and its 80% cell is a MIRAGE: changed_cell_recall
  is 34% -> the model defaults to a near-identity T (mostly '.') and misses 2/3 of the
  actual changes. It is NOT inducing rules and applying them to unseen inputs.
- Reading transformations != inferring them. More training didn't fix it
  (test_substrate_prediction was 0% at 1 epoch too).
- multi_pair_to_rule's 88.5% is transcription, not induction (the trailing OUTPUT is
  shown). Don't mistake it for rule-induction success.

### Why it's not fatal (and half-expected)
The architecture does NOT rely on freehand one-shot T-induction (LLMs' weakest skill).
Rule-application is routed through CODE + execution-validation (write a rule, check vs
the train pairs whose outputs ARE known, repair from the diff) -> far more forgiving of
weak one-shot induction. A weak test_substrate_prediction is consistent with the thesis;
it's WHY Phase 2 exists.

### Lever (the operator's idea, now clearly indicated)
Leave-one-out cycling with the OUTPUT HIDDEN: predict each train pair's T from the
others WITHOUT showing that pair's output (pure induction, N examples/puzzle vs the
single test pair). Overweight this in a same_rule re-train and/or diff_rule/mixed. The
current mix already had test_substrate_prediction at 0.40 yet it stayed 0% -> the
output-bearing formats (multi_pair_to_rule, substrate_to_output) likely let the model
minimize loss via transcription without learning induction.

### Open decision
(a) re-train same_rule with overweighted output-hidden induction cycling before
continuing, vs (b) proceed (diff_rule -> mixed -> Phase 2 code) and let the
code+execution-validation loop enforce rule-application. Leaning: do BOTH — add the
cycling AND smoke-test Phase-2 code to see if validation rescues induction.
