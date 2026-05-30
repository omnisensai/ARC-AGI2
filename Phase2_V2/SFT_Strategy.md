# SFT Strategy — Qwen-Coder Substrate Training

Foundational document for the new repo. Drop into a fresh repo and use as the
authoritative contract for training, eval, ablations, and discipline.

**Date**: 2026-05-30
**Distilled from**: V1 (Run 2, 24% held-out) + V2 (Run 1, this round)

---

## PART I — THE PLAN

# Qwen-Coder Substrate Training Plan

## Core Principle

The model should not be trained to "solve" ARC puzzles directly.

The model should be trained to infer the latent transformation rule behind the
observed `T` fields.

Execution, validation, and output reconstruction should remain external and
deterministic.

The correct division of labor is:

```text
Qwen-Coder = infer the code pattern that produces T
Python substrate = apply T, validate T, validate output, reject failures
```

The model proposes.

The substrate verifies.

---

## Canonical Architecture

For same-size ARC tasks, each training pair is converted into:

```text
INPUT
OUTPUT
T
```

Where `T` is a per-cell transformation map:

```text
.   = unchanged
0-9 = overwrite this cell with that color
```

Example:

```text
INPUT:
00000
00800
00800
00000

OUTPUT:
00000
00000
00200
00200

T:
.....
..0..
..2..
..2..
```

The model should not produce the final output directly.

The model should write code that infers `T`.

The deterministic substrate then applies `T`.

---

## Target Function Contract

The model writes exactly one function:

```python
def infer_T(input_grid):
    ...
    return T
```

Where `T` must be a sparse dictionary:

```python
{
    (row, col): new_color
}
```

The model must not write:

```python
def solve(input_grid):
    ...
```

The model must not write:

```python
def apply_T(input_grid, T):
    ...
```

The model must not return an output grid from `infer_T`.

The model must only return the changed-cell transformation mask.

---

## Fixed External Executor

The Python substrate owns execution:

```python
def apply_T(input_grid, T):
    out = [row[:] for row in input_grid]
    for (r, c), v in T.items():
        out[r][c] = v
    return out
```

Runtime evaluation:

```python
T = infer_T(input_grid)
output = apply_T(input_grid, T)
```

The model never owns execution.

---

## Training Objective

The training objective is:

```text
Given 2–4 examples of INPUT + T,
write the reusable Python code pattern that infers T for any new input of the same puzzle.
```

The model learns:

```text
INPUT/T examples → latent rule → infer_T code
```

Not:

```text
INPUT/OUTPUT examples → final output
```

This prevents the model from bypassing the transformation layer.

---

## Prompt Format

### System Prompt

```text
You write Python functions that infer latent transformation masks for ARC grids.

Return only Python code.

Write exactly one function:

def infer_T(input_grid):
    ...

The function must return a dict mapping (row, col) to new color.

Do not write solve.
Do not write apply_T.
Do not return an output grid.
Do not explain.
```

### User Prompt

```text
Each pair shows INPUT and T.

T marks how INPUT becomes OUTPUT.
. means unchanged.
0-9 means overwrite with that color.

PAIR 1
INPUT:
...
T:
...

PAIR 2
INPUT:
...
T:
...

PAIR 3
INPUT:
...
T:
...

Write infer_T(input_grid).
```

### Assistant Target

```python
def infer_T(input_grid):
    H, W = len(input_grid), len(input_grid[0])
    T = {}

    # rule-specific logic here

    return T
```

---

## Pair Curriculum

Train with variable evidence counts.

| Pair Count | Purpose                                      |
| ---------- | -------------------------------------------- |
| 1 pair     | simple rule recognition and syntax hardening |
| 2 pairs    | basic generalization                         |
| 3 pairs    | normal ARC-style rule induction              |
| 4+ pairs   | robust abstraction and anti-overfitting      |

Recommended mix:

```text
10% one-pair examples
35% two-pair examples
35% three-pair examples
20% four-or-more-pair examples
```

Evaluation should report scores separately for:

```text
2-pair prompts
3-pair prompts
all-train-pair prompts
```

This reveals how much evidence Qwen-Coder needs.

---

## What Python Should Do Mechanically

The Python substrate should handle everything deterministic:

```text
1. Compute T from known train INPUT/OUTPUT pairs
2. Render T as . + digits
3. Compile generated code
4. Check that infer_T exists
5. Check that infer_T returns a dict
6. Reject output-grid returns
7. Apply T to input_grid
8. Validate predicted T against train T
9. Validate output against train OUTPUT
10. Score test output after deterministic apply_T
```

The model should not learn these mechanics.

The model should only infer the reusable transformation rule.

