#!/usr/bin/env python3
"""
clip_overview.py

Project-level Clip overviews for Novel Studio.
Currently supports:
- unassigned: all clips with chapter=unassigned
- all: full project clip listing
"""

from __future__ import annotations

from pathlib import Path
import json
import sys


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


def build(root: Path, mode: str) -> tuple[dict, str, str]:
    all_clips = collect_clips(root)
    if mode == "unassigned":
        clips = [x for x in all_clips if x.get("chapter") == "unassigned"]
        title = "Unassigned Clip Overview"
        basename = "clip-overview-unassigned"
    else:
        clips = all_clips
        title = "All Clip Overview"
        basename = "clip-overview-all"

    stats = {
        "total": len(clips),
        "active": len([x for x in clips if x.get("status") == "active"]),
        "merged": len([x for x in clips if x.get("status") == "merged"]),
        "archived": len([x for x in clips if x.get("status") == "archived"]),
        "discarded": len([x for x in clips if x.get("status") == "discarded"]),
    }

    data = {
        "mode": mode,
        "stats": stats,
        "clips": clips,
    }

    lines = [f"# {title}", ""]
    lines += ["## Stats", ""]
    for k, v in stats.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Clips", ""]
    if clips:
        for item in clips:
            line = f"- {item['title']} (`{item['slug']}`) — chapter={item['chapter']}, status={item['status']}"
            if item.get("status") == "merged" and item.get("merged_into"):
                line += f", merged_into={item['merged_into']}"
            lines.append(line)
            if item.get("tags"):
                lines.append(f"  - tags: {', '.join(item['tags'])}")
            lines.append(f"  - path: `{item['path']}`")
    else:
        lines.append("- None")

    return data, "\n".join(lines) + "\n", basename


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: clip_overview.py <project-dir> <unassigned|all>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    mode = sys.argv[2]
    if mode not in {"unassigned", "all"}:
        print("mode must be one of: unassigned | all")
        return 1
    data, markdown, basename = build(root, mode)
    out_md = root / ".novel-studio" / "logs" / f"{basename}.md"
    out_json = root / ".novel-studio" / "logs" / f"{basename}.json"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown, encoding="utf-8")
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote clip overview: {out_md}")
    print(f"wrote clip overview json: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
