from __future__ import annotations
import random
from dataclasses import dataclass
from pathlib import Path
from .utils import read_lines, ensure_dir, write_text


@dataclass(frozen=True)
class PromptItem:
    idx: int
    text: str


def load_prompts(path: Path) -> list[str]:
    return read_lines(path)


def pick_prompts(all_prompts: list[str], count: int, randomize: bool, seed: int = 1337) -> list[PromptItem]:
    if count <= 0:
        return []
    items = list(all_prompts)
    if randomize:
        rng = random.Random(seed)
        rng.shuffle(items)
    picked = items[: min(count, len(items))]
    return [PromptItem(i, t) for i, t in enumerate(picked)]


def write_prompt_manifest(out_dir: Path, prompts: list[PromptItem]) -> Path:
    ensure_dir(out_dir)
    manifest = out_dir / "prompts_manifest.txt"
    lines = [f"{p.idx}\t{p.text}" for p in prompts]
    write_text(manifest, "\n".join(lines) + "\n")
    return manifest