---

## What Qwen-Coder Should Learn

Qwen-Coder should learn:

```text
1. How to read INPUT/T examples
2. How to identify entities, objects, colors, and spatial relations
3. How to infer the shared transformation rule
4. How to express that rule as infer_T code
5. How to return only sparse changed cells
```

The model should not learn:

```text
1. Direct output construction
2. Arbitrary solve functions
3. apply_T mechanics
4. validation logic
5. final authority over correctness
```

---

## Validation Metrics

Do not evaluate only final ARC output accuracy.

Track separate metrics:

```text
1. Compile rate
2. Runtime pass rate
3. Interface compliance
4. Sparse T validity
5. Direct-output violation rate
6. Train T exact match
7. Train output exact match after apply_T
8. Test output exact match after apply_T
9. Changed-cell precision
10. Changed-cell recall
11. Unchanged-cell preservation
```

The most important metrics are:

```text
T exact match
output exact match after deterministic apply_T
interface compliance
direct-output violation rate
```

---

## Same-Size First

The first Qwen-Coder Infer-T run should include only same-size ARC tasks.

Same-size tasks have a clean T representation:

```text
T grid has same height and width as INPUT.
. means unchanged.
digit means overwrite.
```

Do not mix different-size output tasks in the first run.

Different-size tasks need a separate representation and should be handled later.

Initial target:

```text
same-size ARC → T mask → infer_T code
```

---

## Recommended Training Phases

### Phase 1 — T Ontology Hardening

Train the model on examples where the target is only the T grid.

No Python yet.

Objective:

```text
INPUT + OUTPUT → T
```

Purpose:

```text
Teach that T is not the output.
Teach that dots preserve input cells.
Teach that digits mean overwrite.
Teach sparse transformation representation.
```

---

### Phase 2 — Multi-Pair T Inference

Train:

```text
PAIR 1: INPUT + T
PAIR 2: INPUT + T
PAIR 3: INPUT + T

TEST INPUT:
Return TEST T only.
```

Still no Python.

Purpose:

```text
Teach cross-example rule induction over T fields.
```

This tests the real substrate object before adding code generation.

---

### Phase 3 — infer_T Code Generation

Train Qwen-Coder to write:

```python
def infer_T(input_grid):
    ...
    return T
```

Input evidence remains:

```text
INPUT + T
INPUT + T
INPUT + T
```

Purpose:

```text
Translate learned T-rule inference into executable Python.
```

---

### Phase 4 — Syntax and Contract Hardening

Use many small synthetic examples to stabilize the exact code patterns.

Repeatedly train valid forms like:

```python
for r in range(H):
    for c in range(W):
        v = input_grid[r][c]
```

And:

```python
T[(r, c)] = new_color
```

And:

```python
return T
```

Purpose:

```text
Prevent token-level corruption.
Prevent direct solve shortcuts.
Make the scaffold boring and stable.
```

---

### Phase 5 — Validator Repair Training

Train repair behavior from external validation failures.

Example:

```text
Generated infer_T failed.

Error:
Expected T[(3, 4)] = 2
but the generated T left that cell unchanged.

Repair infer_T only.
Do not write solve.
Do not write apply_T.
```

Target:

```python
def infer_T(input_grid):
    ...
    return T
```

Purpose:

```text
Distill the agent repair loop into the model.
```

---

## Recommended First Serious Run

Use Qwen-Coder as the backbone.

Do not continue from confused V1/V2 checkpoints.

Start fresh with one clean contract.

Recommended staged training:

```text
Stage 1:
10k–50k T-grid examples

Stage 2:
5k–20k multi-pair T inference examples

Stage 3:
2k–10k infer_T Python examples

Stage 4:
1k–5k repair examples
```

Alternative mixed dataset:

```text
40% synthetic T-grid tasks
25% ARC train-pair → T-grid tasks
20% infer_T Python tasks
10% syntax/contract hardening tasks
5% repair tasks
```

The staged approach is cleaner for diagnosis.

---

## Why This Is Different From V1

V1 trained:

```text
INPUT/OUTPUT/T evidence → def solve(input_grid)
```

That allowed the model to bypass T.

The new plan trains:

```text
INPUT/T evidence → def infer_T(input_grid)
```

This forces the model into the substrate role.

It cannot own execution.

It only proposes the transformation mask.

---

## Why This Is Different From Direct ARC Solving

Direct ARC solving asks the model to produce the answer.

Substrate training asks the model to produce a falsifiable transformation field.

The external substrate then checks:

```text
Does the predicted T reconstruct the known train outputs?
Does the inferred rule generalize to test input?
Does the code compile?
Does the function obey the interface?
Does the model stay inside its assigned role?
```

