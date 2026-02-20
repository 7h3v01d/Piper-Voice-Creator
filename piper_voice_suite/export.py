from __future__ import annotations
from pathlib import Path
import json

from .config import SuiteConfig
from .utils import ensure_dir, run


def export_onnx(cfg: SuiteConfig, checkpoint_dir: Path) -> tuple[Path, Path]:
    """
    Exports a trained checkpoint to:
      model.onnx
      model.onnx.json

    This wrapper expects the training repo to provide an export script.
    Many Piper workflows export from a .pth checkpoint to ONNX, then optionally simplify.
    """
    ensure_dir(cfg.paths.out_dir)
    out_voice = cfg.paths.out_dir / cfg.voice_id
    ensure_dir(out_voice)

    onnx_path = out_voice / "model.onnx"
    meta_path = out_voice / "model.onnx.json"

    repo = cfg.training.training_repo_path
    export_py = repo / "export_onnx.py"
    if not export_py.exists():
        raise RuntimeError(
            f"Export script not found: {export_py}\n"
            "Your training repo must provide an ONNX export script. Edit piper_voice_suite/export.py to match it."
        )

    cmd = [
        "python", str(export_py),
        "--checkpoint-dir", str(checkpoint_dir),
        "--output-onnx", str(onnx_path),
        "--opset", str(cfg.export.onnx_opset),
    ]
    run(cmd, cwd=repo)

    if cfg.export.simplify_onnx:
        # optional: onnxsim
        cmd2 = ["python", "-m", "onnxsim", str(onnx_path), str(onnx_path)]
        try:
            run(cmd2, cwd=out_voice)
        except Exception as e:
            print(f"⚠️ onnxsim not available or failed (continuing): {e}")

    # Write Piper metadata JSON (minimal, you can extend)
    meta = {
        "voice_id": cfg.voice_id,
        "language": cfg.language,
        "sample_rate": cfg.sample_rate,
        # Typical inference knobs used in Piper model cards:
        "inference": {
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "noise_w": 0.8
        }
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"✅ Exported: {onnx_path}")
    print(f"✅ Metadata: {meta_path}")
    return onnx_path, meta_path