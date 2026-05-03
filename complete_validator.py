"""
Complete validator with two-phase validation:
Phase 1: Training validation (for iteration)
Phase 2: Test validation (for final success check)
"""

from validator import feedback_loop

def validate_solution_complete(puzzle, code):
    """
    Complete validation:
    1. Check all training pairs
    2. If training passes, check test
    3. Return detailed results
    """
    
    # Phase 1: Training validation
    action, report = feedback_loop(puzzle, code, mode="dev")
    
    training_passed = (action == "SUBMIT")
    
    if not training_passed:
        return {
            "training_passed": False,
            "test_passed": None,  # Didn't get to test
            "true_solve": False,
            "report": report,
            "conclusion": "Training failed - needs iteration"
        }
    
    # Phase 2: Test validation
    try:
        exec(code, globals())
        test_input = puzzle['test'][0]['input']
        test_expected = puzzle['test'][0]['output']
        test_actual = solve(test_input)
        
        test_passed = (test_actual == test_expected)
        
        return {
            "training_passed": True,
            "test_passed": test_passed,
            "true_solve": test_passed,
            "report": report,
            "conclusion": "TRUE SOLVE!" if test_passed else "False positive - test failed"
        }
        
    except Exception as e:
        return {
            "training_passed": True,
            "test_passed": False,
            "true_solve": False,
            "report": report + f"\n\nTest execution error: {e}",
            "conclusion": "Test execution failed"
        }


if __name__ == "__main__":
    # Example usage
    import json
    
    with open('puzzle_new.json', 'r') as f:
        puzzle = json.load(f)
    
    # Test with dummy solution
    test_code = """
def solve(input_grid):
    return input_grid
"""
    
    result = validate_solution_complete(puzzle, test_code)
    
    print("="*80)
    print("COMPLETE VALIDATION RESULTS")
    print("="*80)
    print()
    print(f"Training passed: {result['training_passed']}")
    print(f"Test passed: {result['test_passed']}")
    print(f"TRUE SOLVE: {result['true_solve']}")
    print()
    print(f"Conclusion: {result['conclusion']}")
    print()
    print("Report:")
    print(result['report'])
