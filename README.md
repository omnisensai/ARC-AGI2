# ARC-AGI-2 Substrate Pipeline

Fine-tuning pipeline for teaching a small model (Qwen-2.5-7B-Instruct) to solve
ARC-AGI puzzles. Built around an explicit **transformation substrate**
representation: a compact symbolic form that makes the per-cell change pattern
of an ARC pair legible to the model.

## Repository structure

```
ARC-AGI2/
├── data/                          puzzle JSONs (1,921 total)
│   ├── arc1_train/  (400)         ARC-AGI-1 training
│   ├── arc1_eval/   (400)         ARC-AGI-1 evaluation (public answers, fair to train on)
│   ├── arc2_train/ (1000)         ARC-AGI-2 training
│   └── arc2_eval/   (121)         ARC-AGI-2 evaluation (the held-out benchmark)
│
├── splits/                        locked manifests
│   ├── baseline_10.json           10 same-size ARC-AGI-2 puzzles, held out forever
│   └── training_universe.json     full universe + train/dev split (seed=42)
│
├── Solvers/                       canonical solver catalog (13 named rules)
│
├── research/
│   ├── agent_corpus/by_puzzle/    master corpus, one file per puzzle
│   ├── Phase1_Substrate_Spec.md   Phase 1 spec (substrate training)
│   ├── Fintune.md                 fine-tune master plan
│   └── README.md / per-puzzle case studies
│
├── legacy/                        archived old-pipeline code + artifacts
│
├── substrate.py                   Phase 1 library (encode/decode/hierarchy)
├── gen_phase1_data.py             Phase 1 SFT generator
├── build_sft_jsonl.py             Phase 2/3 SFT + DPO exporter
├── bulk_collect.py                OpenRouter API runner (Qwen baseline, etc.)
├── build_agent_prompt.py          full-puzzle agent prompt builder
└── keys.env                       (gitignored) API keys
```

## Two "houses" inside the repo

**Pipeline house** (deterministic, reproducible, no network): `substrate.py`,
`gen_phase1_data.py`, `build_sft_jsonl.py`, plus `data/`, `splits/`, `Solvers/`,
`research/agent_corpus/`. Anything here runs from scratch on any laptop and
always produces the same output.

**Lab house** (API-driven, exploratory, network access required):
`bulk_collect.py`, `build_agent_prompt.py`, `keys.env`. Runs API calls against
OpenRouter, produces raw outputs that get curated into the master corpus.

Both houses share `data/`, `splits/`, `Solvers/`, `research/` — those are
read-only reference data for either side.

## Task-tag notation (single-letter system prompts)

Each fine-tuning record uses a one-letter task tag in the system prompt.
Letters are opaque task selectors, chosen for clean inference-time control.
See `research/Phase1_Substrate_Spec.md` and `research/Fintune.md` for the
substrate alphabets.

| Tag | Task | Status |
|---|---|---|
| `A` | pixel substrate encode (input + output → substrate) | Phase 1 |
| `B` | pixel substrate decode (input + substrate → output) | Phase 1 |
| `H` | hierarchy decomposition (grid → `. # S`) | Phase 1 |
| `C` | substrate → code | reserved (Phase 2) |
| `D` | pairs → code | Phase 2 |
| `E` | wrong code + feedback → right code | Phase 3 (corrector) |

## Substrate alphabets

### Pixel substrate (same-size puzzles only, tasks A and B)

| Symbol | Meaning |
|---|---|
| `.` | background unchanged (most common color in input) |
| `=` | non-background cell preserved (output == input) |
| `0`–`9` | output is this color (input != output) |

Lossless: given `(input, substrate)`, the output is uniquely determined.

### Hierarchy substrate (any single grid, task H)

| Symbol | Meaning |
|---|---|
| `.` | most common color in the grid |
| `#` | second most common color |
| `S` | all other colors |

Mechanical frequency-based decomposition. Lossy by design — teaches the model
to separate signal from filler.

## End-to-end workflow

1. **Phase 1 data generation** (no API, ~30s, local):
   ```bash
   python3 gen_phase1_data.py
   ```
   Produces `phase1_train.jsonl` + `phase1_dev.jsonl`.

2. **Master corpus build** (manual + agent-driven):
   - Agents (Claude/GPT/Gemini) write solvers for puzzles → curated into
     `research/agent_corpus/by_puzzle/<puzzle_id>.json` as `right_codes`.
   - 5-judge LLM majority vote names each rule; canonical snake_case name +
     file lands in `Solvers/<name>.py`.
   - Wrong codes (from Qwen runs via `bulk_collect.py`, or intentionally
     weakened agents) get appended to `wrong_codes` per puzzle.

3. **Phase 2 / 3 SFT export** (no API, local):
   ```bash
   python3 build_sft_jsonl.py
   ```
   Produces `phase2_train.jsonl` (puzzle → right_code), `phase3_train.jsonl`
   (puzzle + wrong + feedback → right), and `phase3_dpo.jsonl` (DPO pairs).

4. **Fine-tune** (Colab T4, free):
   - Upload the JSONLs.
   - Attach LoRA to Qwen-2.5-7B-Instruct, train 1 epoch.
   - Save adapter weights.

5. **Eval** (locked):
   - Run the fine-tuned model on `splits/baseline_10.json` puzzles.
   - These 10 puzzles are excluded from every training set (across arc1/arc2
     duplicates too). Their solve rate is the only reliable signal.

## Quick start

```bash
git clone https://github.com/omnisensai/ARC-AGI2.git
cd ARC-AGI2
python3 gen_phase1_data.py          # builds phase1 SFT data, no API needed
python3 build_sft_jsonl.py          # builds phase2/3 SFT data, no API needed
```

To run the OpenRouter baseline (API call, costs pennies):
```bash
cp keys.env.example keys.env
# edit keys.env to add your OPENROUTER_API_KEY
python3 -m pip install requests
python3 bulk_collect.py
```

## Status

- 10 puzzles in the master corpus (`research/agent_corpus/by_puzzle/`)
- 13 named solvers in `Solvers/` (validated, all training + test pairs pass)
- Phase 1 SFT pipeline: shipped + roundtrip-verified
- Phase 2 / 3 SFT exporter: shipped, runs on current corpus
- Fine-tune step: not yet executed
- Baseline measurement: Qwen-2.5-7B raw on the 10 locked eval puzzles, 0/99 correct (see `research/Bulk Collect/`)

## Specs (read these for details)

- `research/Phase1_Substrate_Spec.md` — substrate alphabet, training data shape, validation
- `research/Fintune.md` — overall fine-tune plan, task-tag table, model choice rationale
- `research/agent_corpus/README.md` — master corpus schema and data lineage
- `Solvers/README.md` — canonical solver catalog
