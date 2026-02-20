from __future__ import annotations
import csv
from pathlib import Path
from typing import Iterable, Tuple

from .config import SuiteConfig
from .deps import assert_deps
from .utils import ensure_dir, run, CmdError, read_lines


def _ffmpeg_process(in_wav: Path, out_wav: Path, sr: int, ch: int, normalize: bool, trim_silence: bool) -> None:
    # Build a simple filter chain.
    filters = []
    if trim_silence:
        # conservative silence trim
        filters.append("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1")
        filters.append("silenceremove=stop_periods=1:stop_threshold=-45dB:stop_silence=0.1")
    if normalize:
        filters.append("loudnorm=I=-18:TP=-1.5:LRA=11")

    cmd = ["ffmpeg", "-y", "-i", str(in_wav), "-ac", str(ch), "-ar", str(sr)]
    if filters:
        cmd += ["-af", ",".join(filters)]
    cmd += [str(out_wav)]
    run(cmd)


def build_ljspeech_dataset(cfg: SuiteConfig) -> None:
    """
    Builds:
      dataset_dir/
        wavs/000001.wav ...
        metadata.csv  (LJSpeech format: <id>|<text>|<text>)
    Inputs expected:
      recordings_dir/
        takes/<idx>.wav
        takes/<idx>.txt  (same idx, contains transcript)
    """
    assert_deps()
    ensure_dir(cfg.paths.dataset_dir)
    wavs_dir = cfg.paths.dataset_dir / "wavs"
    ensure_dir(wavs_dir)

    takes_dir = cfg.paths.recordings_dir / "takes"
    if not takes_dir.exists():
        raise RuntimeError(f"No recordings found at: {takes_dir}")

    # Collect takes by idx
    wav_files = sorted(takes_dir.glob("*.wav"))
    if not wav_files:
        raise RuntimeError(f"No .wav takes found in: {takes_dir}")

    rows: list[Tuple[str, str, str]] = []
    for wav in wav_files:
        stem = wav.stem
        txt = takes_dir / f"{stem}.txt"
        if not txt.exists():
            raise RuntimeError(f"Missing transcript for {wav.name}: expected {txt.name}")

        text = txt.read_text(encoding="utf-8").strip()
        if not text:
            raise RuntimeError(f"Empty transcript for take {stem}")

        out_id = f"{int(stem):06d}"
        out_wav = wavs_dir / f"{out_id}.wav"
        _ffmpeg_process(
            wav, out_wav,
            sr=cfg.audio.target_sr,
            ch=cfg.audio.target_channels,
            normalize=cfg.audio.normalize,
            trim_silence=cfg.audio.trim_silence
        )
        rows.append((out_id, text, text))

    meta = cfg.paths.dataset_dir / "metadata.csv"
    with meta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="|", quoting=csv.QUOTE_MINIMAL)
        for r in rows:
            w.writerow(r)

    print(f"✅ Dataset built: {cfg.paths.dataset_dir}")
    print(f"   wavs: {wavs_dir}")
    print(f"   metadata: {meta}")


def validate_dataset(cfg: SuiteConfig) -> None:
    meta = cfg.paths.dataset_dir / "metadata.csv"
    wavs_dir = cfg.paths.dataset_dir / "wavs"
    if not meta.exists():
        raise RuntimeError(f"metadata.csv not found: {meta}")
    if not wavs_dir.exists():
        raise RuntimeError(f"wavs/ not found: {wavs_dir}")

    # Basic checks
    lines = meta.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise RuntimeError("metadata.csv is empty")

    missing_wavs = []
    for ln in lines[:2000]:  # cap
        parts = ln.split("|")
        if len(parts) < 2:
            raise RuntimeError(f"Bad metadata row: {ln}")
        fid = parts[0]
        wav = wavs_dir / f"{fid}.wav"
        if not wav.exists():
            missing_wavs.append(fid)

    if missing_wavs:
        raise RuntimeError(f"Missing wav files for ids: {missing_wavs[:20]} ...")

    print(f"✅ Dataset looks OK: {cfg.paths.dataset_dir} (rows={len(lines)})")