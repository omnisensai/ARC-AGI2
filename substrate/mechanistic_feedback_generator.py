"""
Generic Mechanistic Feedback Generator for ARC-AGI
"""

import numpy as np
from collections import deque, Counter
from typing import List, Set, Tuple, Dict, Any


class StructuralAnalyzer:
    def __init__(self, grid):
        self.grid = np.array(grid)
        self.rows, self.cols = self.grid.shape

    def find_clusters(self, value, connectivity=4):
        visited = np.zeros((self.rows, self.cols), dtype=bool)
        clusters = []
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        if connectivity == 8:
            dirs = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i, j] == value and not visited[i, j]:
                    cluster = set()
                    queue = deque([(i, j)])
                    visited[i, j] = True
                    while queue:
                        r, c = queue.popleft()
                        cluster.add((r, c))
                        for dr, dc in dirs:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.grid[nr, nc] == value and not visited[nr, nc]:
                                    visited[nr, nc] = True
                                    queue.append((nr, nc))
                    clusters.append(cluster)
        return clusters

    def classify_cluster_properties(self, cluster):
        if not cluster:
            return {}
        min_r = min(r for r, c in cluster)
        max_r = max(r for r, c in cluster)
        min_c = min(c for r, c in cluster)
        max_c = max(c for r, c in cluster)
        touches_edge = any(
            r == 0 or r == self.rows - 1 or c == 0 or c == self.cols - 1
            for r, c in cluster
        )
        is_vertical_line = (max_c == min_c and max_r - min_r + 1 == self.rows)
        is_horizontal_line = (max_r == min_r and max_c - min_c + 1 == self.cols)
        return {
            'bounds': (min_r, max_r, min_c, max_c),
            'size': len(cluster),
            'touches_edge': touches_edge,
            'is_vertical_line': is_vertical_line,
            'is_horizontal_line': is_horizontal_line,
            'is_complete_line': is_vertical_line or is_horizontal_line,
        }