This makes correctness externally grounded.

---

## Final Rule

The model should not be the solver.

The model should be the transformation-rule projector.

Python is the executor.

The validator is the judge.

The substrate owns correctness.

Canonical runtime:

```text
INPUT/T examples → Qwen-Coder writes infer_T
infer_T(input_grid) → sparse T
apply_T(input_grid, T) → output
validator(output, expected) → accept/reject
```

This is the Qwen-Coder substrate training plan.

---

## PART II — LESSONS LEARNED (CONTEXT BEFORE STARTING)

This section captures hard-won lessons from V1 (Run 2, 24% held-out) and V2
(Run 1, this round). Read before training V3 so we don't redo this debugging.

### Evidence baseline

Measured solve rates on 20 same-size ARC puzzles, identical prompt:

| Setup | Solve Rate | Behavior |
|---|---|---|
| Qwen2.5-7B-Instruct (base) | 0/20 | Behavioral collapse: loops, hallucinated dialog, token degeneration |
| Qwen2.5-Coder-7B-Instruct | 0/20 | Fluent Python, always wrong rule, hardcoded color tables |
| V1 LoRA (substrate-curriculum + code) | 24% historical on held-out | Substrate-vocabulary reasoning |

Any positive solve rate is a methodology contribution, not noise. Code training
alone = 0. Instruction tuning alone = 0. The substrate path is the only one
with positive evidence.

### Qualitative validation

V1 produces substrate vocabulary in its code that Coder/Base never produce:
- "Find the noise color... identify horizontal lines"
- "Find bounding box of all 8s... Identify non-8 colored boundary cells (frame colors)... Identify corners... Determine orientation"
- "Find rows that are all zero - separators... For each group, find the 5-ranges"
- "Find separator rows (all 6s)... Bands are between separators... For each band, find the color that appears as a column-block"

This is post-substrate-literacy reasoning. The curriculum installed something real.

### Start from Qwen2.5-Coder-7B-Instruct, NOT base Qwen2.5-7B-Instruct

Coder produces one clean self-contained solver in 20/20 cases.
Base Qwen does it in ~5/20. The other 15+ are multi-solver loops, hallucinated
dialog, token degeneration, leaked shell prompts, gross syntax errors.

Coder's value is OUTPUT DISCIPLINE, not ARC ability. Both score 0 on solve rate
but Coder gets there cleanly. Start from Coder; you only need to train rule
extraction, not output structure.

### Prompt format is load-bearing — pin it byte-for-byte

V1 with V1's prompt → clean Python.
V1 with V2's prompt → garbled output (`inrange`, missing brackets, repetition).

The LoRA is brittle to OOD prompts in a way the base model isn't. Bundle SYSTEM
and prompt-building helpers in ONE Python module imported at BOTH training and
eval time. Save tokenizer alongside every adapter. Reuse chat template byte-for-byte.

### Hyperparameters: V1's recipe beat V2's

| Parameter | V1 (24% held-out) | V2 (worse) | Use in V3 |
|---|---|---|---|
| Base model | Qwen2.5-7B-Instruct | Qwen2.5-7B-Instruct | **Qwen2.5-Coder-7B-Instruct** |
| Learning rate | 0.00012 | 0.0002 | **0.00012** |
| Weight decay | 0.01 | 0.0 | **0.01** |
| Sequence length | 8192 | 4096 | **8192** |
| LoRA rank | 32 | 32 | **64** (bump for capacity) |
| LoRA alpha | (V1 default) | 64 | **128** (2× rank) |
| Sample packing | true | true | true |
| `train_on_inputs` | false | false | false |
| Attention impl (train) | flash-attn | flash-attn | flash-attn |
| Seed | unpinned | unpinned | **pin to 42** |

### Data hygiene — strip leaks before training

V2 trained on 740 canonical solvers. **192/740 had docstring leaks** like:
```python
"""Canonical solver for ARC puzzle 00d62c1b"""
```
V2 memorized these and now hallucinates puzzle IDs at inference time.

Before training, AST + regex scan every training source for:
1. Puzzle-ID strings (`[0-9a-f]{8}`) in comments/docstrings/variable names
2. Hardcoded grids matching any puzzle's input or output
3. Metadata tags ("origin:", "puzzle_id:", "stage:")

Anything that hardcodes a puzzle identity in the target is a leak. Strip or exclude.

Additionally: functionally validate every training target. `exec()` the solver,
run against all train pairs + test pair, exclude any that fail. Training on
broken code teaches broken patterns. Non-negotiable.

### Inference characteristics

