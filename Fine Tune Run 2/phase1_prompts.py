#!/usr/bin/env python3
"""Phase 1 system prompts — single machine-read source of truth.

These are the exact bytes used as the `system` message for every Phase 1
training/probe record, and the exact bytes the eval harness must use at
inference. `build_phase1_dataset.py` and `verify_records.py` both import
`PROMPT_BY_STAGE` from here — there is no second copy to drift from.

The human-readable spec lives in `PROMPTS.md`. Running this file as a
script (`python3 phase1_prompts.py`) asserts that the composed prompts
below match the fenced "System prompt:" blocks in PROMPTS.md byte-for-byte,
so the doc and the code can never silently diverge.

Prompts are assembled from reusable blocks so each legend is defined once:
  _PIXEL_LEGEND_BODY  — same-size T (per-cell)
  _FACTS_LEGEND_BODY  — diff-size T (aggregate)
A stage prompt = shared header (+ optional rule line) + the relevant branch(es).
"""
from pathlib import Path

# --- reusable blocks ---------------------------------------------------------

_HEADER = (
    "Transformation dynamics:\n"
    "T encodes how the INPUT grid becomes the OUTPUT grid."
)

_RULE_LINE = (
    "Each T encodes exactly one transformation rule that applies across all pairs."
)

_SAME_CONDITION = (
    "When INPUT and OUTPUT share [r,c] dimensions, T is per-cell and lossless "
    "— OUTPUT can be rebuilt exactly from INPUT via T."
)

_DIFF_CONDITION = (
    "When INPUT and OUTPUT [r,c] dimensions mismatch, T is aggregate and lossy "
    "— OUTPUT cannot be rebuilt exactly from INPUT via T."
)

_PIXEL_LEGEND_BODY = (
    "  .       INPUT -> OUTPUT cell unchanged\n"
    "  0-9     INPUT -> OUTPUT cell changed to this color"
)

_FACTS_LEGEND_BODY = (
    "  SIZE     H x W -> h x w   with relation tags\n"
    "  BG       in_bg -> out_bg   with relation tag\n"
    "  PALETTE  per-color count change\n"
    "  ROWS     per-row dominant colors + non-bg counts (INPUT and OUTPUT)\n"
    "  COLS     per-column dominant colors + non-bg counts (INPUT and OUTPUT)\n"
    "  BBOX     per-color bounding box (INPUT and OUTPUT)\n"
    "\n"
    "Relation tags for a -> b:\n"
    "  =        a == b\n"
    "  ×N       b = a*N (N>1)\n"
    "  ÷N       a = b*N (N>1)\n"
    "  Δ±N      additive offset b - a\n"
    "  new      a == 0, b > 0\n"
    "  dropped  a > 0, b == 0"
)


def _pixel_block(encoding_header: str) -> str:
    return f"{_SAME_CONDITION}\n\n{encoding_header}\n{_PIXEL_LEGEND_BODY}"


def _facts_block(encoding_header: str) -> str:
    return f"{_DIFF_CONDITION}\n\n{encoding_header}\n{_FACTS_LEGEND_BODY}"


# --- the five stage prompts --------------------------------------------------

# Literacy stages: condition line directly follows the header (no blank line,
# no rule line). Rule stages insert the rule line + a blank line before it.
SAME_LIT = f"{_HEADER}\n{_pixel_block('T encoding (per cell [r,c]):')}"

DIFF_LIT = f"{_HEADER}\n{_facts_block('T encoding (aggregate summary):')}"

SAME_RULE = (
    f"{_HEADER}\n{_RULE_LINE}\n\n"
    f"{_pixel_block('T encoding (per cell [r,c]):')}"
)

DIFF_RULE = (
    f"{_HEADER}\n{_RULE_LINE}\n\n"
    f"{_facts_block('T encoding (aggregate summary):')}"
)

MIXED = (
    f"{_HEADER}\n{_RULE_LINE}\n\n"
    f"{_pixel_block('T encoding when dimensions match (per cell [r,c]):')}\n\n"
    f"{_facts_block('T encoding when dimensions mismatch (aggregate summary):')}"
)


# Stage order is the training order: same-literacy -> diff-literacy ->
# same-rule -> diff-rule -> mixed.
STAGE_ORDER = ["same_lit", "diff_lit", "same_rule", "diff_rule", "mixed"]

PROMPT_BY_STAGE = {
    "same_lit":  SAME_LIT,
    "diff_lit":  DIFF_LIT,
    "same_rule": SAME_RULE,
    "diff_rule": DIFF_RULE,
    "mixed":     MIXED,
}


# --- doc-sync check ----------------------------------------------------------

_DOC = Path(__file__).resolve().parent / "PROMPTS.md"


def _extract_doc_system_prompts(doc_path: Path) -> list:
    """Return, in document order, the contents of every fenced code block
    that immediately follows a `**System prompt:**` line in PROMPTS.md."""
    lines = doc_path.read_text().splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "**System prompt:**":
            # advance to the opening fence
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            if j >= len(lines):
                break
            k = j + 1
            body = []
            while k < len(lines) and not lines[k].startswith("```"):
                body.append(lines[k])
                k += 1
            blocks.append("\n".join(body))
            i = k + 1
        else:
            i += 1
    return blocks


def check_against_doc() -> None:
    """Assert the composed prompts match PROMPTS.md's System prompt blocks,
    in stage order. Raises AssertionError with a precise diff on mismatch."""
    doc_blocks = _extract_doc_system_prompts(_DOC)
    expected = [PROMPT_BY_STAGE[s] for s in STAGE_ORDER]
    assert len(doc_blocks) == len(expected), (
        f"PROMPTS.md has {len(doc_blocks)} System-prompt blocks, "
        f"expected {len(expected)} (one per stage in STAGE_ORDER)."
    )
    for stage, doc_b, exp in zip(STAGE_ORDER, doc_blocks, expected):
        if doc_b != exp:
            # find first differing line for a precise message
            d_lines, e_lines = doc_b.split("\n"), exp.split("\n")
            for n, (dl, el) in enumerate(zip(d_lines, e_lines)):
                if dl != el:
                    raise AssertionError(
                        f"[{stage}] line {n} differs:\n"
                        f"  doc : {dl!r}\n  code: {el!r}"
                    )
            raise AssertionError(
                f"[{stage}] differs in length: "
                f"doc {len(d_lines)} lines vs code {len(e_lines)} lines"
            )


if __name__ == "__main__":
    check_against_doc()
    print("OK: phase1_prompts.py matches PROMPTS.md for all "
          f"{len(STAGE_ORDER)} stages.\n")
    for stage in STAGE_ORDER:
        p = PROMPT_BY_STAGE[stage]
        approx_tokens = len(p) // 4
        print(f"--- {stage}  (~{approx_tokens} tokens, {len(p)} chars) ---")
        print(p)
        print()
