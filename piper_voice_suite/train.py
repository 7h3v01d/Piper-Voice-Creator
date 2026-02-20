from __future__ import annotations
from pathlib import Path
from .config import SuiteConfig
from .utils import run, ensure_dir


def train_voice(cfg: SuiteConfig) -> Path:
    """
    Calls into an external training repo.
    You must point `training_repo_path` at a repo that contains training scripts.

    This wrapper looks for a script named `train.py` or `train.sh` inside that repo.
    Adjust as needed for the repo you use.
    """
    repo = cfg.training.training_repo_path
    if not repo.exists():
        raise RuntimeError(f"Training repo not found: {repo}")

    ensure_dir(cfg.paths.work_dir)
    ensure_dir(cfg.paths.out_dir)

    # Output checkpoint dir
    ckpt_dir = cfg.paths.work_dir / "checkpoints" / cfg.voice_id
    ensure_dir(ckpt_dir)

    # Common environment flags
    env = {}
    if not cfg.training.use_cuda:
        env["CUDA_VISIBLE_DEVICES"] = ""

    # Heuristic: try train.py first
    train_py = repo / "train.py"
    train_sh = repo / "train.sh"

    if train_py.exists():
        cmd = [
            "python", str(train_py),
            "--dataset", str(cfg.paths.dataset_dir),
            "--voice-id", cfg.voice_id,
            "--epochs", str(cfg.training.epochs),
            "--batch-size", str(cfg.training.batch_size),
            "--learning-rate", str(cfg.training.learning_rate),
            "--out", str(ckpt_dir),
        ]
        run(cmd, cwd=repo, env=env)
    elif train_sh.exists():
        cmd = [
            "bash", str(train_sh),
            str(cfg.paths.dataset_dir),
            cfg.voice_id,
            str(cfg.training.epochs),
            str(cfg.training.batch_size),
            str(cfg.training.learning_rate),
            str(ckpt_dir),
        ]
        run(cmd, cwd=repo, env=env)
    else:
        raise RuntimeError(
            "Could not find train.py or train.sh in training repo.\n"
            "Point training_repo_path at a Piper/VITS training repo and/or edit piper_voice_suite/train.py."
        )

    print(f"✅ Training complete (or launched). Checkpoints: {ckpt_dir}")
    return ckpt_dir