| Setting | Value | Why |
|---|---|---|
| Temperature | 0.5 | T=0 (greedy) brittle to backend drift |
| top_p | 0.9 | reasonable default |
| Max new tokens | 2048 | enough for canonical style; bigger wastes time on rambles |
| Beam search | num_beams=4 | catches bad-token cascades for production eval |
| Repetition penalty | 1.0 (off) | hurts code: solvers legitimately repeat patterns |
| no_repeat_ngram | 0 (off) | hurts code: boilerplate repeats are real |

If a trained LoRA is running 50s+/puzzle, something's wrong (OOD prompt, env
drift, or training didn't teach EOS). Fine-tuned models emit EOS fast.

### Failure-mode taxonomy

| Bucket | Meaning |
|---|---|
| PASS | Solver runs, output matches expected |
| WRONG_OUTPUT | Solver runs, wrong output → wrong rule (cognitive) |
| SHAPE_MISMATCH | Solver runs, wrong dimensions → output planning broken |
| RUNTIME_ERROR | Solver crashes → code-emission broken |
| TIMEOUT | Solver runs >3s → infinite loop / quadratic bug |
| EMPTY_OR_INVALID | No code or syntax error → discipline broken |
| HARDCODED | Passes only because answer is hardcoded → leak / memorization |

Watch the RATIO. High WRONG_OUTPUT = wrong rules (methodology problem). High
EMPTY_OR_INVALID = discipline broken (env problem). High HARDCODED = data leak.

---

## PART III — PROMPT + ENVIRONMENT VERSIONING PROTOCOL (NON-NEGOTIABLE)

The two biggest sources of wasted hours in V1 → V2. Concrete protocol below.
If anything in this section is skipped or weakened, the run is contaminated.

### 3.1 Prompt versioning — single source of truth + signature check

**Rule 1: One module. No copy-paste anywhere.**

Create `shared/prompts.py`:

```python
"""V3 prompt module — the canonical source of truth.

Imported by BOTH data builders AND eval scripts. Never copy-paste anything
from this file into another file. Drift = invalidated training.
"""
import hashlib
import json

PROMPT_VERSION = "v3.0.0"   # bump on ANY semantic change to SYSTEM or render

SYSTEM = """You write Python functions that infer latent transformation masks for ARC grids.

Return only Python code.

Write exactly one function:

def infer_T(input_grid):
    ...

The function must return a dict mapping (row, col) to new color.

Do not write solve.
Do not write apply_T.
Do not return an output grid.
Do not explain."""

def render_pairs(pairs):
    """Render a list of (input, T_str) pairs as the USER prompt body."""
    parts = []
    for i, (inp, t) in enumerate(pairs, 1):
        inp_str = "\n".join("".join(str(c) for c in row) for row in inp)
        parts.append(f"PAIR {i}\nINPUT:\n{inp_str}\nT:\n{t}")
    return "\n\n".join(parts)

def build_user_prompt(pairs):
    """Full USER content. The ONLY way data builders or eval scripts assemble USER."""
    header = (
        "Each pair shows INPUT and T.\n\n"
        "T marks how INPUT becomes OUTPUT.\n"
        ". means unchanged.\n"
        "0-9 means overwrite with that color.\n\n"
    )
    return header + render_pairs(pairs) + "\n\nWrite infer_T(input_grid)."

def prompt_signature():
    """Stable hash over SYSTEM + a frozen sample USER. Checkpoints record this.
    Eval refuses to load if its signature doesn't match the checkpoint's."""
    sample_pairs = [
        ([[0, 0], [0, 8]], ".\n.2"),
        ([[1, 0], [0, 1]], "..\n.."),
    ]
    canonical = SYSTEM + "\n\n---\n\n" + build_user_prompt(sample_pairs)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

**Rule 2: Every checkpoint stores `prompt_signature()` at save time.**

Wrap `axolotl train` with a small post-save hook (or add to the training script)
that writes `<checkpoint>/prompt_signature.json`:

```python
import json
from shared.prompts import PROMPT_VERSION, prompt_signature
json.dump(
    {"version": PROMPT_VERSION, "signature": prompt_signature()},
    open(f"{ckpt_dir}/prompt_signature.json", "w"),
)
```

**Rule 3: Eval refuses to run if signatures disagree.**

In every eval script:

```python
from shared.prompts import PROMPT_VERSION, prompt_signature
import json
ckpt_sig = json.load(open(f"{args.adapter}/prompt_signature.json"))
if ckpt_sig["signature"] != prompt_signature():
    raise SystemExit(
        f"PROMPT DRIFT DETECTED.\n"
        f"  checkpoint: {ckpt_sig['version']} / {ckpt_sig['signature']}\n"
        f"  current   : {PROMPT_VERSION} / {prompt_signature()}\n"
        f"  Fix shared/prompts.py to match, or use the matching adapter version."
    )
