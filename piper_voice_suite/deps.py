from __future__ import annotations
from pathlib import Path
from .utils import which


def assert_deps() -> None:
    missing = []
    for exe in ["ffmpeg", "ffprobe"]:
        if which(exe) is None:
            missing.append(exe)
    if missing:
        raise RuntimeError(
            "Missing dependencies in PATH: " + ", ".join(missing) + "\n"
            "Install ffmpeg and ensure it is available in your shell PATH."
        )