# Agent Corpus

Working data store for the fine-tuning pipeline. Each puzzle has a JSON file
collecting everything we know about it: correct solver implementations, wrong
attempts (with failure-mode annotations), judging votes, and the canonical
rule name.

## Layout

```
research/agent_corpus/
├── by_puzzle/<puzzle_id>.json    # one file per puzzle, the master record
├── batch_001_judged.json         # historical aggregate (kept for provenance)
└── README.md                     # this file
```

## Per-puzzle file schema

```jsonc
{
  "puzzle_id": "3e980e27",
  "source": "arc2_train",
  "consensus": {                     // null until 3+ judges produce same name
    "name": "stamp_template_on_anchor_singletons",
    "desc": "...",
    "majority": "3/5",
    "solver_path": "Solvers/stamp_template_on_anchor_singletons.py"
  },
  "right_codes": [                   // 1+ correct implementations
    {
      "bucket": "correct",
      "exec_error": null,
      "pairs": [...],                // per-pair validation result
      "code": "...",
      "source": "gpt_after_claude_failed",
      "approach": "Connected-components: ..."
    }
  ],
  "wrong_codes": [                   // 0+ wrong implementations
    {
      "bucket": "wrong_test",        // wrong_test | wrong_training | exec_error | no_code
      "pairs": [...],
      "code": "...",
      "source": "claude_agent_R1",
      "failure_mode": "overfit: passes 4/4 training pairs but fails test..."
    }
  ],
  "judging": {                       // 5-judge naming round + tiebreaker if needed
    "votes": [{"name": "...", "desc": "..."}, ...],
    "counts": {"name_a": 3, "name_b": 1, ...}
  }
}
```

## Why per-puzzle (not aggregate)

This is the **master corpus**, not the training data the trainer ingests.

| Master corpus (here) | Training JSONL (derived) |
|---|---|
| `by_puzzle/<pid>.json` | `phase2_train.jsonl`, `phase3_train.jsonl` |
| Holds N right + M wrong codes per puzzle | One line per (prompt, completion) pair |
| Easy to inspect "everything about puzzle X" | What HuggingFace / LoRA / TRL consumes |
| Append-only as new wrong/right codes arrive | Regenerated from master corpus |

`build_sft_jsonl.py` reads `by_puzzle/*.json` and produces the flat training
JSONLs. Don't edit the JSONL directly; edit the per-puzzle files and re-export.

## How records grow

A puzzle's record starts with whatever the first batch produced and grows:

1. Initial batch: ~1 right_code (from Claude agent), 0 wrong_codes.
2. Wrong-code collection pass: bulk_collect.py on Qwen-7B → typically adds
   5-10 wrong codes per puzzle.
3. Cross-model right codes: when GPT or Gemini also solves a puzzle, append
   their code to `right_codes`.
4. Judge consensus: 5 LLM judges name the rule; if 3+ agree, set
   `consensus`; otherwise run a tiebreaker round.
5. Solver lands in `Solvers/<canonical_name>.py` once consensus is reached.

Target data density per puzzle (for the corrector training that follows):
- 2-5 right_codes (diverse algorithmic approaches)
- 5-10 wrong_codes (varied failure modes)

## Source attribution

Every code entry carries a `source` field so we can trace data lineage:

| Source value | Meaning |
|---|---|
| `claude_agent_R1` | First-pass Claude agent (seed prompt, no test answer) |
| `gpt_after_claude_failed` | GPT solving a puzzle Claude failed on |
| `gemini` | Manually-pasted Gemini code |
| `grok` | Manually-pasted Grok code |
| `qwen_baseline` | bulk_collect.py output (typically wrong codes) |
