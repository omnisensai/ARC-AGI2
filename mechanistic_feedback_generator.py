"""
Generic Mechanistic Feedback Generator for ARC-AGI
Generates structural analysis instead of just grid diffs
"""

import numpy as np
from collections import deque, Counter
from typing import List, Set, Tuple, Dict, Any

class StructuralAnalyzer:
    """Analyzes grid structure and properties"""
    
    def __init__(self, grid):
        self.grid = np.array(grid)
        self.rows, self.cols = self.grid.shape
    
    def find_clusters(self, value, connectivity=4):
        """Find connected components of a specific value"""
        visited = np.zeros((self.rows, self.cols), dtype=bool)
        clusters = []
        
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        if connectivity == 8:
            dirs = [(dr,dc) for dr in [-1,0,1] for dc in [-1,0,1] if not (dr==0 and dc==0)]
        
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
    
    def classify_cluster_properties(self, cluster: Set[Tuple[int, int]]) -> Dict[str, Any]:
        """Extract topological properties of a cluster"""
        if not cluster:
            return {}
        
        min_r = min(r for r, c in cluster)
        max_r = max(r for r, c in cluster)
        min_c = min(c for r, c in cluster)
        max_c = max(c for r, c in cluster)
        
        touches_edge = any(
            r == 0 or r == self.rows-1 or c == 0 or c == self.cols-1
            for r, c in cluster
        )
        
        touches_top = any(r == 0 for r, c in cluster)
        touches_bottom = any(r == self.rows-1 for r, c in cluster)
        touches_left = any(c == 0 for r, c in cluster)
        touches_right = any(c == self.cols-1 for r, c in cluster)
        
        # Check if forms a complete line
        is_vertical_line = (max_c == min_c and max_r - min_r + 1 == self.rows)
        is_horizontal_line = (max_r == min_r and max_c - min_c + 1 == self.cols)
        
        return {
            'bounds': (min_r, max_r, min_c, max_c),
            'size': len(cluster),
            'touches_edge': touches_edge,
            'edge_locations': {
                'top': touches_top,
                'bottom': touches_bottom,
                'left': touches_left,
                'right': touches_right
            },
            'is_vertical_line': is_vertical_line,
            'is_horizontal_line': is_horizontal_line,
            'is_complete_line': is_vertical_line or is_horizontal_line,
            'is_internal': not touches_edge
        }
    
    def flood_fill(self, start, passable_values, connectivity=4):
        """Flood fill from a starting position"""
        if not (0 <= start[0] < self.rows and 0 <= start[1] < self.cols):
            return set()
        
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        if connectivity == 8:
            dirs = [(dr,dc) for dr in [-1,0,1] for dc in [-1,0,1] if not (dr==0 and dc==0)]
        
        reachable = set()
        queue = deque([start])
        visited = {start}
        
        while queue:
            r, c = queue.popleft()
            reachable.add((r, c))
            
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if (nr, nc) not in visited and self.grid[nr, nc] in passable_values:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        
        return reachable


