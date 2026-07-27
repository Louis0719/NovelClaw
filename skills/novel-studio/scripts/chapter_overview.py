#!/usr/bin/env python3
"""
chapter_overview.py

Generate a chapter-scoped overview for Novel Studio, including:
- published / candidates / early-drafts / drafts / revisions
- clips assigned to this chapter
- unassigned clips view when requested
- packet / summary / objects / logs readiness

Items under chapters/retired/ are intentionally excluded from active workflow views.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

STATUS_DIRS = ["published", "candidates", "early-drafts", "drafts", "revisions"]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    raw = parts[0].splitlines()[1:]
    body = parts[1]
    data: dict = {}
    for line in raw:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "tags":
            try:
                data[key] = json.loads(value) if value else []
            except Exception:
                data[key] = []
        else:
            data[key] = value if value else None
    return data, body


def chapter_files(root: Path, chapter_id: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {name: [] for name in STATUS_DIRS}
    for dirname in STATUS_DIRS:
        folder = root / "chapters" / dirname
        if not folder.exists():
            continue
        for path in sorted(folder.glob(f"{chapter_id}*.md")):
            out[dirname].append(str(path.relative_to(root)))
    return out


def collect_clips(root: Path) -> list[dict]:
    folder = root / "chapters" / "clips"
    items: list[dict] = []
    if not folder.exists():
        return items
    for path in sorted(folder.glob("*.md")):
        data, _ = parse_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        if data.get("type") != "clip":
            continue
        items.append({
            "title": data.get("title") or path.stem,
            "slug": path.stem,
            "chapter": data.get("chapter") or "unassigned",
            "status": data.get("status") or "active",
            "updated_at": data.get("updated_at"),
            "tags": data.get("tags") or [],
            "merged_into": data.get("merged_into"),
            "path": str(path.relative_to(root)),
        })
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return items


def build_overview(root: Path, chapter_id: str) -> tuple[dict, str]:
    files = chapter_files(root, chapter_id)
    all_clips = collect_clips(root)
    clips = [item for item in all_clips if item.get("chapter") == chapter_id]
    unassigned = [item for item in all_clips if item.get("chapter") == "unassigned"]
    summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md"
    objects = root / ".novel-studio" / "summaries" / f"{chapter_id}-objects.md"
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    style_overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    writeback = root / ".novel-studio" / "logs" / f"{chapter_id}-writeback-checklist.md"

    clip_stats = {
        "total": len(clips),
        "active": len([x for x in clips if x.get("status") == "active"]),
        "merged": len([x for x in clips if x.get("status") == "merged"]),
        "archived": len([x for x in clips if x.get("status") == "archived"]),
        "discarded": len([x for x in clips if x.get("status") == "discarded"]),
        "unassigned_total": len(unassigned),
    }

    data = {
        "chapter": chapter_id,
        "chapterFiles": files,
        "clips": clips,
        "clipStats": clip_stats,
        "unassignedClipsPreview": unassigned[:10],
        "artifacts": {
            "summary": str(summary.relative_to(root)) if summary.exists() else None,
            "objects": str(objects.relative_to(root)) if objects.exists() else None,
            "packet": str(packet.relative_to(root)) if packet.exists() else None,
            "styleOverlay": str(style_overlay.relative_to(root)) if style_overlay.exists() else None,
            "writebackChecklist": str(writeback.relative_to(root)) if writeback.exists() else None,
        },
    }

    lines = [f"# {chapter_id} Chapter Overview", ""]
    lines += ["## Chapter Files", ""]
    for dirname in STATUS_DIRS:
        lines.append(f"### {dirname}")
        if files[dirname]:
            lines.extend([f"- `{item}`" for item in files[dirname]])
        else:
            lines.append("- None")
        lines.append("")

    lines += ["## Clip Stats", ""]
    lines.append(f"- total: {clip_stats['total']}")
    lines.append(f"- active: {clip_stats['active']}")
    lines.append(f"- merged: {clip_stats['merged']}")
    lines.append(f"- archived: {clip_stats['archived']}")
    lines.append(f"- discarded: {clip_stats['discarded']}")
    lines.append(f"- unassigned_total(project): {clip_stats['unassigned_total']}")

    lines += ["", "## Clips", ""]
    if clips:
        for item in clips:
            line = f"- {item['title']} (`{item['slug']}`) — status={item['status']}, updated_at={item.get('updated_at') or ''}"
            if item.get("status") == "merged" and item.get("merged_into"):
                line += f", merged_into={item['merged_into']}"
            lines.append(line)
            if item.get("tags"):
                lines.append(f"  - tags: {', '.join(item['tags'])}")
            lines.append(f"  - path: `{item['path']}`")
    else:
        lines.append("- None")

    lines += ["", "## Unassigned Clips Preview", ""]
    if unassigned:
        for item in unassigned[:10]:
            lines.append(f"- {item['title']} (`{item['slug']}`) — status={item['status']}")
            if item.get("tags"):
                lines.append(f"  - tags: {', '.join(item['tags'])}")
            lines.append(f"  - path: `{item['path']}`")
    else:
        lines.append("- None")

    lines += ["", "## Artifacts", ""]
    for key, value in data["artifacts"].items():
        lines.append(f"- {key}: `{value}`" if value else f"- {key}: None")

    return data, "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: chapter_overview.py <project-dir> <chapter-id>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    data, markdown = build_overview(root, chapter_id)
    out_md = root / ".novel-studio" / "logs" / f"{chapter_id}-chapter-overview.md"
    out_json = root / ".novel-studio" / "logs" / f"{chapter_id}-chapter-overview.json"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown, encoding="utf-8")
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote chapter overview: {out_md}")
    print(f"wrote chapter overview json: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
