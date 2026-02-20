from __future__ import annotations
import typer
from rich import print as rprint

from .config import load_config
from .deps import assert_deps
from .studio import run_studio
from .dataset import build_ljspeech_dataset, validate_dataset
from .train import train_voice
from .export import export_onnx

app = typer.Typer(add_completion=False, help="Piper Voice Creator / Trainer Suite")


@app.command()
def studio(config: str = typer.Option(..., "--config", "-c"), host: str = "127.0.0.1", port: int = 7860):
    """Start the local recording studio web UI."""
    cfg = load_config(config)
    assert_deps()
    run_studio(cfg, host=host, port=port)


dataset_app = typer.Typer(help="Dataset commands")
app.add_typer(dataset_app, name="dataset")


@dataset_app.command("build")
def dataset_build(config: str = typer.Option(..., "--config", "-c")):
    """Build an LJSpeech-style dataset from recorded takes."""
    cfg = load_config(config)
    build_ljspeech_dataset(cfg)


@dataset_app.command("validate")
def dataset_validate(config: str = typer.Option(..., "--config", "-c")):
    """Validate dataset structure and file presence."""
    cfg = load_config(config)
    validate_dataset(cfg)


@app.command()
def train(config: str = typer.Option(..., "--config", "-c")):
    """Run/launch training using an external training repo."""
    cfg = load_config(config)
    ckpt_dir = train_voice(cfg)
    rprint(f"[green]Checkpoints:[/green] {ckpt_dir}")


@app.command()
def export(config: str = typer.Option(..., "--config", "-c"), checkpoint_dir: str = typer.Option(..., "--checkpoint-dir")):
    """Export a trained checkpoint directory to ONNX + Piper JSON."""
    cfg = load_config(config)
    onnx_path, meta_path = export_onnx(cfg, checkpoint_dir=Path(checkpoint_dir).expanduser().resolve())
    rprint(f"[green]ONNX:[/green] {onnx_path}")
    rprint(f"[green]META:[/green] {meta_path}")