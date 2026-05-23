#!/usr/bin/env python3
"""Verify the byte-level invariants of Phase 1 SFT records.

Runs against the committed .jsonl / .jsonl.gz files for all five
stages (same_lit / diff_lit / same_rule / diff_rule / mixed). Exits
non-zero on the first violation.

Expected system prompts are imported from phase1_prompts (the single
source of truth), and that module is itself checked against PROMPTS.md
before record verification begins — so doc, code, and data must all agree.

Invariants enforced:

  S1  system content matches the expected system message FOR THIS
      RECORD'S STAGE (provenance.stage_key in
      {same_lit, diff_lit, same_rule, diff_rule, mixed})
  S2  messages array is exactly [system, user, assistant]
  S3  no Qwen2 special tokens in any content
  U1  user content ends with `LABEL:\\n` (a trailing label + newline)
  U2  no trailing space on any line of the user content
  U3  no triple-newline ("\\n\\n\\n") anywhere
  A1  assistant content is non-empty
  A2  no leading/trailing whitespace on the assistant content
  P1  provenance.format is one of the known formats
  P2  provenance has the required keys
  P3  provenance.substrate_type matches the stage filter
       (same -> "same", diff -> "diff", mixed -> "same" or "diff")
"""
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data_sft"
sys.path.insert(0, str(ROOT))
from phase1_prompts import PROMPT_BY_STAGE, STAGE_ORDER, check_against_doc  # noqa: E402

FILES = [
    f for stage in STAGE_ORDER for f in (
        DATA / f"phase1_{stage}_train.jsonl.gz",
        DATA / f"phase1_{stage}_probe.jsonl",
    )
]

KNOWN_FORMATS = {
    "pair_to_substrate",
    "substrate_to_output",
    "multi_pair_to_rule",
    "test_substrate_prediction",
    "direct_output_grid",
}

REQUIRED_PROV_KEYS = {"format", "stage", "stage_key", "bucket", "puzzle_id",
                      "sources", "substrate_type", "d4_op",
                      "color_perm_seed", "pair_subset"}

QWEN_SPECIAL_RE = re.compile(
    r"<\|im_(start|end)\|>|<\|object_ref_(start|end)\|>|"
    r"<\|box_(start|end)\|>|<\|quad_(start|end)\|>|"
    r"<\|endoftext\|>"
)

TRAILING_LABEL_RE = re.compile(r"\n?[A-Z][A-Z0-9 _]*:\n$")


# Expected system prompts come from the single source of truth.
EXPECTED_BY_STAGE = PROMPT_BY_STAGE

# Which substrate types each stage's records may contain.
ALLOWED_SUBSTRATE = {
    "same_lit":  {"same"},
    "diff_lit":  {"diff"},
    "same_rule": {"same"},
    "diff_rule": {"diff"},
    "mixed":     {"same", "diff"},
}


def violation(file, line_no, code, detail, record):
    print(f"\nFAIL {file.name}:{line_no} [{code}] {detail}")
    print(f"  provenance: {record.get('provenance', {})}")
    raise SystemExit(1)


def open_records(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            yield i, json.loads(line)


def check_record(rec, file, line_no):
    msgs = rec.get("messages")
    if not isinstance(msgs, list) or len(msgs) != 3:
        violation(file, line_no, "S2",
                  f"messages length is {len(msgs) if isinstance(msgs, list) else None}",
                  rec)

    sys_msg, user_msg, asst_msg = msgs

    prov = rec.get("provenance")
    if not isinstance(prov, dict):
        violation(file, line_no, "P2", "provenance missing", rec)
    missing = REQUIRED_PROV_KEYS - set(prov.keys())
    if missing:
        violation(file, line_no, "P2", f"provenance missing keys: {missing}", rec)
    if prov["format"] not in KNOWN_FORMATS:
        violation(file, line_no, "P1", f"unknown format {prov['format']!r}", rec)

    stage_key = prov.get("stage_key")
    if stage_key not in EXPECTED_BY_STAGE:
        violation(file, line_no, "P2",
                  f"unknown stage_key {stage_key!r}", rec)

    if sys_msg.get("role") != "system" or sys_msg.get("content") != EXPECTED_BY_STAGE[stage_key]:
        violation(file, line_no, "S1",
                  f"system content does not match expected for stage "
                  f"{stage_key!r} (first 80 chars: "
                  f"{sys_msg.get('content', '')[:80]!r})",
                  rec)
    if user_msg.get("role") != "user":
        violation(file, line_no, "S2", "messages[1].role != user", rec)
    if asst_msg.get("role") != "assistant":
        violation(file, line_no, "S2", "messages[2].role != assistant", rec)

    for label, content in (("system", sys_msg["content"]),
                           ("user",   user_msg["content"]),
                           ("asst",   asst_msg["content"])):
        if QWEN_SPECIAL_RE.search(content):
            violation(file, line_no, "S3",
                      f"qwen2 special token inside {label}", rec)

    user = user_msg["content"]
    if not TRAILING_LABEL_RE.search(user):
        violation(file, line_no, "U1",
                  f"user content lacks trailing 'LABEL:\\n' "
                  f"(tail: {user[-40:]!r})", rec)
    for ln_idx, ln in enumerate(user.split("\n")):
        if ln != ln.rstrip(" "):
            violation(file, line_no, "U2",
                      f"trailing space on user line {ln_idx}: {ln!r}", rec)
    if "\n\n\n" in user:
        violation(file, line_no, "U3", "triple-newline in user content", rec)

    asst = asst_msg["content"]
    if not asst:
        violation(file, line_no, "A1", "assistant content empty", rec)
    if asst.startswith((" ", "\n", "\t")) or asst.endswith((" ", "\n", "\t")):
        violation(file, line_no, "A2",
                  f"assistant has leading/trailing whitespace", rec)

    # P3: substrate_type must match the stage's allowed set
    sub_type = prov.get("substrate_type")
    allowed = ALLOWED_SUBSTRATE.get(stage_key, set())
    if sub_type not in allowed:
        violation(file, line_no, "P3",
                  f"{stage_key}-stage record has substrate_type {sub_type!r} "
                  f"(allowed: {sorted(allowed)})", rec)


def main():
    # Doc/code sync first: the prompts module must match PROMPTS.md before
    # we trust EXPECTED_BY_STAGE against the data.
    check_against_doc()
    print("OK   phase1_prompts.py matches PROMPTS.md")

    total = 0
    for file in FILES:
        if not file.exists():
            print(f"SKIP {file.name} (does not exist)")
            continue
        n = 0
        for i, rec in open_records(file):
            check_record(rec, file, i)
            n += 1
        total += n
        print(f"OK   {file.name}: {n} records")
    print(f"\nAll invariants hold across {total} records.")


if __name__ == "__main__":
    main()