```

This is non-bypassable. The eval cannot accidentally use a different prompt than
training. This single check would have saved most of V2's debugging.

**Rule 4: Golden tests in CI.**

`tests/test_prompts.py`:

```python
import json
from pathlib import Path
from shared.prompts import SYSTEM, build_user_prompt, prompt_signature, PROMPT_VERSION

def test_signature_stable():
    """Signature must match the committed golden. Bump version + golden together."""
    golden = json.load(open(Path(__file__).parent / "golden_signature.json"))
    assert prompt_signature() == golden["signature"], \
        f"Prompt changed without version bump. Current sig: {prompt_signature()}"
    assert PROMPT_VERSION == golden["version"]

def test_system_contract():
    """SYSTEM must not reference 'solve', must reference 'infer_T'."""
    assert "infer_T" in SYSTEM
    assert "Do not write solve" in SYSTEM

def test_user_format():
    """USER must follow the PAIR N / INPUT / T pattern."""
    out = build_user_prompt([([[0, 1], [1, 0]], "..\n..")])
    assert "PAIR 1" in out
    assert "INPUT:" in out
    assert "T:" in out
    assert "Write infer_T(input_grid)." in out.strip().splitlines()[-1]
```

`tests/golden_signature.json` is committed and updated only with intentional
version bumps:

```json
{"version": "v3.0.0", "signature": "abc123..."}
```

Run `pytest tests/` before every training run. If signature changes without a
version bump, CI fails — you can't ship drifted prompts.

**Rule 5: Save prompts.py into every promoted checkpoint dir.**

```bash
cp shared/prompts.py <checkpoint>/prompts_snapshot.py
```

This is belt-and-suspenders. If the repo evolves but you need to reload an old
checkpoint, the snapshot lets you reproduce the exact training prompts even if
`shared/prompts.py` has moved on.

### 3.2 Environment versioning — lockfile + verify-on-load

**Rule 1: Lockfile committed.**

`requirements.lock` — exact pip freeze, committed to repo. Generated once on a
clean working environment:

```bash
pip freeze | grep -vE "(file:///|pkg_resources)" > requirements.lock
git add requirements.lock && git commit -m "lock environment for V3"
```

Plus a `requirements.txt` with the loose top-level deps for documentation.

**Rule 2: Environment snapshot script.**

`scripts/snapshot_env.py`:

```python
"""Capture exact env state for reproducibility. Run after training a checkpoint."""
import json, subprocess, sys, platform
from pathlib import Path

def snap():
    info = {"python": sys.version, "platform": platform.platform()}
    # Library versions
    for lib in ("torch", "transformers", "peft", "flash_attn", "axolotl",
                "datasets", "accelerate", "bitsandbytes"):
        try:
            mod = __import__(lib)
            info[lib] = getattr(mod, "__version__", "unknown")
        except ImportError:
            info[lib] = None
    # CUDA / cuDNN
    try:
        import torch
        info["cuda"] = torch.version.cuda
        info["cudnn"] = torch.backends.cudnn.version()
        info["torch_compiled_for"] = torch.cuda.get_device_capability()
    except Exception:
        pass
    # GPU info
    try:
        info["nvidia_smi"] = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv"], text=True).strip()
    except Exception:
        pass
    # Pip freeze
    info["pip_freeze"] = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True).strip().split("\n")
    return info

if __name__ == "__main__":
    ckpt_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    snap_data = snap()
    out = Path(ckpt_dir) / "env_snapshot.json"
    json.dump(snap_data, open(out, "w"), indent=2)
    print(f"wrote {out}")
```

Run after every promoted checkpoint:

```bash
python3 scripts/snapshot_env.py outputs/v3_phase1/
```

**Rule 3: Eval verifies env compatibility.**

`scripts/verify_env.py`:

```python
"""Refuse to load a checkpoint if the current env materially differs.

Critical libs (must match exactly): torch, transformers, peft
Important libs (warn if differ): flash_attn, axolotl, accelerate
"""
import json, sys
from pathlib import Path

CRITICAL = ("torch", "transformers", "peft")
IMPORTANT = ("flash_attn", "axolotl", "accelerate", "bitsandbytes")

