"""
Feedback diagnostics: classify whether the model is in code-debug or
rule-comprehension phase, and detect specific bug-class fingerprints
from the spatial pattern of output errors.

Used to gate iter-2+ feedback content. Instead of dumping all diagnostics,
the validator picks the feedback type that matches the phase the model is in.
"""

import ast
from collections import Counter, deque
from difflib import SequenceMatcher


def detect_wall_color(input_grid):
    """Most-common non-background color (matches the heuristic model code uses)."""
    counts = Counter(v for row in input_grid for v in row)
    bg = counts.most_common(1)[0][0]
    non_bg = [(c, n) for c, n in counts.items() if c != bg]
    if not non_bg:
        return None
    return max(non_bg, key=lambda x: x[1])[0]


def detect_conn_mismatch(input_grid, expected, actual, wall_color=None):
    """4-conn vs 8-conn adjacency bug in distance/layer-depth computation.

    Fingerprint: error cells have a wall as a diagonal neighbor but NOT as
    a 4-neighbor. Under 4-conn BFS, the path to those cells must "go around"
    the diagonal, so they get assigned a higher depth than they should — and
    the cycling color sequence comes out offset.
    """
    if wall_color is None:
        wall_color = detect_wall_color(input_grid)
    if wall_color is None:
        return None

    H, W = len(input_grid), len(input_grid[0])
    error_cells = [(r, c) for r in range(H) for c in range(W)
                   if expected[r][c] != actual[r][c]]
    if not error_cells:
        return None

    def in_bounds(nr, nc):
        return 0 <= nr < H and 0 <= nc < W

    diag_only = 0
    for r, c in error_cells:
        has_4_wall = any(
            (not in_bounds(r + dr, c + dc)) or input_grid[r + dr][c + dc] == wall_color
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )
        has_diag_wall = any(
            (not in_bounds(r + dr, c + dc)) or input_grid[r + dr][c + dc] == wall_color
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        )
        if has_diag_wall and not has_4_wall:
            diag_only += 1

    ratio = diag_only / len(error_cells)
    if ratio < 0.5:
        return None

    return {
        "bug_class": "connectivity_mismatch",
        "confidence": ratio,
        "fingerprint": (
            f"{diag_only}/{len(error_cells)} error cells are diagonally "
            f"adjacent to a barrier but not 4-adjacent. This is the spatial "
            f"signature of 4-conn vs 8-conn divergence."
        ),
        "suggested_fix": (
            "Your distance/layer BFS likely uses 4-connectivity. Try "
            "8-connectivity for the layer-depth propagation. Keep your "
            "region-detection BFS as 4-conn; only the depth/halo step "
            "needs 8-conn."
        ),
    }


def transformation_count_match(input_grid, expected, actual):
    """Ratio of per-(input_color, output_color) pair counts that match between
    expected and actual outputs.

    When this is ~1.0, the model is producing the right kinds of color
    transformations in the right quantities — only their spatial placement
    is wrong. Strong signal that the rule is right and only code is wrong.
    """
    H, W = len(input_grid), len(input_grid[0])
    expected_pairs = Counter()
    actual_pairs = Counter()
    for r in range(H):
        for c in range(W):
            expected_pairs[(input_grid[r][c], expected[r][c])] += 1
            actual_pairs[(input_grid[r][c], actual[r][c])] += 1
    overlap = sum(min(expected_pairs[k], actual_pairs[k]) for k in expected_pairs)
    total = sum(expected_pairs.values())
    return overlap / total if total else 0


def color_distribution_overlap(expected, actual):
    """Ratio of color-frequency overlap (output palette match)."""
    expected_counts = Counter(v for row in expected for v in row)
    actual_counts = Counter(v for row in actual for v in row)
    overlap = sum(min(expected_counts[c], actual_counts[c]) for c in expected_counts)
    total = sum(expected_counts.values())
    return overlap / total if total else 0


def error_cluster_density(expected, actual):
    """Fraction of error cells whose 8-neighborhood contains another error cell."""
    H, W = len(expected), len(expected[0])
    errors = {(r, c) for r in range(H) for c in range(W)
              if expected[r][c] != actual[r][c]}
    if not errors:
        return 0
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                 (-1, -1), (-1, 1), (1, -1), (1, 1)]
    clustered = sum(
        1 for r, c in errors
        if any((r + dr, c + dc) in errors for dr, dc in neighbors)
    )
    return clustered / len(errors)


