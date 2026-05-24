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
  puzzles still train via shorter pair-subset variants. Optionally bump
  `sequence_len: 16384` for rule/mixed to keep them (watch memory).

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
3. **Read the new metrics** and test GPT's predictions:
   - Expect (if under-training was the cause): `substrate_to_output` rises fast,
     `pair_to_substrate` rises meaningfully, **`zero_dot_confusion` drops**,
     **`changed_cell_recall` rises**.
   - **If they improve** → continue the chain (diff_lit → … → mixed), still gating
     each stage's probe.
   - **If changed-recall stays low / zero-dot stays high** → do GPT's Steps 3–4:
     add **dot/zero contrast examples** (tiny synthetic pairs, e.g.
     `111/101/111 → 000` giving T `.../.0./...`) and **oversample sparse/thin-edit
     puzzles** (single cell, thin lines, endpoints, isolated markers) in
     `build_phase1_dataset.py`; regenerate same_lit; retrain.
4. **Do NOT stack stages until same_lit is solid** on the new metrics. same_rule
   was failing because it's reasoning on an alphabet not yet mastered.
5. Longer term: the real verdict is **Phase 2 (code) solve rate**, not Phase-1
   freehand exact-match. Consider gating Phase 1 on cell-accuracy/changed-recall,
   not exact-match.

## Pending decision (left for the user)
Whether to **pre-build Steps 3–4** (dot/zero contrast + sparse oversampling) now
vs wait for the Step-2 metrics. Recommendation: **run Step 2 first** (cheap,
GPT's predictions are testable), add Steps 3–4 only if the metrics show the
specific problems persist — avoids changing the data distribution blindly and
avoids confounding "did epochs or data help."

## Pod / cost facts
- RunPod A100-SXM4-80GB, region **us-wa-1**, **Volume disk** (survives Stop,
  DELETED on Terminate — never click Terminate). Stopped = ~$0.03/hr storage.
- ~80 s/optimizer-step at grad_accum 16; with grad_accum 4 expect more steps,
  ~same wall-clock per epoch (epoch time ~fixed by data size).
- HF backup target repo: `Omnisensai/arc-lora-run2` (subfolder per stage).
