"""Extract Run 1 training metrics from Axolotl's trainer_state.json and write
a human-readable summary + a CSV of all per-step metrics.

Run from the repo root AFTER training finishes:

    python3 Phase2_V2/run1/summarize_run.py

Reads:
  outputs/phase2_v2_run1/checkpoint-<last>/trainer_state.json

Writes:
  outputs/phase2_v2_run1/RUN_SUMMARY.md  (human-readable; commit this)
  outputs/phase2_v2_run1/metrics.csv     (every step, every metric)

Notes:
- Axolotl saves trainer_state.json inside each checkpoint dir. The latest
  checkpoint has the complete log_history covering the entire run.
- The summary picks out training-loss samples, all eval points, the loss
  trajectory, and a per-checkpoint table for later A/B selection.
"""
import csv, json, sys
from pathlib import Path


def find_latest_state(out_dir: Path) -> Path:
    """Return trainer_state.json from the latest checkpoint dir."""
    ckpts = sorted(out_dir.glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[1]))
    if not ckpts:
        sys.exit(f"no checkpoints found in {out_dir}")
    return ckpts[-1] / "trainer_state.json"


def main():
    out_dir = Path("outputs/phase2_v2_run1")
    state_path = find_latest_state(out_dir)
    state = json.loads(state_path.read_text())

    log = state["log_history"]                # list of dicts, one per logging step
    train_rows = [r for r in log if "loss" in r and "eval_loss" not in r]
    eval_rows  = [r for r in log if "eval_loss" in r]

    # --------------- write metrics.csv ---------------
    csv_path = out_dir / "metrics.csv"
    all_keys = sorted({k for r in log for k in r.keys()})
    with csv_path.open("w") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_keys)
        writer.writeheader()
        for r in log:
            writer.writerow(r)
    print(f"wrote {csv_path}  ({len(log)} rows)")

    # --------------- write RUN_SUMMARY.md ---------------
    md = out_dir / "RUN_SUMMARY.md"
    lines = []
    lines.append("# Phase2_V2 Run 1 — Training Summary")
    lines.append("")
    lines.append("Generated from `trainer_state.json` of the latest checkpoint.")
    lines.append("")

    # ---- run config (from trainer_state)
    lines.append("## Run configuration")
    lines.append("")
    cfg_keys = ["max_steps", "num_train_epochs", "global_step",
                "best_metric", "best_model_checkpoint",
                "total_flos"]
    for k in cfg_keys:
        if k in state:
            lines.append(f"- **{k}**: {state[k]}")
    lines.append("")

    # ---- eval trajectory (the headline)
    lines.append("## Eval trajectory")
    lines.append("")
    lines.append("| step | epoch | eval_loss | eval_ppl |")
    lines.append("|---:|---:|---:|---:|")
    for r in eval_rows:
        step = r.get("step", "?")
        epoch = r.get("epoch", "?")
        if isinstance(epoch, float):
            epoch = f"{epoch:.3f}"
        el = r.get("eval_loss", "?")
        pp = r.get("eval_ppl", "?")
        lines.append(f"| {step} | {epoch} | {el} | {pp} |")
    lines.append("")

    # ---- training loss sampling (every 100 steps)
    lines.append("## Training loss (sampled every ~100 steps)")
    lines.append("")
    lines.append("| step | epoch | loss | lr | grad_norm |")
    lines.append("|---:|---:|---:|---:|---:|")
    last_logged_step = -100
    for r in train_rows:
        step = r.get("step", 0)
        if isinstance(step, int) and step >= last_logged_step + 100:
            last_logged_step = step
            epoch = r.get("epoch", "?")
            if isinstance(epoch, float):
                epoch = f"{epoch:.3f}"
            loss = r.get("loss", "?")
            lr   = r.get("learning_rate", "?")
            gn   = r.get("grad_norm", "?")
            lines.append(f"| {step} | {epoch} | {loss} | {lr} | {gn} |")
    lines.append("")

    # ---- final metrics
    lines.append("## Final metrics")
    lines.append("")
    if train_rows:
        last = train_rows[-1]
        lines.append("**Final training step:**")
        for k in ("step", "epoch", "loss", "learning_rate", "grad_norm"):
            v = last.get(k)
            if v is not None:
                lines.append(f"- {k}: {v}")
        lines.append("")
    if eval_rows:
        best_eval = min(eval_rows, key=lambda r: float(r.get("eval_loss", 1e9)))
        last_eval = eval_rows[-1]
        lines.append("**Best eval:**")
        for k in ("step", "epoch", "eval_loss", "eval_ppl"):
            v = best_eval.get(k)
            if v is not None:
                lines.append(f"- {k}: {v}")
        lines.append("")
        lines.append("**Last eval:**")
        for k in ("step", "epoch", "eval_loss", "eval_ppl"):
            v = last_eval.get(k)
            if v is not None:
                lines.append(f"- {k}: {v}")
        lines.append("")

    # ---- checkpoints saved
    lines.append("## Saved checkpoints")
    lines.append("")
    ckpts = sorted(out_dir.glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[1]))
    lines.append("| checkpoint | path |")
    lines.append("|---|---|")
    for c in ckpts:
        lines.append(f"| {c.name} | `{c.relative_to(Path.cwd()) if c.is_absolute() else c}` |")
    lines.append("")

    # ---- explainer footer
    lines.append("## How to use this")
    lines.append("")
    lines.append("- Eval trajectory shows where the model plateaued and which checkpoints")
    lines.append("  bracket the best generalization. Take 2-3 nearby late-stage checkpoints")
    lines.append("  for the bucket 2 A/B.")
    lines.append("- `metrics.csv` has every step's metrics for plotting / deeper analysis.")
    lines.append("- `trainer_state.json` in the final checkpoint dir is the canonical source.")
    lines.append("")

    md.write_text("\n".join(lines))
    print(f"wrote {md}  ({len(lines)} lines)")


if __name__ == "__main__":
    main()
