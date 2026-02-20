from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


@dataclass(frozen=True)
class Paths:
    work_dir: Path
    recordings_dir: Path
    dataset_dir: Path
    out_dir: Path


@dataclass(frozen=True)
class PromptsCfg:
    file: Path
    count: int = 120
    randomize: bool = True


@dataclass(frozen=True)
class AudioCfg:
    target_sr: int = 22050
    target_channels: int = 1
    target_format: str = "wav"
    normalize: bool = True
    trim_silence: bool = True


@dataclass(frozen=True)
class TrainingCfg:
    training_repo_path: Path
    run_kind: str = "single_speaker"
    epochs: int = 200
    batch_size: int = 16
    learning_rate: float = 2e-4
    use_cuda: bool = True


@dataclass(frozen=True)
class ExportCfg:
    onnx_opset: int = 17
    simplify_onnx: bool = True


@dataclass(frozen=True)
class SuiteConfig:
    voice_id: str
    language: str
    sample_rate: int
    paths: Paths
    prompts: PromptsCfg
    audio: AudioCfg
    training: TrainingCfg
    export: ExportCfg


def _p(v: Any) -> Path:
    return Path(str(v)).expanduser().resolve()


def load_config(path: str | Path) -> SuiteConfig:
    cfg_path = _p(path)
    data: Dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    voice_id = str(data["voice_id"])
    language = str(data.get("language", "en_US"))
    sample_rate = int(data.get("sample_rate", 22050))

    paths = data["paths"]
    prompts = data["prompts"]
    audio = data.get("audio", {})
    training = data["training"]
    export = data.get("export", {})

    return SuiteConfig(
        voice_id=voice_id,
        language=language,
        sample_rate=sample_rate,
        paths=Paths(
            work_dir=_p(paths["work_dir"]),
            recordings_dir=_p(paths["recordings_dir"]),
            dataset_dir=_p(paths["dataset_dir"]),
            out_dir=_p(paths["out_dir"]),
        ),
        prompts=PromptsCfg(
            file=_p(prompts["file"]),
            count=int(prompts.get("count", 120)),
            randomize=bool(prompts.get("randomize", True)),
        ),
        audio=AudioCfg(
            target_sr=int(audio.get("target_sr", 22050)),
            target_channels=int(audio.get("target_channels", 1)),
            target_format=str(audio.get("target_format", "wav")),
            normalize=bool(audio.get("normalize", True)),
            trim_silence=bool(audio.get("trim_silence", True)),
        ),
        training=TrainingCfg(
            training_repo_path=_p(training["training_repo_path"]),
            run_kind=str(training.get("run_kind", "single_speaker")),
            epochs=int(training.get("epochs", 200)),
            batch_size=int(training.get("batch_size", 16)),
            learning_rate=float(training.get("learning_rate", 2e-4)),
            use_cuda=bool(training.get("use_cuda", True)),
        ),
        export=ExportCfg(
            onnx_opset=int(export.get("onnx_opset", 17)),
            simplify_onnx=bool(export.get("simplify_onnx", True)),
        ),
    )