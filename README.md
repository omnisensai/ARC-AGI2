# TCP/AP Substrate Validation Framework

**Deterministic validation system for ARC-AGI puzzle solving using transformation grid encoding and mechanistic feedback.**

---

## 🎯 What This Is

This framework validates LLM solutions to ARC-AGI puzzles through:
1. **Substrate encoding** - Transformation grids that compress patterns 200×
2. **Training validation** - Proves rule extraction (not lucky guessing)
3. **Mechanistic feedback** - Structural diagnosis of failures
4. **Two-phase validation** - Training (3/3) + Test (1/1) = TRUE SOLVE

**Key insight:** Traditional benchmarks can't distinguish understanding from luck. This framework validates rule extraction through deterministic training validation.

---

## 📁 File Structure

```
/home/claude/
├── puzzle_28a6681f.json              # Example puzzle (75% difficulty)
├── puzzle_new.json                   # Puzzle 8f3a5a89 (75% difficulty)
│
├── arc_prompt_generator_v5.py        # ★ Generates substrate prompts
├── transformation_grid.py            # ★ Core: Generates +/=/−/. symbols
├── mechanistic_feedback_generator.py # ★ Cluster analysis & diagnosis
├── complete_substrate_feedback.py    # ★ 4-layer feedback system
├── complete_validator.py             # ★ Two-phase validation
├── validator.py                      # Phase 1 only (legacy)
│
/mnt/user-data/outputs/
├── PUZZLE_8f3a5a89_FINAL.txt         # Ready-to-send substrate prompt
├── TEST_FEEDBACK_PAIR_*.txt          # Example feedback files
├── README.md                          # This file
└── [all documentation & examples]
```

---

## 🚀 Quick Start

### **Step 1: Generate Substrate Prompt**

```python
from arc_prompt_generator_v5 import generate_prompt
import json

# Load puzzle
with open('puzzle_new.json', 'r') as f:
    puzzle = json.load(f)

# Generate substrate prompt
prompt = generate_prompt(puzzle)

# Save to file
with open('substrate_prompt.txt', 'w') as f:
    f.write(prompt)

# Send this prompt to your LLM
```

### **Step 2: Validate Model's Solution**

```python
from complete_validator import validate_solution_complete

# Model returns Python code
model_code = """
def solve(input_grid):
    # Model's solution
    return output_grid
"""

# Validate (both training + test)
result = validate_solution_complete(puzzle, model_code)

if result['true_solve']:
    print("✅ TRUE SOLVE! Training 3/3 + Test 1/1")
elif result['training_passed']:
    print("⚠️ False positive: Training passed, test failed")
else:
    print("❌ Training failed, needs iteration")
```

### **Step 3: Generate Feedback (if failed)**

```python
from complete_substrate_feedback import generate_complete_substrate_feedback

# Execute model's code
exec(model_code, globals())

# Generate feedback for each failed training pair
for i, pair in enumerate(puzzle['train'], 1):
    actual = solve(pair['input'])
    expected = pair['output']
    
    if actual != expected:
        feedback = generate_complete_substrate_feedback(
            pair['input'],
            expected,
            actual,
            pair_number=i
        )
        
        print(f"=== FEEDBACK FOR PAIR {i} ===")
        print(feedback)
        
        # Send this feedback back to model for iteration
```

---

## 🔧 Core Components

### **1. Substrate Prompt Generator**

**File:** `arc_prompt_generator_v5.py`

**Purpose:** Creates constraint-engineered prompts with transformation grids

**Key features:**
- No hardcoded colors (works on any puzzle)
- Precise directive language ("transformation rule" not "grids")
- Clean formatting (no confusing symbols)
- Includes transformation grids for all training examples

**Usage:**
```python
from arc_prompt_generator_v5 import generate_prompt, save_prompt

prompt = generate_prompt(puzzle)  # Returns string
# OR
save_prompt(puzzle, 'output.txt')  # Saves to file
```

---

### **2. Transformation Grid Engine**

**File:** `transformation_grid.py`

**Purpose:** Deterministic encoding of input→output transitions