def verify(ckpt_dir):
    snap_path = Path(ckpt_dir) / "env_snapshot.json"
    if not snap_path.exists():
        raise SystemExit(f"NO env_snapshot.json in {ckpt_dir}. Refuse to load.")
    saved = json.load(open(snap_path))
    from scripts.snapshot_env import snap
    current = snap()
    errors, warnings = [], []
    for lib in CRITICAL:
        if saved.get(lib) != current.get(lib):
            errors.append(f"{lib}: ckpt={saved.get(lib)} != current={current.get(lib)}")
    for lib in IMPORTANT:
        if saved.get(lib) != current.get(lib):
            warnings.append(f"{lib}: ckpt={saved.get(lib)} != current={current.get(lib)}")
    if errors:
        raise SystemExit("ENV MISMATCH (critical):\n  " + "\n  ".join(errors)
                         + "\nFix env or use a matching checkpoint.")
    if warnings:
        print("ENV WARNINGS (proceed but be aware):", file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)

if __name__ == "__main__":
    verify(sys.argv[1])
    print("env OK")
```

Every eval script calls `verify(args.adapter)` before loading the model. No
silent drift.

**Rule 4: Containerize the env.**

`Dockerfile.train`:

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3.11 python3-pip git
WORKDIR /workspace
COPY requirements.lock .
RUN pip install --no-deps -r requirements.lock
# Plus any binary deps (flash-attn often needs special build)
RUN pip install flash-attn==<exact_version> --no-build-isolation
COPY . /workspace/
```

For pod work: build the image once, pin it on a registry, every training run
uses the same container. No "what version of torch did this pod ship with"
mysteries.

**Rule 5: Pre-install all deps in the preflight, before any training/eval.**

Common forgotten installs:
```bash
pip install protobuf sentencepiece  # Qwen tokenizer
pip install accelerate==<pinned>     # axolotl dep
pip install bitsandbytes==<pinned>   # if doing 4-bit
```

Add these to `scripts/preflight.py` so they fail loudly at the start, not 50
minutes into a run.

### 3.3 The two-line discipline summary

**Prompts**: imported, never copy-pasted; signature checked at every eval load.
**Env**: locked, snapshotted into every checkpoint, verified before every load.

If either of these is bypassed, the run is contaminated and the numbers don't count.

---

## PART IV — OTHER ENVIRONMENT / SETUP LESSONS

### Attention implementation drift — mostly secondary

Training: flash-attn. V1 eval: sdpa. V2 eval: eager (after vLLM broke cuDNN).

Initially blamed eager for `inrange` typos. WRONG — that was V1 under V2's OOD
prompt, not attention drift. With V1's own prompt, output was clean (1 typo
across 18 generated solvers).

Prompt-format mismatch dominates attention drift as a cause of corruption. Fix
the prompt first (which §III makes literally impossible to skip). Only suspect
attention if a signature-matched, env-verified run still produces token-level
garbage.

### Preflight discipline

Before any 30+ min run, `scripts/preflight.py` must do:

```python
# 1. Verify deps
# 2. Verify env snapshot against checkpoint
# 3. Verify prompt signature
# 4. Print 1 sample prompt — eyeball it
# 5. Run 1-puzzle eval — verify output is parseable
# 6. Confirm JSONL writer is per-line-flushing
```

ETA from the run script is a faster signal than waiting for final SOLVE RATE.
We burned hours waiting on full runs that were clearly failing at puzzle 5.

### Always JSONL per-line with flush

Per-puzzle write + flush means Ctrl+C preserves data. Always.

### Common pod setup gotchas (preflight should catch these)

- `pip install protobuf sentencepiece` for Qwen tokenizers
- Pod CWD is usually `/workspace`, repo is `/workspace/<repo>` — cd first
- HF download needs correct subfolder name — list first: `hf repo files <repo>`
- Git auth: PAT with `repo` scope, cache 24h: `git config credential.helper 'cache --timeout=86400'`
- Pin git identity at session start: `git config user.email/name`

### Debugging order of operations (DO NOT SKIP)

When a run produces garbage output:

1. **Print the actual prompt being sent.** Eyeball it. (Should never come up if
   §III.1 signature check is wired — but check anyway.)
2. **Print raw model_output** (not extracted_code). Catches leaks, hallucinated
   metadata, structural collapses.
3. **Run at T=0** to remove sampling noise.
4. **Check pip versions vs training-time versions.** (Should never come up if
   §III.2 env verify is wired.)
5. **Verify the adapter loaded.** `print(model.peft_config)` — check target_modules / rank.
6. **Self-consistency test.** Run trained model on training puzzles. If it can't
   reproduce those, rule extraction broken at training time, not inference.

Order matters. Each step is faster than the next. Don't skip 1 to debug 3. Most
of V2's night was wasted by skipping 1 — and most of THAT was avoidable with the
§III prompt signature check.

