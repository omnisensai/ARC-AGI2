"""
Feedback diagnostics: classify whether the model is in code-debug or
rule-comprehension phase, and detect specific bug-class fingerprints
from the spatial pattern of output errors.

Used to gate iter-2+ feedback content. Instead of dumping all diagnostics,
the validator picks the feedback type that matches the phase the model is in.
"""

from collections import Counter


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


DETECTORS = [
    detect_conn_mismatch,
]


def diagnose(input_grid, expected, actual, training_pass_rate, wall_color=None):
    """Top-level diagnosis. Returns phase classification + matching bug diagnoses."""
    phase = classify_phase(input_grid, expected, actual, training_pass_rate)
    bugs = []
    for detector in DETECTORS:
        result = detector(input_grid, expected, actual, wall_color)
        if result:
            bugs.append(result)
    return {"phase": phase, "bugs": bugs}


def format_targeted_feedback(diagnosis):
    """Render diagnosis as the targeted-feedback string for iter-2+ prompts."""
    phase_info = diagnosis["phase"]
    phase = phase_info["phase"]
    bugs = diagnosis["bugs"]

    lines = []
    lines.append("=" * 80)
    lines.append("DIAGNOSIS")
    lines.append("=" * 80)
    lines.append("")
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
    else:
        lines.append(
            "Diagnosis ambiguous. The rule is partially right but the code may "
            "also have bugs. Re-examine both rule and implementation."
        )

    return "\n".join(lines)
