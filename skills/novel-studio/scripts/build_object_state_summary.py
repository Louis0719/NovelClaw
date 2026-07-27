#!/usr/bin/env python3
"""
build_object_state_summary.py

Create a chapter-scoped object state summary scaffold based on packet object lists.
Current version combines recent change, stable state, and a light carry-over hint
from the chapter summary when a matching object name appears.
"""

from pathlib import Path
import sys


def extract_items(packet: Path, section_name: str):
    if not packet.exists():
        return []
    lines = packet.read_text().splitlines()
    items = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped == f"### {section_name}":
            capture = True
            continue
        if capture and stripped.startswith("### "):
            break
        if capture and stripped.startswith("- "):
            item = stripped[2:].strip()
            if item:
                items.append(item)
    return items


def match_card(folder: Path, item: str) -> Path | None:
    if not folder.exists() or not item:
        return None
    item_lower = item.lower()
    for p in sorted(folder.glob("*.md")):
        stem = p.stem.lower()
        if stem in {"readme", "scene-index"}:
            continue
        if item_lower in stem:
            return p
    return None


def match_change_log(folder: Path, item: str) -> Path | None:
    if not folder.exists() or not item:
        return None
    item_lower = item.lower()
    for p in sorted(folder.glob("*.md")):
        stem = p.stem.lower()
        if item_lower in stem:
            return p
    return None


def extract_hint(path: Path) -> str:
    if not path or not path.exists():
        return ""
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped[2:].strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            return stripped
    return ""


def extract_latest_change(path: Path) -> str:
    if not path or not path.exists():
        return ""
    bullets = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets[-1] if bullets else ""


def extract_summary_hint(path: Path, item: str) -> str:
    if not path or not path.exists() or not item:
        return ""
    item_lower = item.lower()
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if item_lower in stripped.lower() and stripped and not stripped.startswith("#"):
            return stripped.lstrip("- ").strip()
    return ""


def block(title: str, items: list[str], card_folder: Path, change_folder: Path, summary: Path):
    lines = [title, ""]
    if not items:
        lines.append("- ")
        return lines
    for item in items:
        card = match_card(card_folder, item)
        change = match_change_log(change_folder, item)
        hint = extract_hint(card) if card else ""
        latest = extract_latest_change(change) if change else ""
        carry = extract_summary_hint(summary, item)

        lines.append(f"- {item}")
        if latest:
            lines.append(f"  - 最近变化：{latest}{f'（参考 `{change.name}`）' if change else ''}")
        else:
            lines.append("  - 最近变化：")
        if hint:
            lines.append(f"  - 当前稳定状态：{hint}{f'（参考 `{card.name}`）' if card else ''}")
        else:
            lines.append("  - 当前稳定状态：")
        if carry:
            lines.append(f"  - 上一章承接结果：{carry}{f'（参考 `{summary.name}`）' if summary.exists() else ''}")
        else:
            lines.append("  - 上一章承接结果：")
        lines.append("  - 本章约束：")
    return lines


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: build_object_state_summary.py <project-dir> <chapter-id>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md"
    out = root / ".novel-studio" / "summaries" / f"{chapter_id}-objects.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    chars = extract_items(packet, "人物")
    events = extract_items(packet, "事件")
    spaces = extract_items(packet, "空间")
    scenes = extract_items(packet, "场景")

    char_dir = root / "settings" / "subsettings" / "characters"
    char_changes = char_dir / "changes"
    event_dir = root / "settings" / "subsettings" / "events"
    event_changes = event_dir / "changes"
    space_dir = root / "settings" / "subsettings" / "spaces" / "cards"
    space_changes = root / "settings" / "subsettings" / "spaces" / "changes"
    scene_dir = root / "settings" / "subsettings" / "scenes" / "cards"
    scene_changes = root / "settings" / "subsettings" / "scenes" / "changes"

    lines = [f"# {chapter_id} 对象状态摘要", ""]
    lines += block("## 一、相关人物当前状态", chars, char_dir, char_changes, summary)
    lines += [""]
    lines += block("## 二、相关事件当前状态", events, event_dir, event_changes, summary)
    lines += [""]
    lines += block("## 三、相关空间当前状态", spaces, space_dir, space_changes, summary)
    lines += [""]
    lines += block("## 四、相关场景当前状态", scenes, scene_dir, scene_changes, summary)
    lines += ["", "## 五、这一章最该记住的对象约束", "- ", "- ", "- ", ""]

    out.write_text("\n".join(lines))
    print(f"prepared object state summary scaffold: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
