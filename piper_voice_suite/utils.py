from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional


class CmdError(RuntimeError):
    pass


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def which(exe: str) -> Optional[str]:
    return shutil.which(exe)


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise CmdError(f"Command failed ({proc.returncode}): {' '.join(cmd)}\n\n{proc.stdout}")
    print(proc.stdout)


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def read_lines(path: Path) -> list[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]