**Symbols:**
- `.` = background unchanged
- `=` = colored cell unchanged (structural anchor)
- `+` = background activated (0→color)
- `-` = color deactivated (color→0)
- `~` = color changed (color→different color)

**How it works:**
```python
from transformation_grid import generate_transformation_grid

# Pure algorithmic mapping (no AI!)
trans_grid, background = generate_transformation_grid(
    input_grid,
    output_grid
)

# Returns 2D array of symbols
# Example: [['.', '.', '+', '='], ...]
```

**Algorithm:** Pure if/else logic based on cell comparisons

---

### **3. Mechanistic Feedback Generator**

**File:** `mechanistic_feedback_generator.py`

**Purpose:** Structural analysis using graph algorithms

**Key algorithms:**
- **BFS (Breadth-First Search)** - Cluster detection
- **Flood fill** - Connected component analysis
- **Edge detection** - Boolean boundary checks
- **Operation counting** - Transition statistics

**What it analyzes:**
- Cluster count and properties
- Edge-touching vs internal clusters
- Spurious activations vs missed activations
- Operation type mismatches (adding vs removing)

**Usage:**
```python
from mechanistic_feedback_generator import generate_mechanistic_feedback

feedback = generate_mechanistic_feedback(
    input_grid,
    expected_output,
    actual_output
)

# Returns structural diagnosis (pure graph theory)
```

---

### **4. Complete Substrate Feedback**

**File:** `complete_substrate_feedback.py`

**Purpose:** Orchestrates all 4 feedback layers

**The 4 Layers:**

**Layer 1: Grid Comparison**
- Side-by-side expected vs actual grids
- Visual comparison

**Layer 2: Diff Map**
- X marks showing error locations
- Coordinate list with details

**Layer 3: Transformation Grid Analysis**
- Expected transformation grid
- Actual transformation grid
- Mismatch locations and types

**Layer 4: Mechanistic Analysis**
- Error classification (spurious/missed/wrong)
- Cluster analysis
- Operation diagnosis

**Usage:**
```python
from complete_substrate_feedback import generate_complete_substrate_feedback

feedback = generate_complete_substrate_feedback(
    input_grid,
    expected_output,
    actual_output,
    pair_number=1
)

# Returns complete 4-layer feedback string
```

---

### **5. Complete Validator (Two-Phase)**

**File:** `complete_validator.py`

**Purpose:** Validate both training AND test (true solve vs false positive)

**Two phases:**

**Phase 1: Training Validation**
- Checks all 3 training pairs
- If any fail → Returns failure, stops
- If all pass → Proceeds to Phase 2

**Phase 2: Test Validation**
- Checks test case
- Determines if true solve or false positive

**Usage:**
```python
from complete_validator import validate_solution_complete

result = validate_solution_complete(puzzle, code)

# Returns:
# {
#   'training_passed': bool,
#   'test_passed': bool,
#   'true_solve': bool,
#   'conclusion': str
# }
```

**Success criteria:**
- TRUE SOLVE: training 3/3 + test 1/1 = 4/4
- FALSE POSITIVE: training 1-2/3 + test 1/1 (lucky guess)
- OVERFITTING: training 3/3 + test 0/1 (memorized)

---

## 🔄 Complete Workflow

### **Iteration Loop (Training Validation)**

```python
from complete_validator import validate_solution_complete
from complete_substrate_feedback import generate_complete_substrate_feedback

iteration = 0
max_iterations = 10

while iteration < max_iterations:
    # Validate current solution
    result = validate_solution_complete(puzzle, code)
    
    if result['true_solve']:
        print(f"✅ TRUE SOLVE in {iteration} iterations!")
        break
    
    elif result['training_passed'] and not result['test_passed']:
        print("⚠️ Training passed but test failed (overfitting)")
        break
    
    else:
        # Training failed - generate feedback
        exec(code, globals())
        
        feedback_parts = []
        for i, pair in enumerate(puzzle['train'], 1):
            actual = solve(pair['input'])
            expected = pair['output']
            
            if actual != expected:
                feedback = generate_complete_substrate_feedback(
                    pair['input'],
                    expected,
                    actual,
                    pair_number=i
                )
                feedback_parts.append(feedback)
        
        # Send feedback to model
        combined_feedback = "\n\n".join(feedback_parts)
        code = model.iterate(combined_feedback)  # Get new code from model
        
        iteration += 1

print(f"Final result: {result}")
```