class MechanisticFeedback:
    """Generates mechanistic feedback by comparing expected vs actual behavior"""
    
    def __init__(self, input_grid, expected_output, actual_output):
        self.input_grid = np.array(input_grid)
        self.expected = np.array(expected_output)
        self.actual = np.array(actual_output)
        self.rows, self.cols = self.input_grid.shape
        
        self.input_analyzer = StructuralAnalyzer(input_grid)
        self.expected_analyzer = StructuralAnalyzer(expected_output)
        self.actual_analyzer = StructuralAnalyzer(actual_output)
    
    def find_errors(self) -> List[Tuple[int, int]]:
        """Find all cells where expected != actual"""
        errors = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.expected[r, c] != self.actual[r, c]:
                    errors.append((r, c))
        return errors
    
    def classify_errors(self, errors: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Classify errors by type and pattern"""
        if not errors:
            return {'type': 'none', 'count': 0}
        
        error_types = {
            'spurious_activation': [],  # Cell activated when shouldn't be
            'missed_activation': [],     # Cell not activated when should be
            'wrong_value': []            # Cell has wrong value
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
    
    def analyze_structural_mismatch(self, value) -> str:
        """Analyze differences in structure for a specific value"""
        input_clusters = self.input_analyzer.find_clusters(value)
        expected_clusters = self.expected_analyzer.find_clusters(value)
        actual_clusters = self.actual_analyzer.find_clusters(value)
        
        analysis = f"\nSTRUCTURAL ANALYSIS FOR VALUE {value}:\n"
        analysis += f"  Input: {len(input_clusters)} clusters\n"
        analysis += f"  Expected output: {len(expected_clusters)} clusters\n"
        analysis += f"  Your output: {len(actual_clusters)} clusters\n\n"
        
        # Analyze input clusters with properties
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
    
    def diagnose_operation_mismatch(self, seed_value=None) -> str:
        """Diagnose what operations were performed incorrectly"""
        diagnosis = "\nOPERATION DIAGNOSIS:\n"
        
        # Find what changed from input to expected
        changed_cells_exp = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.input_grid[r, c] != self.expected[r, c]:
                    changed_cells_exp.append((r, c, self.input_grid[r, c], self.expected[r, c]))
        
        # Find what changed from input to actual
        changed_cells_act = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.input_grid[r, c] != self.actual[r, c]:
                    changed_cells_act.append((r, c, self.input_grid[r, c], self.actual[r, c]))
        
        diagnosis += f"  EXPECTED CHANGES: {len(changed_cells_exp)} cells modified\n"
        diagnosis += f"  YOUR CHANGES: {len(changed_cells_act)} cells modified\n\n"
        
        # Analyze change patterns
        if changed_cells_exp:
            exp_change_types = Counter((from_val, to_val) for _, _, from_val, to_val in changed_cells_exp)
            diagnosis += "  EXPECTED TRANSFORMATIONS:\n"
            for (from_val, to_val), count in exp_change_types.most_common():
                diagnosis += f"    {from_val} → {to_val}: {count} cells\n"
        
        if changed_cells_act:
            act_change_types = Counter((from_val, to_val) for _, _, from_val, to_val in changed_cells_act)
            diagnosis += "\n  YOUR TRANSFORMATIONS:\n"
            for (from_val, to_val), count in act_change_types.most_common():
                diagnosis += f"    {from_val} → {to_val}: {count} cells\n"
        
        return diagnosis
    
    def generate_feedback(self) -> str:
        """Generate complete mechanistic feedback"""
        feedback = "="*80 + "\n"
        feedback += "MECHANISTIC FEEDBACK\n"
        feedback += "="*80 + "\n\n"
        
        # Error summary
        errors = self.find_errors()
        feedback += f"ERRORS: {len(errors)} / {self.rows * self.cols} cells\n"
        
        if len(errors) == 0:
            feedback += "\n✓✓✓ PERFECT! All cells match expected output.\n"
            return feedback
        
        # Classify errors
        error_types = self.classify_errors(errors)
        feedback += f"\nERROR CLASSIFICATION:\n"
        feedback += f"  Spurious activations: {len(error_types['spurious_activation'])}\n"
        feedback += f"  Missed activations: {len(error_types['missed_activation'])}\n"
        feedback += f"  Wrong values: {len(error_types['wrong_value'])}\n"
        
        # Structural analysis for each unique value
        unique_values = set(self.input_grid.flatten()) | set(self.expected.flatten())
        for val in sorted(unique_values):
            if val in self.input_grid or val in self.expected:
                feedback += self.analyze_structural_mismatch(val)
        
        # Operation diagnosis
        feedback += self.diagnose_operation_mismatch()
        
        # Specific error locations (sample)
        feedback += "\nERROR SAMPLES (first 10):\n"
        for i, (r, c) in enumerate(errors[:10]):
            exp_val = self.expected[r, c]
            act_val = self.actual[r, c]
            inp_val = self.input_grid[r, c]
            feedback += f"  ({r:2}, {c:2}): input={inp_val}, expected={exp_val}, got={act_val}\n"
        
        if len(errors) > 10:
            feedback += f"  ... and {len(errors) - 10} more errors\n"
        
        feedback += "\n" + "="*80 + "\n"
        
        return feedback


def generate_mechanistic_feedback(input_grid, expected_output, actual_output) -> str:
    """
    Main entry point: Generate mechanistic feedback for a solution attempt
    
    Args:
        input_grid: Original puzzle input
        expected_output: Correct solution
        actual_output: Model's attempted solution
    
    Returns:
        Formatted mechanistic feedback string
    """
    mf = MechanisticFeedback(input_grid, expected_output, actual_output)
    return mf.generate_feedback()


# Example usage
if __name__ == "__main__":
    # Test with a simple example
    input_grid = [
        [8, 8, 1, 8],
        [8, 8, 1, 8],
        [6, 8, 1, 8],
        [8, 8, 1, 8]
    ]
    
    expected = [
        [7, 7, 1, 8],
        [7, 7, 1, 8],
        [6, 7, 1, 8],
        [7, 7, 1, 8]
    ]
    
    actual = [
        [7, 7, 1, 7],  # Wrong: extra 7 on right
        [7, 7, 1, 7],
        [6, 7, 1, 7],
        [7, 7, 1, 7]
    ]
    
    feedback = generate_mechanistic_feedback(input_grid, expected, actual)
    print(feedback)
