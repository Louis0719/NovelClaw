#!/usr/bin/env python3
"""
writeback_sync.py

Check which packet-first writeback artifacts exist for a chapter and
produce a checklist report under .novel-studio/logs/.
"""

from pathlib import Path
import json
import sys


def check(path: Path) -> bool:
    return path.exists()


def mark(ok: bool) -> str:
    return "x" if ok else " "


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: writeback_sync.py <project-dir> <chapter-id>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    logs_dir = root / ".novel-studio" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out = logs_dir / f"{chapter_id}-writeback-checklist.md"

    summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md"
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    style_overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    style_check = root / ".novel-studio" / "logs" / f"{chapter_id}-style-check.md"
    indexes_dir = root / ".novel-studio" / "indexes"
    state_json = root / ".novel-studio" / "state.json"
    meta_json = root / ".novel-studio" / "chapter-meta.json"

    items = [
        ("已更新本章 summary", check(summary), summary),
        ("已更新本章 packet", check(packet), packet),
        ("已更新本章 style overlay", check(style_overlay), style_overlay),
        ("已完成本章 style check", check(style_check), style_check),
        ("已更新 state.json", check(state_json), state_json),
        ("已更新 chapter-meta.json", check(meta_json), meta_json),
        ("已建立 indexes/", indexes_dir.exists(), indexes_dir),
    ]

    lines = [f"# {chapter_id} 回写检查", ""]
    for label, ok, path in items:
        rel = path.relative_to(root) if path.exists() or path.parent.exists() else path
        lines.append(f"- [{mark(ok)}] {label} — `{rel}`")

    lines += ["", "## 说明", "- 人物 / 事件 / 空间 / 场景变化记录当前仍以人工判断为主。", "- 该脚本当前负责检查关键 packet-first 产物是否存在。", ""]
    out.write_text("\n".join(lines))

    missing = [label for label, ok, _ in items if not ok]
    if missing:
        print("missing:")
        for label in missing:
            print("-", label)
    else:
        print(f"writeback looks complete for {chapter_id}")

    print(f"wrote checklist: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