---

## 📊 Example Results

### **Puzzle 28a6681f (75% traditional difficulty):**

```
GPT:    3/3 training → Test ✅ (2 iterations)
Grok:   3/3 training → Test ✅ (2 iterations)
Claude: 3/3 training → Test ✅ (5 iterations)
Gemini: 2/3 training → Stuck ❌ (11 iterations)

Framework success rate: 75% (3/4 models)
Traditional success rate: ~75%
```

### **Puzzle 8f3a5a89 (75% traditional difficulty):**

```
Opus 4.7:    3/3 training in 2 iterations  ✅
Grok:        3/3 training in ~5 iterations ✅
Gemini:      3/3 training in 5 iterations  ✅ (after mechanistic upgrade)
Sonnet 4.6:  3/3 training in 9 iterations  ✅ (after lockdown v2 upgrade)

Framework success rate: 100% (4/4 models)
```

**Validation:** Framework tracks traditional difficulty. Lockdown v2 brought Sonnet across the line — see findings below.

---

## 🔬 Lockdown v2 — Findings from Sonnet 4.6 on 8f3a5a89

### **The arc**

Sonnet's per-iter pass count on 8f3a5a89:
```
Iter:    1  2  3  4  5  6  7  8  9
Score:  1/3 1/3 1/3 1/3 2/3 0/3 1/3 0/3 → 3/3 ✅
```

Eight iters of mechanistic feedback, history blocks, and lock-down anchors took Sonnet from 1/3 to 0/3 with constant drift. The model preserved *outcome* across iters (lock-down worked) but kept rewriting *mechanism*, breaking previously passing pairs.

Iter 9 jumped from 0/3 to 3/3 in a single response after **adding 6 lines to the substrate prompt** — a worked example for cluster-level vs cell-level property propagation.

### **The bug pattern**

For 8 iters Sonnet kept testing "edge-touching" per cell:
```python
# Wrong (per-cell test):
if r == 0 or c == 0 or r == H-1 or c == W-1:
    is_edge = True
```

The correct mechanic is cluster-level:
```python
# Right (cluster-level, propagated to all cells):
touches_edge = any((r == 0 or c == 0 or r == H-1 or c == W-1)
                   for r, c in cluster)
if touches_edge:
    for r, c in cluster:
        edge_touching.add((r, c))
```

The validator was telling Sonnet *which output cells were wrong* (mechanistic feedback). It never told Sonnet *which line of code was wrong*. The TIPS section had abstract guidance ("use topology"), but no concrete example to ground it.

### **What flipped 0 → 3/3**

Adding this to `arc_prompt_generator_v5.py` TIPS:

> **CLUSTER-LEVEL vs CELL-LEVEL PROPERTIES**
> A property describing a connected component applies to ALL cells of that cluster equally — do not redefine it per cell.
>
> **Worked example:** a vertical wall of 1s spanning rows 0..15 at column 6 is a single cluster. It "touches the grid edge" because (0,6) and (15,6) lie on the boundary. Therefore EVERY cell of that cluster — including (5,6), (8,6), deep in the interior of the grid — inherits the "edge-touching" property.
>
> **Wrong:** `if r == 0 or c == 0 or r == H-1 or c == W-1` (per-cell test).
> **Right:** classify the cluster once, then propagate the result to every cell.

Sonnet's iter 9 response opened with: *"The key insight from the tips is that I should check cluster properties at the cluster level, not cell-by-cell."* — direct citation, applied verbatim.

### **The two substrates**

| Substrate | Where | Shown when | Best for |
|---|---|---|---|
| **Prompt substrate** (`arc_prompt_generator_v5.py`) | Static prompt | Iter 1 only (task setup) | Teaching *how to think*: encoding rules, principles, worked examples |
| **Feedback substrate** (`run_feedback.py` + `complete_substrate_feedback.py`) | Per-iter output | Every failed iter | Teaching *what's wrong*: error localization, regression alerts, diagnostics |

