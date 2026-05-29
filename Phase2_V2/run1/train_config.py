"""Phase2_V2 Run 1 training config.

ONE LoRA on the L2 same-size corpus only. No L1 micro, no diff-size, no synthetic
repair. The training corpus is the union of:

  Phase2_V2/canonical/sft/real_samesize_original.jsonl       (~2,081 records)
  Phase2_V2/canonical/sft/real_samesize_augmented_shard0[0-3].jsonl
                                                              (~29,645 records)

Total: ~31,726 SFT records.

Held-out (NEVER in training):
  bucket1: trained sample (200) -- for "did it learn" sanity
  bucket2: 43 same-size puzzles -- transfer signal; failure-collect for Phase 3
  bucket3: 364 diff-size puzzles -- cold probe; failure-collect for Phase 3
"""
from dataclasses import dataclass, field


@dataclass
class Run1Config:
    # === model ===
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # === LoRA ===
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    lora_target_modules: tuple = (
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    )

    # === data ===
    train_files: tuple = (
        "Phase2_V2/canonical/sft/real_samesize_original.jsonl",
        "Phase2_V2/canonical/sft/real_samesize_augmented_shard00.jsonl",
        "Phase2_V2/canonical/sft/real_samesize_augmented_shard01.jsonl",
        "Phase2_V2/canonical/sft/real_samesize_augmented_shard02.jsonl",
        "Phase2_V2/canonical/sft/real_samesize_augmented_shard03.jsonl",
    )
    # Held-out puzzle ids -- any SFT record whose meta.puzzle is in this set
    # is FILTERED OUT of training at dataloader time.
    heldout_split_files: tuple = (
        "Phase2_V2/run1/splits/bucket2_heldout_samesize.txt",
        "Phase2_V2/run1/splits/bucket3_cold_diffsize.txt",
    )

    # === train hyperparams (single-GPU defaults; tune for cluster) ===
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    lr_scheduler_type: str = "cosine"

    # === seq lengths / format ===
    max_seq_length: int = 4096   # most records fit; long-tail truncated right
    train_on_completions_only: bool = True   # mask SYSTEM + USER; loss on ASSISTANT only

    # === checkpointing / output ===
    output_dir: str = "Phase2_V2/run1/lora_out/"
    save_strategy: str = "epoch"
    logging_steps: int = 50
    seed: int = 0


def load_heldout_ids() -> set:
    """Union of all puzzle ids that must NEVER appear in training."""
    cfg = Run1Config()
    held = set()
    for path in cfg.heldout_split_files:
        with open(path) as f:
            held |= {line.strip() for line in f if line.strip()}
    return held


if __name__ == "__main__":
    cfg = Run1Config()
    held = load_heldout_ids()
    print(f"base model:    {cfg.base_model}")
    print(f"LoRA r={cfg.lora_r}, alpha={cfg.lora_alpha}, dropout={cfg.lora_dropout}")
    print(f"target modules: {cfg.lora_target_modules}")
    print(f"epochs={cfg.num_train_epochs}, bs={cfg.per_device_train_batch_size}"
          f" x grad_accum {cfg.gradient_accumulation_steps}, lr={cfg.learning_rate}")
    print(f"max_seq_length: {cfg.max_seq_length}")
    print(f"train files:")
    for f in cfg.train_files:
        print(f"  {f}")
    print(f"held-out puzzle ids (excluded from training): {len(held)}")
