#!/usr/bin/env python3
"""
index_refresh.py

Refresh active indexes under .novel-studio/indexes/ from current project files.
Current behavior is intentionally conservative and file-system based.
"""

from pathlib import Path
import sys


def list_markdown_names(folder: Path, suffix_to_strip: str = ".md") -> list[str]:
    if not folder.exists():
        return []
    items = []
    for path in sorted(folder.glob("*.md")):
        name = path.name
        if suffix_to_strip and name.endswith(suffix_to_strip):
            name = name[: -len(suffix_to_strip)]
        items.append(name)
    return items


def write_index(path: Path, title: str, items: list[str], fallback: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    if items:
        lines.extend([f"- {item}" for item in items])
    else:
        lines.append(f"- {fallback}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: index_refresh.py <project-dir>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    idx_dir = root / ".novel-studio" / "indexes"
    idx_dir.mkdir(parents=True, exist_ok=True)

    char_dir = root / "settings" / "subsettings" / "characters"
    event_dir = root / "settings" / "subsettings" / "events"
    space_dir = root / "settings" / "subsettings" / "spaces" / "cards"
    scene_dir = root / "settings" / "subsettings" / "scenes" / "cards"
    clip_dir = root / "chapters" / "clips"

    characters = [n for n in list_markdown_names(char_dir) if n not in {"README"}]
    events = [n for n in list_markdown_names(event_dir) if n not in {"README"}]
    spaces = [n for n in list_markdown_names(space_dir) if n not in {"README"}]
    scenes = [n for n in list_markdown_names(scene_dir) if n not in {"README", "scene-index"}]
    clips = []
    if clip_dir.exists():
        for path in sorted(clip_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "type: clip" not in text:
                continue
            if "status: active" not in text:
                continue
            clips.append(path.stem)

    pending = []
    foreshadow_file = root / "settings" / "subsettings" / "foreshadowing" / "foreshadowing-management.md"
    if foreshadow_file.exists():
        text = foreshadow_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("- "):
                pending.append(line)
                if len(pending) >= 20:
                    break

    write_index(idx_dir / "active-characters.md", "active characters", characters, "待刷新")
    write_index(idx_dir / "active-events.md", "active events", events, "待刷新")
    write_index(idx_dir / "active-spaces.md", "active spaces", spaces, "待刷新")
    write_index(idx_dir / "active-scenes.md", "active scenes", scenes, "待刷新")
    write_index(idx_dir / "active-clips.md", "active clips", clips, "待刷新")
    write_index(idx_dir / "pending-foreshadowing.md", "pending foreshadowing", pending, "待刷新")

    print(f"refreshed indexes under: {idx_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