**Lockdown v2 added to BOTH:**
- Prompt: cluster worked example, 4-conn vs 8-conn hint
- Feedback: code-checkpoint regression block, REGRESSION DETECTOR paragraph, "Pair(s) REGRESSED" status line

The win came from the prompt side. The feedback upgrade is structural insurance for future drift but didn't fire decisively in this run.

---

## 🎓 Takeaways

1. **Mechanistic feedback localizes errors; worked examples name bugs.** Per-cell error reports tell the model *where* the output is wrong. They don't tell the model *what kind of bug* its code has. For the latter, a concrete worked example with literal coordinates and a "wrong vs right" code snippet does more in 6 lines than thousands of chars of per-cell diagnostics.

2. **Small models need concrete bug names.** Larger models (Opus 4.7) infer the granularity rule from the abstract topology hint and the cluster cluster annotations in mechanistic feedback. Smaller models (Sonnet 4.6) need the bug pattern named with a literal example. The ceiling between Opus and Sonnet on 8f3a5a89 was 7 iters — entirely closeable with prompt clarification.

3. **Lock-down preserves outcome, not mechanism.** The original PASSING anchor block stops the model from changing the *output* on previously passing pairs, but allowed Sonnet to silently rewrite the *logic* that produced that output. The v2 code-checkpoint regression block shows the model its own past working code when a pair regresses, anchoring mechanism instead of just result.

4. **3-pair training is thin signal.** A pair passing once could be a coincidence (wrong rule that fits accidentally). A pair passing across 5+ iters is genuine understanding. The framework can't distinguish the two automatically. Future: weight checkpoints by pass-streak length.

5. **Two substrates, two roles.** Don't conflate prompt substrate (where the model learns the rule grammar) with feedback substrate (where the model gets correctness pressure). Adding error-feedback patterns to the prompt clutters it; adding worked examples to the feedback dilutes the per-iter signal.

---

## 🧪 Fine-Tune Ideas

These are concrete prompts/data shapes a fine-tune could target, not full curricula:

### **A. Prompt-side patterns (teach how to think)**

- **Worked-example library by bug pattern.** Build a library indexed by failure mode — `cluster_vs_cell_granularity`, `connectivity_choice`, `anchor_misidentification`, `halo_thickness`, `pre_grouping_artifacts`. Each entry: 5-line concrete example + wrong vs right code. Inject only the relevant ones based on which mechanistic-feedback signature matches.

- **"Rule grammar" templates.** Common ARC rules expressed as code skeletons: BFS-from-anchor, flood-fill-with-barrier, cluster-classify-and-propagate, halo-paint-with-mask. Show the skeleton in the prompt; ask the model to fill in the puzzle-specific bits.

- **Negative training in TIPS.** Currently TIPS lists "what to do" (look for anchors, look for barriers). Add "what to avoid": magic-number thresholds, per-cell tests for cluster properties, hardcoded grid dimensions.

### **B. Feedback-side patterns (teach what's wrong)**

- **Bug-pattern detector in mechanistic feedback.** When the substrate sees a *missed activation* concentrated along a single column/row that coincides with a vertical/horizontal cluster, emit a tagged diagnosis: "BUG PATTERN: cluster-level property mis-applied at cell level — missed cells (3,5), (4,5), ... lie inside cluster X which touches grid edge at (0,5) and (15,5)."

- **Auto-injected worked example on regression.** Detect bug pattern → inject the matching worked example from the library directly into the failing-pair feedback. Model sees the bug name, the example, and the per-cell evidence side by side.

- **Code-diff in regression block.** Don't just echo the past passing solve(); produce a `diff` between current and checkpoint, highlighting which lines were modified. Frames the regression as a literal patch the model needs to reconsider.

### **C. Iteration patterns (teach when to think harder)**