class MechanisticFeedback:
    def __init__(self, input_grid, expected_output, actual_output):
        self.input_grid = np.array(input_grid)
        self.expected = np.array(expected_output)
        self.actual = np.array(actual_output)
        self.rows, self.cols = self.input_grid.shape
        self.input_analyzer = StructuralAnalyzer(input_grid)
        self.expected_analyzer = StructuralAnalyzer(expected_output)
        self.actual_analyzer = StructuralAnalyzer(actual_output)

    def find_errors(self):
        errors = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.expected[r, c] != self.actual[r, c]:
                    errors.append((r, c))
        return errors

    def classify_errors(self, errors):
        if not errors:
            return {'type': 'none', 'count': 0}
        error_types = {
            'spurious_activation': [],
            'missed_activation': [],
            'wrong_value': []
        }
        for r, c in errors:
            exp_val = self.expected[r, c]
            act_val = self.actual[r, c]
            if exp_val == self.input_grid[r, c] and act_val != exp_val:
                error_types['spurious_activation'].append((r, c, act_val))
            elif act_val == self.input_grid[r, c] and exp_val != act_val:
                error_types['missed_activation'].append((r, c, exp_val))
            else:
                error_types['wrong_value'].append((r, c, exp_val, act_val))
        return error_types

    def analyze_structural_mismatch(self, value):
        input_clusters = self.input_analyzer.find_clusters(value)
        expected_clusters = self.expected_analyzer.find_clusters(value)
        actual_clusters = self.actual_analyzer.find_clusters(value)
        analysis = f"\nSTRUCTURAL ANALYSIS FOR VALUE {value}:\n"
        analysis += f"  Input: {len(input_clusters)} clusters\n"
        analysis += f"  Expected output: {len(expected_clusters)} clusters\n"
        analysis += f"  Your output: {len(actual_clusters)} clusters\n\n"
        if input_clusters:
            analysis += f"  INPUT CLUSTER PROPERTIES:\n"
            for i, cluster in enumerate(input_clusters, 1):
                props = self.input_analyzer.classify_cluster_properties(cluster)
                min_r, max_r, min_c, max_c = props['bounds']
                status = "EDGE-TOUCHING" if props['touches_edge'] else "INTERNAL"
                if props['is_complete_line']:
                    line_type = "VERTICAL" if props['is_vertical_line'] else "HORIZONTAL"
                    status += f" ({line_type} COMPLETE LINE)"
                analysis += f"    Cluster {i}: {status}\n"
                analysis += f"      Location: rows {min_r}-{max_r}, cols {min_c}-{max_c}\n"
                analysis += f"      Size: {props['size']} cells\n"
        return analysis

    def diagnose_operation_mismatch(self):
        diagnosis = "\nOPERATION DIAGNOSIS:\n"
        changed_cells_exp = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.input_grid[r, c] != self.expected[r, c]:
                    changed_cells_exp.append((r, c, self.input_grid[r, c], self.expected[r, c]))
        changed_cells_act = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.input_grid[r, c] != self.actual[r, c]:
                    changed_cells_act.append((r, c, self.input_grid[r, c], self.actual[r, c]))
        diagnosis += f"  EXPECTED CHANGES: {len(changed_cells_exp)} cells modified\n"
        diagnosis += f"  YOUR CHANGES: {len(changed_cells_act)} cells modified\n\n"
        if changed_cells_exp:
            exp_change_types = Counter((from_val, to_val) for _, _, from_val, to_val in changed_cells_exp)
            diagnosis += "  EXPECTED TRANSFORMATIONS:\n"
            for (from_val, to_val), count in exp_change_types.most_common():
                diagnosis += f"    {from_val} -> {to_val}: {count} cells\n"
        if changed_cells_act:
            act_change_types = Counter((from_val, to_val) for _, _, from_val, to_val in changed_cells_act)
            diagnosis += "\n  YOUR TRANSFORMATIONS:\n"
            for (from_val, to_val), count in act_change_types.most_common():
                diagnosis += f"    {from_val} -> {to_val}: {count} cells\n"
        return diagnosis

    def generate_feedback(self):
        feedback = "=" * 80 + "\n"
        feedback += "MECHANISTIC FEEDBACK\n"
        feedback += "=" * 80 + "\n\n"
        errors = self.find_errors()
        feedback += f"ERRORS: {len(errors)} / {self.rows * self.cols} cells\n"
        if len(errors) == 0:
            feedback += "\nPERFECT! All cells match expected output.\n"
            return feedback
        error_types = self.classify_errors(errors)
        feedback += f"\nERROR CLASSIFICATION:\n"
        feedback += f"  Spurious activations: {len(error_types['spurious_activation'])}\n"
        feedback += f"  Missed activations: {len(error_types['missed_activation'])}\n"
        feedback += f"  Wrong values: {len(error_types['wrong_value'])}\n"
        unique_values = set(self.input_grid.flatten()) | set(self.expected.flatten())
        for val in sorted(unique_values):
            feedback += self.analyze_structural_mismatch(int(val))
        feedback += self.diagnose_operation_mismatch()
        feedback += "\nERROR SAMPLES (first 10):\n"
        for i, (r, c) in enumerate(errors[:10]):
            exp_val = self.expected[r, c]
            act_val = self.actual[r, c]
            inp_val = self.input_grid[r, c]
            feedback += f"  ({r:2}, {c:2}): input={inp_val}, expected={exp_val}, got={act_val}\n"
        if len(errors) > 10:
            feedback += f"  ... and {len(errors) - 10} more errors\n"
        feedback += "\n" + "=" * 80 + "\n"
        return feedback


def generate_mechanistic_feedback(input_grid, expected_output, actual_output):
    mf = MechanisticFeedback(input_grid, expected_output, actual_output)
    return mf.generate_feedback()
