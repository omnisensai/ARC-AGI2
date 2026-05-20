# Training-data samples — one per task

One representative SFT record per task, drawn from the live training files.
Code targets (C/D/E) are now comment-free and docstring-free — only
executable Python — per the design choice that unverified natural language
is risky training signal.

- **A** — [`task_A_phase1a.md`](task_A_phase1a.md) — single-pair encode (input + output -> substrate)
- **B** — [`task_B_phase1b.md`](task_B_phase1b.md) — single-pair decode (input + substrate -> output)
- **H** — [`task_H_phase1a_hierarchy.md`](task_H_phase1a_hierarchy.md) — hierarchy substrate (grid -> 3-tier frequency map)
- **M** — [`task_M_phase1_multi_pair.md`](task_M_phase1_multi_pair.md) — multi-pair encode (all pairs -> all substrates; cross-pair rule consistency)
- **C** — [`task_C_phase1_substrate_to_code.md`](task_C_phase1_substrate_to_code.md) — substrate-scaffolded code (pairs + substrates + test input -> code)
- **D** — [`task_D_phase2.md`](task_D_phase2.md) — end-to-end (pairs + test input -> code; the competition task)
- **E** — [`task_E_phase3.md`](task_E_phase3.md) — corrector (pairs + test input + wrong code + feedback -> right code)