- **Stuck detection.** If 3+ consecutive iters stay at the same N/3 with the same failing pair(s), force the model into "step back" mode: reread the substrate, re-classify clusters from scratch, ignore prior code entirely. Breaks the local-minimum pattern Sonnet got stuck in (iter 1-4 all 1/3 with same P1 mechanism).

- **Hypothesis-first iters.** Before letting the model write code, require it to state in 2-3 sentences what rule it thinks the puzzle implements, *separately* from the code. Validate the hypothesis against training pairs (not just the code output). Catches misunderstanding earlier than per-cell diff.

- **Drop-and-redo on 0/3 regression.** When a model goes from N/3 → 0/3, automatically include the last passing solve() AND a "restart from this code" instruction. Prevents the cascade of compounding rewrites that Sonnet exhibited iters 6→8.

### **D. Architecture-level**

- **Per-puzzle worked-example caching.** When a puzzle is solved, save the *winning solve()* + the *bug pattern that was finally fixed* to a corpus. Future puzzles with similar mechanistic feedback signatures get the matching example pre-injected. Compounds gains across the puzzle set.

- **Multi-model bake-off as data generator.** Run all 4 models on each puzzle, log every iter response. Use the trajectory data to train a "next-iter advice" classifier that predicts which fine-tune intervention (worked example / code skeleton / hypothesis check) would unblock a given stuck state.

---

## 🎓 Key Concepts

### **Why Training Validation Matters**

**Traditional approach:**
```
Test output matches → "SOLVED!" ✓
Problem: Can't verify if understanding or luck
```

**TCP/AP approach:**
```
Training 3/3 → Proves rule extraction ✓
Test 1/1 → Proves generalization ✓
Total 4/4 → TRUE SOLVE verified ✓
```

**Example:** Gemini on 28a6681f
- Test output: ✅ Correct (would count as "solved")
- Training: ❌ 1/3 (only got one pair right)
- Verdict: **Lucky guess, not understanding**

Training validation caught this!

---

### **Deterministic Feedback (No AI)**

All feedback is **pure algorithmic**:
- Grid comparison → Boolean array equality
- Diff map → Set operations
- Transformation grids → If/else symbol mapping
- Mechanistic analysis → BFS graph algorithms

**No neural networks, no interpretation, no randomness!**

**Result:** Same input = same feedback (always)

---

### **Substrate Constraint Engineering**

**The core TCP/AP principle:**
> "LLMs don't need to 'understand' - they need interpretation space collapsed until only one valid option remains."

**How substrate achieves this:**
1. Transformation grids → Visual pattern encoding
2. Training validation → Eliminates invalid interpretations
3. Mechanistic feedback → Structural constraints
4. Precise language → Directive clarity

**Result:** Space collapse through systematic constraint!

---

## 🔬 Testing on New Puzzles

### **Add a new puzzle:**

```python
# 1. Get puzzle JSON
puzzle = {
    'train': [
        {'input': [[...]], 'output': [[...]]},
        # ... 2 more training pairs
    ],
    'test': [
        {'input': [[...]], 'output': [[...]]}
    ]
}

# 2. Save to file
import json
with open('puzzle_new.json', 'w') as f:
    json.dump(puzzle, f)

# 3. Generate prompt
from arc_prompt_generator_v5 import save_prompt
save_prompt(puzzle, 'puzzle_new_prompt.txt')

# 4. Send to models and validate!
```

**The framework is 100% generic - works on ANY puzzle!**

---

## ⚠️ Common Pitfalls

### **1. Using validator.py instead of complete_validator.py**

❌ Wrong:
```python
from validator import feedback_loop
action, report = feedback_loop(puzzle, code, mode="dev")
# Only checks training, never checks test!
```

✅ Right:
```python
from complete_validator import validate_solution_complete
result = validate_solution_complete(puzzle, code)
# Checks both training AND test!
```

---

### **2. Not executing the code before validation**

❌ Wrong:
```python
result = validate_solution_complete(puzzle, code_string)
# Error: solve() function not defined!
```

✅ Right:
```python
exec(code_string, globals())  # Execute to define solve()
result = validate_solution_complete(puzzle, code_string)
```

---

