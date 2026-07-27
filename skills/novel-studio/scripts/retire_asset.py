#!/usr/bin/env python3
"""
retire_asset.py

Move chapter-side assets into chapters/retired/ so they no longer participate
in active creation workflows.

Supported kinds:
- chapter: move from published/candidates/early-drafts/drafts/revisions -> retired/
- clip: move from clips/ -> retired/clips/
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys


ACTIVE_CHAPTER_DIRS = ["published", "candidates", "early-drafts", "drafts", "revisions"]


def find_chapter(root: Path, ref: str) -> Path | None:
    for dirname in ACTIVE_CHAPTER_DIRS:
        folder = root / "chapters" / dirname
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            if path.stem == ref or path.name == ref or path.name.startswith(ref + "-"):
                return path
    return None


def find_clip(root: Path, ref: str) -> Path | None:
    folder = root / "chapters" / "clips"
    if not folder.exists():
        return None
    direct = folder / (ref if ref.endswith(".md") else f"{ref}.md")
    if direct.exists():
        return direct
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if f"title: {ref}" in text:
            return path
    return None


def retire_chapter(root: Path, ref: str) -> int:
    path = find_chapter(root, ref)
    if not path:
        print(f"chapter not found: {ref}")
        return 2
    target_dir = root / "chapters" / "retired"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    shutil.move(str(path), str(target))
    print(f"retired chapter: {target}")
    return 0


def retire_clip(root: Path, ref: str) -> int:
    path = find_clip(root, ref)
    if not path:
        print(f"clip not found: {ref}")
        return 2
    target_dir = root / "chapters" / "retired" / "clips"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    shutil.move(str(path), str(target))
    print(f"retired clip: {target}")
    return 0


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: retire_asset.py <project-dir> <chapter|clip> <ref>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    kind = sys.argv[2]
    ref = sys.argv[3]
    if kind == "chapter":
        return retire_chapter(root, ref)
    if kind == "clip":
        return retire_clip(root, ref)
    print("kind must be one of: chapter | clip")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