def classify_phase(input_grid, expected, actual, training_pass_rate):
    """Decide whether the model is in code-debug or rule-comprehension phase.

    Code-debug signals (rule looks right, implementation has a bug):
      - high training pass rate (model's algorithm mostly works)
      - per-color transformation counts match (right kinds, right amounts)
      - color distribution overlap is high (right palette in right amounts)
      - errors are spatially clustered (structural bug at a specific location)

    A score of 3+ ⇒ code_debug; 0–1 ⇒ rule_comprehension; 2 ⇒ ambiguous.
    """
    tx_match = transformation_count_match(input_grid, expected, actual)
    color_match = color_distribution_overlap(expected, actual)
    cluster_density = error_cluster_density(expected, actual)

    score = 0
    if training_pass_rate >= 2 / 3:
        score += 1
    if tx_match > 0.99:
        score += 2
    if color_match > 0.95:
        score += 1
    if cluster_density > 0.7:
        score += 1

    if score >= 3:
        phase = "code_debug"
    elif score <= 1:
        phase = "rule_comprehension"
    else:
        phase = "ambiguous"

    return {
        "phase": phase,
        "code_bug_signals": score,
        "training_pass_rate": training_pass_rate,
        "transformation_match": tx_match,
        "color_distribution_overlap": color_match,
        "error_cluster_density": cluster_density,
    }


def detect_boundary_unchanged(input_grid, expected, actual, wall_color=None):
    """Boundary-handling bug: cells along region boundaries kept their input value
    when they should have been transformed.

    Fingerprint: a high fraction of error cells have identical input and actual
    output values (model didn't modify them), while expected modified them.
    Diagnoses missing boundary processing in the model's code.
    """
    H, W = len(input_grid), len(input_grid[0])
    error_cells = [(r, c) for r in range(H) for c in range(W)
                   if expected[r][c] != actual[r][c]]
    if not error_cells:
        return None

    unchanged = sum(
        1 for r, c in error_cells if actual[r][c] == input_grid[r][c]
    )
    ratio = unchanged / len(error_cells)
    if ratio < 0.7:
        return None

    return {
        "bug_class": "boundary_unchanged",
        "confidence": ratio,
        "fingerprint": (
            f"{unchanged}/{len(error_cells)} error cells kept their input "
            f"value unchanged. Your code skipped processing for those cells."
        ),
        "suggested_fix": (
            "Check whether your code's main loop visits ALL relevant cells. "
            "Common cause: boundary cells excluded by an off-by-one in range, "
            "or processed only when a neighbor exists (causing edge cells to "
            "fall through). Verify the loop bounds and any neighbor-existence "
            "checks include the boundary."
        ),
    }


def detect_no_transformation_applied(input_grid, expected, actual, wall_color=None):
    """No-op bug: the code didn't transform the input at all (or barely).

    Fingerprint: actual output is identical or near-identical to input, while
    expected output modifies many cells. Diagnoses a main-loop that never
    executes, a conditional that skips every relevant cell, or a missing
    write-back to the output grid.
    """
    H, W = len(input_grid), len(input_grid[0])
    expected_changes = sum(
        1 for r in range(H) for c in range(W)
        if expected[r][c] != input_grid[r][c]
    )
    if expected_changes < 10:
        return None

    actual_changes = sum(
        1 for r in range(H) for c in range(W)
        if actual[r][c] != input_grid[r][c]
    )

    if actual_changes / expected_changes > 0.1:
        return None

    return {
        "bug_class": "no_transformation_applied",
        "confidence": 1.0 - (actual_changes / expected_changes),
        "fingerprint": (
            f"Your code modified {actual_changes} cells. The expected output "
            f"modifies {expected_changes} cells. Your code is essentially a no-op "
            f"on this pair."
        ),
        "suggested_fix": (
            "Your code returns the input grid almost unchanged. The transformation "
            "rule isn't being applied at all. Likely causes:\n"
            "  - A main loop never enters its body (empty iterable, wrong condition)\n"
            "  - A conditional gate skips every cell that should change\n"
            "  - Output is being written to a copy that's never returned\n"
            "  - solve() returns input_grid instead of the modified output\n"
            "Trace through your code on training pair 1: which line should be "
            "writing the new value to output[r][c], and why isn't that line firing?"
        ),
    }