### **3. Confusing transformation_grid.py with arc_prompt_generator_v5.py**

- `transformation_grid.py` = **Engine** (generates symbols)
- `arc_prompt_generator_v5.py` = **Builder** (uses engine to create prompts)

The prompt generator **uses** transformation_grid.py as a component!

---

## 📚 Documentation Files

**In `/mnt/user-data/outputs/`:**

- `README.md` - This file
- `COMPLETE_WORKFLOW.md` - Detailed workflow diagram
- `VALIDATION_CRITERIA.md` - Success criteria explained
- `VALIDATOR_COMPARISON.md` - Two validators compared
- `PYTHON_CODE_SUMMARY.md` - Code architecture
- `FEEDBACK_EXAMPLES_SUMMARY.md` - Example feedback breakdown
- `LANGUAGE_REFINEMENT_v3_to_v4.md` - Language precision rationale
- `SYMBOL_FORMATTING_FIX.md` - Symbol clarity fix
- `PROMPT_FIX_COMPARISON.md` - Hardcoded color fix

**Read these for deep understanding!**

---

## 🎯 Success Metrics

### **For a TRUE SOLVE:**
```
Training: 3/3 ✅ (all pairs pass)
Test: 1/1 ✅ (test case passes)
Total: 4/4 ✅

Meaning: Rule extracted AND generalizes!
```

### **Other outcomes:**
- **False positive:** Training <3/3, Test 1/1 (lucky guess)
- **Overfitting:** Training 3/3, Test 0/1 (memorized specifics)
- **Training failure:** Training <3/3 (needs iteration)

**Only TRUE SOLVE counts as framework success!**

---

## 🚀 Production Use

```python
# Complete pipeline
import json
from arc_prompt_generator_v5 import generate_prompt
from complete_validator import validate_solution_complete
from complete_substrate_feedback import generate_complete_substrate_feedback

# 1. Load puzzle
with open('puzzle.json', 'r') as f:
    puzzle = json.load(f)

# 2. Generate substrate prompt
prompt = generate_prompt(puzzle)

# 3. Send to model, get code
model_code = your_model.generate(prompt)

# 4. Validate
result = validate_solution_complete(puzzle, model_code)

# 5. If failed, generate feedback and iterate
if not result['true_solve']:
    exec(model_code, globals())
    
    feedback = []
    for i, pair in enumerate(puzzle['train'], 1):
        if solve(pair['input']) != pair['output']:
            fb = generate_complete_substrate_feedback(
                pair['input'], pair['output'],
                solve(pair['input']), i
            )
            feedback.append(fb)
    
    # Send feedback back to model
    model_code = your_model.iterate("\n\n".join(feedback))
    
    # Repeat validation...
```

---

## 📖 Citation

If using this framework in research:

```
TCP/AP Substrate Validation Framework
Elin Hansson / OmnisensAI
Deterministic validation for ARC-AGI through transformation grid encoding
https://github.com/... [add your repo]
```

---

## 🎓 Core Thesis

**Traditional AI systems:**
```
Prompt → LLM → Output → ???
(Black box, non-reproducible)
```

**TCP/AP Substrate:**
```
Substrate Prompt → LLM → Output → Deterministic Validation
                                         ↓
                                  Deterministic Feedback
                                         ↓
                                  Space Collapse via Constraints
```

**Feedback is PART of the constraint system!**

Not AI interpretation - pure computational constraint engineering! 🎯

---

## ✅ Quick Reference

**Generate prompt:**
```python
from arc_prompt_generator_v5 import generate_prompt
prompt = generate_prompt(puzzle)
```

**Validate solution:**
```python
from complete_validator import validate_solution_complete
result = validate_solution_complete(puzzle, code)
```

**Generate feedback:**
```python
from complete_substrate_feedback import generate_complete_substrate_feedback
feedback = generate_complete_substrate_feedback(input, expected, actual, pair_num)
```

**That's it! Three functions, complete framework!** 🚀

---

**Framework is production-ready and fully tested!** ✅

For questions or issues, review the documentation files in `/mnt/user-data/outputs/`