---

## PART V — REPO STRUCTURE FOR THE FRESH START

Recommended layout:

```
<repo>/
├── README.md                           ← brief, links here
├── SFT_Strategy.md                     ← this file
├── shared/
│   ├── prompts.py                      ← SYSTEM + user prompt builder (canonical)
│   ├── tokenizer_setup.py              ← chat template, special tokens
│   ├── t_encoding.py                   ← compute T from INPUT/OUTPUT, render . + digits
│   ├── apply_T.py                      ← canonical executor (deterministic)
│   └── puzzle_loader.py                ← format-detecting loader
├── canonical/
│   ├── ground_truth_puzzles/           ← clean puzzle JSONs (source of truth)
│   └── puzzles_text_encoded/           ← optional text-format mirror
├── data/
│   ├── build_phase1_T_grids.py         ← INPUT/OUTPUT → T grid (no Python target)
│   ├── build_phase2_multi_pair_T.py    ← multi-pair → test T (no Python target)
│   ├── build_phase3_infer_T_code.py    ← multi-pair → def infer_T (Python target)
│   ├── build_phase4_syntax_hardening.py← small synth examples
│   └── build_phase5_repair.py          ← failed infer_T + error → repaired infer_T
├── train/
│   ├── phase1_T_grids_axolotl.yaml
│   ├── phase2_multi_pair_T_axolotl.yaml
│   ├── phase3_infer_T_code_axolotl.yaml
│   ├── phase4_syntax_hardening_axolotl.yaml
│   └── phase5_repair_axolotl.yaml
├── eval/
│   ├── probe_phase1_T_grids.py         ← INPUT+OUTPUT given, model emits T → exact match
│   ├── probe_phase2_multi_pair_T.py    ← multi-pair given, model emits test T → exact match
│   ├── eval_infer_T_code.py            ← full pipeline: model writes infer_T, substrate runs it
│   └── compare_runs.py
├── scripts/
│   ├── clean_canonical_solvers.py      ← strip leaks (puzzle IDs, hardcoded grids, metadata)
│   ├── validate_canonical_solvers.py   ← exec + check against pairs, exclude failures
│   ├── upload_checkpoint_to_hf.sh
│   └── preflight.py                    ← smoke test before any expensive run
└── splits/
    ├── train_puzzles.txt
    ├── dev_eval_puzzles.txt
    └── frozen_final_puzzles.txt        ← DO NOT TOUCH UNTIL END
```

### One-time setup tasks (in order)

1. **Port canonical solvers** from old repo → `canonical/ground_truth_puzzles/`
2. **Write `shared/t_encoding.py`** — the function that turns INPUT/OUTPUT into T
3. **Write `shared/apply_T.py`** — the canonical executor (deterministic, the contract)
4. **Write `shared/prompts.py`** — SYSTEM + USER builders matching the plan above
5. **Write `clean_canonical_solvers.py`** + run it
6. **Write `validate_canonical_solvers.py`** + run it (excludes broken solvers)
7. **Generate splits**, commit `frozen_final_puzzles.txt`
8. **Build datasets** for phases 1-5 using the cleaned, validated solvers
9. **Write 5 axolotl yaml configs**
10. **Preflight**: 1-step training + 1-puzzle eval before any real run

---

## PART VI — RIGOR & DISCIPLINE

### Pre-registration is non-negotiable

This doc is committed BEFORE training starts. Plan locked. Hyperparams locked.
Splits locked. If we find a reason to change something, we commit the change
with reasoning BEFORE running, never after.

### Per-stage promotion gates

After each phase, evaluate against that phase's specific probe:

| Phase | Probe |
|---|---|
| Phase 1 — T Ontology | Given INPUT + OUTPUT, emit T grid. Exact-match score ≥ 80% to promote. |
| Phase 2 — Multi-Pair T | Given multi-pair INPUT+T, emit TEST T. Exact-match score ≥ 60% to promote. |
| Phase 3 — infer_T Code | Model writes infer_T. Substrate runs it. Train T exact match ≥ 50% to promote. |
| Phase 4 — Syntax Hardening | Direct-output violation rate < 5%. Compile rate ≥ 95%. |
| Phase 5 — Repair | Repair correctly fixes injected errors ≥ 70%. |

Don't move to the next phase until the current phase's probe passes. If a probe
plateaus below threshold, debug the data/training before adding more stages.

### Three eval levels

1. **Probe** — after each phase. Tests that phase's specific skill. Fast (<2 min). Can be looked at freely.
2. **Dev eval** — after promotion. Full solve rate on `dev_eval_puzzles.txt`. Look at to make go/no-go decisions.
3. **Frozen final** — ONCE at end. Solve rate on `frozen_final_puzzles.txt`. The number we report. No re-rolls.