DETECTORS = [
    detect_conn_mismatch,
    detect_boundary_unchanged,
    detect_no_transformation_applied,
]


# ----------------------------------------------------------------------
# Structural-diff detector: compare features of failing pairs vs passing
# pairs. Used to make rule_comprehension feedback as concrete as
# code_debug feedback.
# ----------------------------------------------------------------------


def _count_regions(input_grid, wall_color):
    """Count 4-connected components of non-wall cells."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    n = 0
    for r in range(H):
        for c in range(W):
            if seen[r][c] or input_grid[r][c] == wall_color:
                continue
            n += 1
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < H and 0 <= ny < W
                            and not seen[nx][ny]
                            and input_grid[nx][ny] != wall_color):
                        seen[nx][ny] = True
                        q.append((nx, ny))
    return n


def _has_wraparound_region(input_grid, wall_color):
    """Detect if any non-wall region's bounding box contains an interior wall —
    i.e., the region wraps around an internal obstacle (non-rectangular shape)."""
    H, W = len(input_grid), len(input_grid[0])
    seen = [[False] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if seen[r][c] or input_grid[r][c] == wall_color:
                continue
            cells = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < H and 0 <= ny < W
                            and not seen[nx][ny]
                            and input_grid[nx][ny] != wall_color):
                        seen[nx][ny] = True
                        q.append((nx, ny))
            rmin = min(p[0] for p in cells)
            rmax = max(p[0] for p in cells)
            cmin = min(p[1] for p in cells)
            cmax = max(p[1] for p in cells)
            for rr in range(rmin, rmax + 1):
                for cc in range(cmin, cmax + 1):
                    if input_grid[rr][cc] == wall_color:
                        return True
    return False


def extract_pair_features(input_grid, output_grid, wall_color=None):
    """Extract structural features of a single training pair."""
    if wall_color is None:
        wall_color = detect_wall_color(input_grid)

    H, W = len(input_grid), len(input_grid[0])
    in_palette = set(v for row in input_grid for v in row)
    out_palette = set(v for row in output_grid for v in row)

    return {
        "grid_shape": (H, W),
        "input_palette_size": len(in_palette),
        "output_palette_size": len(out_palette),
        "new_colors_in_output": len(out_palette - in_palette),
        "removed_colors": len(in_palette - out_palette),
        "num_non_wall_regions": (
            _count_regions(input_grid, wall_color) if wall_color is not None else None
        ),
        "has_wraparound_region": (
            _has_wraparound_region(input_grid, wall_color)
            if wall_color is not None else None
        ),
    }


def detect_structural_diff(passing_pairs, failing_pairs, wall_color=None):
    """Compare features of failing-pair inputs vs passing-pair inputs.

    Each argument is a list of (input_grid, output_grid) tuples.
    Returns a list of {feature, passing_values, failing_values, suggestion}
    for features that differ cleanly between the two groups.
    """
    if not passing_pairs or not failing_pairs:
        return []

    passing_features = [extract_pair_features(i, o, wall_color) for i, o in passing_pairs]
    failing_features = [extract_pair_features(i, o, wall_color) for i, o in failing_pairs]

    differences = []
    for key in passing_features[0]:
        passing_vals = [f[key] for f in passing_features]
        failing_vals = [f[key] for f in failing_features]
        if any(v is None for v in passing_vals + failing_vals):
            continue
        if all(isinstance(v, bool) for v in passing_vals + failing_vals):
            if set(passing_vals) != set(failing_vals) and len(set(failing_vals)) == 1:
                differences.append({
                    "feature": key,
                    "passing_values": passing_vals,
                    "failing_values": failing_vals,
                })
            continue
        try:
            p_min, p_max = min(passing_vals), max(passing_vals)
            f_min, f_max = min(failing_vals), max(failing_vals)
        except TypeError:
            continue
        if f_min > p_max or f_max < p_min:
            differences.append({
                "feature": key,
                "passing_values": passing_vals,
                "failing_values": failing_vals,
            })

    return differences


# ----------------------------------------------------------------------
# Regression detector: AST-diff between iter N and iter N-1 to determine
# whether the model patched (similar code) or rewrote (different code).
# Useful for catching false-confident algorithm changes.
# ----------------------------------------------------------------------


def detect_code_change(prev_code_text, current_code_text):
    """Classify whether iter N is a patch, modification, or rewrite of iter N-1.

    Returns {kind, similarity, prev_lines, current_lines}.
    Kinds: patched (>0.7), modified (>0.3), rewritten (<=0.3).
    Falls back to text similarity when AST parsing fails.
    """
    try:
        prev_norm = ast.dump(ast.parse(prev_code_text))
        curr_norm = ast.dump(ast.parse(current_code_text))
    except SyntaxError:
        prev_norm = prev_code_text
        curr_norm = current_code_text

    sim = SequenceMatcher(None, prev_norm, curr_norm).ratio()
    if sim > 0.7:
        kind = "patched"
    elif sim > 0.3:
        kind = "modified"
    else:
        kind = "rewritten"

    return {
        "kind": kind,
        "similarity": sim,
        "prev_lines": len(prev_code_text.splitlines()),
        "current_lines": len(current_code_text.splitlines()),
    }


# ----------------------------------------------------------------------
# Per-pair correctness tracking + regression detector (Layer 1).
# Catches the failure mode "model rewrites iter N away from a close-to-
# correct iter N-1" by giving the model a cell-level scoreboard.
# ----------------------------------------------------------------------


def per_pair_correctness(puzzle, actual_outputs):
    """For each training pair, count cells matching expected output.

    actual_outputs: list of grids (or None for failed solves), one per pair.
    Returns list of {pair_idx, correct, total, fraction} or marker dicts when
    solve() crashed or returned malformed output.
    """
    results = []
    train = puzzle.get("train", [])
    for i, (pair, actual) in enumerate(zip(train, actual_outputs), 1):
        expected = pair["output"]
        total = len(expected) * len(expected[0]) if expected else 0
        if actual is None:
            results.append({"pair_idx": i, "correct": 0, "total": total,
                            "fraction": 0.0, "status": "crashed"})
            continue
        if (len(actual) != len(expected)
                or any(len(actual[r]) != len(expected[r]) for r in range(len(expected)))):
            results.append({"pair_idx": i, "correct": 0, "total": total,
                            "fraction": 0.0, "status": "dim_mismatch"})
            continue
        correct = sum(
            1 for r in range(len(expected)) for c in range(len(expected[0]))
            if actual[r][c] == expected[r][c]
        )
        results.append({
            "pair_idx": i,
            "correct": correct,
            "total": total,
            "fraction": correct / total if total else 0.0,
            "status": "ok",
        })
    return results


def detect_regression(prev_per_pair, current_per_pair):
    """Compare per-pair correctness from iter N-1 to iter N.

    Returns {regressed_pairs, improved_pairs, cells_lost, cells_gained, net}
    or None if no useful comparison is possible.
    """
    if not prev_per_pair or len(prev_per_pair) != len(current_per_pair):
        return None

    regressed = []
    improved = []
    cells_lost = 0
    cells_gained = 0

    for prev, curr in zip(prev_per_pair, current_per_pair):
        if prev.get("status") != "ok" or curr.get("status") != "ok":
            continue
        delta = curr["correct"] - prev["correct"]
        if delta < 0:
            regressed.append({
                "pair_idx": curr["pair_idx"],
                "prev_correct": prev["correct"],
                "curr_correct": curr["correct"],
                "cells_lost": -delta,
                "total": curr["total"],
            })
            cells_lost += -delta
        elif delta > 0:
            improved.append({
                "pair_idx": curr["pair_idx"],
                "prev_correct": prev["correct"],
                "curr_correct": curr["correct"],
                "cells_gained": delta,
                "total": curr["total"],
            })
            cells_gained += delta

    if not regressed and not improved:
        return None

    return {
        "regressed_pairs": regressed,
        "improved_pairs": improved,
        "cells_lost": cells_lost,
        "cells_gained": cells_gained,
        "net": cells_gained - cells_lost,
    }


def diagnose(input_grid, expected, actual, training_pass_rate, wall_color=None):
    """Per-pair diagnosis. Returns phase classification + matching bug diagnoses.

    For full diagnosis with structural-diff and regression detection, use
    diagnose_full() which takes the whole puzzle and iter history.
    """
    phase = classify_phase(input_grid, expected, actual, training_pass_rate)
    bugs = []
    for detector in DETECTORS:
        result = detector(input_grid, expected, actual, wall_color)
        if result:
            bugs.append(result)
    return {"phase": phase, "bugs": bugs}


def diagnose_full(puzzle, actual_outputs, prev_code=None, current_code=None,
                  prev_actual_outputs=None, wall_color=None):
    """Full diagnosis using all training pairs + iter-over-iter regression check.

    puzzle: dict with 'train' key (list of {input, output} pairs)
    actual_outputs: list of model's solve() outputs, one per training pair, in order
    prev_code, current_code: optional code text strings for AST-similarity check
    prev_actual_outputs: optional iter N-1 solve() outputs for cell-level
                        regression detection (Layer 1)

    Returns:
      {
        phase: {...},
        bugs: [...],
        structural_diff: [...],            # if phase == rule_comprehension
        regression: {kind, similarity},    # AST-level (if both code texts)
        regression_alert: {...} | None,    # cell-level (if prev_actual_outputs)
        curr_per_pair: [{pair_idx, correct, total, ...}],
        prev_per_pair: [{...}] | None,
        passing_pair_indices: [...],
        failing_pair_indices: [...],
      }
    """
    train = puzzle.get("train", [])
    if len(actual_outputs) != len(train):
        raise ValueError("actual_outputs length must match number of training pairs")

    passing_idx, failing_idx = [], []
    for i, (pair, actual) in enumerate(zip(train, actual_outputs)):
        if actual == pair["output"]:
            passing_idx.append(i)
        else:
            failing_idx.append(i)

    train_n = len(train)
    pass_rate = len(passing_idx) / train_n if train_n else 0.0

    curr_per_pair = per_pair_correctness(puzzle, actual_outputs)
    prev_per_pair = None
    regression_alert = None
    if prev_actual_outputs is not None:
        prev_per_pair = per_pair_correctness(puzzle, prev_actual_outputs)
        regression_alert = detect_regression(prev_per_pair, curr_per_pair)

    result = {
        "phase": None,
        "bugs": [],
        "structural_diff": [],
        "regression": None,
        "regression_alert": regression_alert,
        "curr_per_pair": curr_per_pair,
        "prev_per_pair": prev_per_pair,
        "passing_pair_indices": passing_idx,
        "failing_pair_indices": failing_idx,
    }

    if not failing_idx:
        return result

    first_failing = failing_idx[0]
    inp = train[first_failing]["input"]
    exp = train[first_failing]["output"]
    act = actual_outputs[first_failing]

    result["phase"] = classify_phase(inp, exp, act, pass_rate)

    for detector in DETECTORS:
        match = detector(inp, exp, act, wall_color)
        if match:
            result["bugs"].append(match)

    if result["phase"]["phase"] == "rule_comprehension" and passing_idx:
        passing_pairs = [(train[i]["input"], train[i]["output"]) for i in passing_idx]
        failing_pairs = [(train[i]["input"], train[i]["output"]) for i in failing_idx]
        result["structural_diff"] = detect_structural_diff(
            passing_pairs, failing_pairs, wall_color
        )

    if prev_code and current_code:
        result["regression"] = detect_code_change(prev_code, current_code)

    return result


def format_targeted_feedback(diagnosis):
    """Render diagnosis as the targeted-feedback string for iter-2+ prompts."""
    phase_info = diagnosis["phase"]
    phase = phase_info["phase"] if phase_info else None
    bugs = diagnosis.get("bugs", [])

    lines = []

    reg_alert = diagnosis.get("regression_alert")
    if reg_alert and reg_alert.get("cells_lost", 0) > 0:
        lines.append("!" * 80)
        lines.append("REGRESSION ALERT")
        lines.append("!" * 80)
        lines.append("")
        lines.append(
            f"Your current iter destroyed {reg_alert['cells_lost']} cells that "
            f"were correct in the prior iter."
        )
        if reg_alert.get("cells_gained", 0) > 0:
            lines.append(
                f"You also gained {reg_alert['cells_gained']} cells, "
                f"net change: {reg_alert['net']:+d}."
            )
        lines.append("")
        lines.append("Per-pair changes:")
        for r in reg_alert.get("regressed_pairs", []):
            lines.append(
                f"  Pair {r['pair_idx']}: {r['prev_correct']}/{r['total']} -> "
                f"{r['curr_correct']}/{r['total']} (-{r['cells_lost']})"
            )
        for r in reg_alert.get("improved_pairs", []):
            lines.append(
                f"  Pair {r['pair_idx']}: {r['prev_correct']}/{r['total']} -> "
                f"{r['curr_correct']}/{r['total']} (+{r['cells_gained']})"
            )
        lines.append("")
        if reg_alert.get("net", 0) < 0:
            lines.append(
                "Your rewrite went BACKWARDS. The prior iter's algorithm was "
                "closer to correct than your current one. REVERT to the prior "
                "algorithm and apply a small patch instead of rewriting."
            )
        else:
            lines.append(
                "Mixed change: you fixed some pairs but broke others. Pull the "
                "winning logic from the prior iter on the regressed pair(s) "
                "back into your current code."
            )
        lines.append("")

    per_pair = diagnosis.get("curr_per_pair") or []
    if per_pair:
        lines.append("=" * 80)
        lines.append("PER-PAIR CELL CORRECTNESS")
        lines.append("=" * 80)
        lines.append("")
        for p in per_pair:
            tag = "PASS" if p.get("status") == "ok" and p["correct"] == p["total"] else "FAIL"
            if p.get("status") == "crashed":
                lines.append(f"  Pair {p['pair_idx']}: CRASHED")
            elif p.get("status") == "dim_mismatch":
                lines.append(f"  Pair {p['pair_idx']}: DIMENSION MISMATCH")
            else:
                lines.append(
                    f"  Pair {p['pair_idx']}: {p['correct']}/{p['total']} "
                    f"({p['fraction'] * 100:.1f}%)  [{tag}]"
                )
        lines.append("")

    lines.append("=" * 80)
    lines.append("DIAGNOSIS")
    lines.append("=" * 80)
    lines.append("")

    if phase is None:
        lines.append("All training pairs pass. No further diagnosis needed.")
        return "\n".join(lines)

    lines.append(f"Phase: {phase}")
    lines.append(
        f"  Signals: training_pass={phase_info['training_pass_rate']:.2f}, "
        f"transformation_match={phase_info['transformation_match']:.2f}, "
        f"color_overlap={phase_info['color_distribution_overlap']:.2f}, "
        f"error_cluster_density={phase_info['error_cluster_density']:.2f}"
    )
    lines.append("")

    if phase == "code_debug":
        lines.append(
            "Your transformation rule looks correct (you are producing the right "
            "color transformations in roughly the right quantities). The bug is "
            "in the code-level implementation. Do NOT rewrite the algorithm — "
            "find the implementation bug."
        )
        lines.append("")
        if bugs:
            for bug in bugs:
                lines.append(
                    f"BUG MATCHED: {bug['bug_class']} (confidence {bug['confidence']:.2f})"
                )
                lines.append(f"  Fingerprint: {bug['fingerprint']}")
                lines.append(f"  Suggested fix: {bug['suggested_fix']}")
                lines.append("")
        else:
            lines.append(
                "No specific bug-class fingerprint matched. Scan your code for "
                "off-by-one errors, wrong adjacency choices (4-conn vs 8-conn), "
                "boundary handling mistakes, or aliasing/mutation bugs."
            )
    elif phase == "rule_comprehension":
        lines.append(
            "The transformation rule appears wrong (not just a code bug). "
            "Re-derive the rule from the training pairs before changing code."
        )
        struct = diagnosis.get("structural_diff") or []
        if struct:
            lines.append("")
            lines.append(
                "Structural difference between failing and passing training pairs:"
            )
            for diff in struct:
                lines.append(
                    f"  - {diff['feature']}: passing pairs={diff['passing_values']}, "
                    f"failing pairs={diff['failing_values']}"
                )
            lines.append("")
            lines.append(
                "Your current rule handles the passing pairs but not the failing "
                "ones. Identify what's different about the failing input(s) and "
                "make sure your rule accounts for it."
            )
    else:
        lines.append(
            "Diagnosis ambiguous. The rule is partially right but the code may "
            "also have bugs. Re-examine both rule and implementation."
        )

    regression = diagnosis.get("regression")
    if regression:
        lines.append("")
        lines.append(
            f"Iter-over-iter change: {regression['kind']} "
            f"(similarity={regression['similarity']:.2f})"
        )
        if regression["kind"] == "rewritten" and phase == "code_debug":
            lines.append(
                "  Warning: you rewrote the algorithm but the prior version was "
                "close to correct (rule was right; only the code had a bug). "
                "Consider reverting to the prior structure and applying a small "
                "patch instead."
            )

    return "\n".join(lines)
