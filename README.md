# Piper Voice Creator / Trainer Suite

A practical suite for:
1) Recording prompts (local web studio)
2) Building an LJSpeech-style dataset
3) Running Piper/VITS training (external training repo)
4) Exporting to Piper ONNX + metadata JSON

## Why this exists
Piper training is conceptually simple (dataset -> train -> export), but the tooling is scattered. This repo provides a repeatable, CLI-driven pipeline.

> Use only voices you have rights to record/train. Do not train or distribute voices that imitate real people without permission.

---

## Prereqs
- Python 3.10–3.12
- `ffmpeg` in PATH
- A GPU is strongly recommended for training (CUDA), but CPU can work for tiny experiments.
- A Piper training repo checkout (see below).

## Install
### Linux/macOS

```bash
scripts/venv_unix.sh
. .venv/bin/activate
pvs --help
```
### Windows (PowerShell)
```powershell
.\scripts\venv_win.ps1
. .\.venv\Scripts\Activate.ps1
pvs --help
```
### Quickstart (local recording -> dataset -> train -> export)
### A) Start the recording studio
```bash
pvs studio --config examples/voice_config.yaml
```
Open the printed URL in your browser, record prompts, then click “Finalize”.

### B) Validate dataset
```bash
pvs dataset validate --config examples/voice_config.yaml
```
### C) Train (wraps an external training repo)

1. Clone a Piper training repo and set its path in your config:

    - `training_repo_path: /path/to/piper_training_repo`

Then:
```bash
pvs train --config examples/voice_config.yaml
```

### D) Export to ONNX
```bash
pvs export --config examples/voice_config.yaml
```
Outputs:

- `out/<voice_id>/model.onnx`
- `out/<voice_id>/model.onnx.json`

## Config

See: `examples/voice_config.yaml`

## License

MIT for this suite. Your trained weights may be subject to the training repo/model licenses and dataset licenses.