### Validation metrics to log per checkpoint

```text
compile_rate
runtime_pass_rate
interface_compliance_rate
sparse_T_validity_rate
direct_output_violation_rate
train_T_exact_match_rate
train_output_exact_match_rate
test_output_exact_match_rate
changed_cell_precision
changed_cell_recall
unchanged_cell_preservation_rate
```

The 4 that matter most: T exact match, output exact match after apply_T,
interface compliance, direct-output violation rate.

### Ablations (pre-committed)

After the headline V3 run completes, run these in order:

**Must run (defines V3's identity)**:
- V3 full: Coder base, all 5 phases, cleaned data, pinned hyperparams
- V3 minus phases 4+5: tests if syntax hardening and repair matter
- V3 minus phases 1+2: tests if T ontology and multi-pair T inference were necessary
- V3 from Base Qwen: tests if Coder vs Base matters

**If time permits**:
- V3 leak-not-stripped (with the 192 docstring leaks)
- V3 lower rank (32 instead of 64)
- V3 longer training (2× epochs each phase)

**Will NOT run** (decided in advance):
- Different prompt formats — the prompt is in §I, don't bikeshed
- Different LoRA target modules
- Other base models beyond Coder / Base Qwen

### Checkpoint policy

- Save every 1000 steps during each phase
- Keep ALL checkpoints until run is fully evaluated
- End of phase: identify checkpoint with best probe score → "promoted" → next phase init
- Upload promoted checkpoints to HF: `<org>/arc-lora-v3/<phase>`
- Every promoted checkpoint dir includes: weights, tokenizer, pip freeze, axolotl config, chat template, probe results

### Definition of done

V3 is "done" when:
- All 5 phases hit their probe gates
- Dev eval is stable across two seeds
- Frozen final eval is run ONCE
- All artifacts on HF
- This doc has a "Results" appendix with the actual frozen final number

The number we publish is that frozen final score. No re-rolls. If we find a
bug after the frozen run, that's V4.

---

## PART VII — OPEN QUESTIONS (RESOLVE BEFORE TRAINING)

These need answers BEFORE the data builders run:

- [ ] Phase 1 dataset size — 10K, 30K, 50K?
- [ ] Phase 3 dataset size — 2K, 10K?
- [ ] Augmentation policy — D4 × color permutation (42 variants) for which phases?
- [ ] Frozen final split size — 30 (V1's number), 100, more?
- [ ] Eval temperature — pin to 0.5
- [ ] pass@N — pin to pass@1 (clean) or pass@2 (variance)?
- [ ] Per-phase epochs — 1 each? 2 each?
- [ ] Final SYSTEM string — the one in §I is the plan; lock it before data build

---

## PART VIII — STATUS CHECKLIST

### Pre-training
- [ ] Port canonical solvers
- [ ] Write shared/t_encoding.py + apply_T.py
- [ ] Write shared/prompts.py with §I prompts
- [ ] Run clean_canonical_solvers.py
- [ ] Run validate_canonical_solvers.py
- [ ] Generate splits, commit frozen
- [ ] Build phase 1-5 datasets
- [ ] Write 5 axolotl yamls
- [ ] Resolve open questions
- [ ] Preflight 1 step + 1 puzzle

### Training
- [ ] Phase 1 (T ontology) complete + probe ≥ 80%
- [ ] Phase 2 (multi-pair T) complete + probe ≥ 60%
- [ ] Phase 3 (infer_T code) complete + probe ≥ 50%
- [ ] Phase 4 (syntax) complete + violation rate < 5%
- [ ] Phase 5 (repair) complete + repair rate ≥ 70%

### Ablations
- [ ] V3 full
- [ ] V3 minus phases 4+5
- [ ] V3 minus phases 1+2
- [ ] V3 from Base Qwen

### Final
- [ ] Frozen eval ONCE
- [ ] Results appended
- [ ] Artifacts on HF

---

## PART IX — TL;DR

- The model writes `infer_T` only. Python owns `apply_T`, validation, scoring.
- 5 phases: T ontology → multi-pair T → infer_T code → syntax → repair.
- Start from Qwen2.5-Coder-7B-Instruct.
- Pin everything: prompts, tokenizer, hyperparams, env.
- Strip leaks. Validate every training target. No broken code in.
- Frozen final eval is the only number we publish. No re-rolls.
- Methodology is the only known path off 0%. Don't bikeshed; execute.

*End of strategy. Drop into the new repo. Update with results when V3 completes.*
