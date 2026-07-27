#!/usr/bin/env python3
"""
clip_stats_sync.py

Sync project-level and chapter-level clip stats into:
- .novel-studio/state.json
- .novel-studio/chapter-meta.json

This is conservative but helpful:
- preserves unrelated fields
- adds/updates clip-related summary fields
- auto-creates minimal chapter-meta entries for chapters implied by active files/clips
- excludes retired assets under chapters/retired/
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

STATUS_BY_DIR = {
    "published": "published",
    "candidates": "candidate",
    "early-drafts": "draft",
    "drafts": "draft",
    "revisions": "reference",
}


def load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    return items


def collect_chapter_file_statuses(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for dirname, status in STATUS_BY_DIR.items():
        folder = root / "chapters" / dirname
        if not folder.exists():
            continue
        for path in sorted(folder.glob("ch_*.md")):
            cid = path.name.split("-")[0]
            out.setdefault(cid, status)
    return out


def chapter_status_counts(chapter_statuses: dict[str, str]) -> dict[str, int]:
    return {
        "chapters_published": len([x for x in chapter_statuses.values() if x == "published"]),
        "chapters_candidate": len([x for x in chapter_statuses.values() if x == "candidate"]),
        "chapters_draft": len([x for x in chapter_statuses.values() if x == "draft"]),
        "chapters_reference_only": len([x for x in chapter_statuses.values() if x == "reference"]),
    }


def ensure_meta_entry(chapters: list[dict], chapter_id: str, status: str) -> dict:
    for item in chapters:
        if isinstance(item, dict) and item.get("id") == chapter_id:
            if not item.get("status"):
                item["status"] = status
            return item
    item = {
        "id": chapter_id,
        "title": chapter_id,
        "status": status,
        "summary": "",
        "hasPacket": False,
        "hasSummary": False,
        "cardsUpdated": False,
        "timeAnchor": "",
        "clipStats": {
            "total": 0,
            "active": 0,
            "merged": 0,
            "archived": 0,
            "discarded": 0,
        },
    }
    chapters.append(item)
    return item


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: clip_stats_sync.py <project-dir>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    state_path = root / ".novel-studio" / "state.json"
    meta_path = root / ".novel-studio" / "chapter-meta.json"

    state = load_json(state_path, {})
    meta = load_json(meta_path, {"chapters": []})
    clips = collect_clips(root)
    chapter_statuses = collect_chapter_file_statuses(root)

    project_stats = {
        "clips_total": len(clips),
        "clips_active": len([x for x in clips if x.get("status") == "active"]),
        "clips_merged": len([x for x in clips if x.get("status") == "merged"]),
        "clips_archived": len([x for x in clips if x.get("status") == "archived"]),
        "clips_discarded": len([x for x in clips if x.get("status") == "discarded"]),
        "clips_unassigned": len([x for x in clips if x.get("chapter") == "unassigned"]),
    }

    summary = state.get("summary") if isinstance(state.get("summary"), dict) else {}
    summary.update(chapter_status_counts(chapter_statuses))
    summary.update(project_stats)
    state["summary"] = summary

    chapters = meta.get("chapters") if isinstance(meta.get("chapters"), list) else []
    by_chapter: dict[str, list[dict]] = {}
    chapter_ids = set(chapter_statuses)
    for item in clips:
        ch = item.get("chapter")
        if not ch or ch == "unassigned":
            continue
        by_chapter.setdefault(ch, []).append(item)
        chapter_ids.add(ch)

    for cid in sorted(chapter_ids):
        entry = ensure_meta_entry(chapters, cid, chapter_statuses.get(cid, "draft"))
        items = by_chapter.get(cid, [])
        entry["clipStats"] = {
            "total": len(items),
            "active": len([x for x in items if x.get("status") == "active"]),
            "merged": len([x for x in items if x.get("status") == "merged"]),
            "archived": len([x for x in items if x.get("status") == "archived"]),
            "discarded": len([x for x in items if x.get("status") == "discarded"]),
        }
        entry["hasPacket"] = (root / ".novel-studio" / "packets" / f"{cid}-packet.md").exists()
        entry["hasSummary"] = (root / ".novel-studio" / "summaries" / f"{cid}-summary.md").exists()

    meta["chapters"] = sorted(chapters, key=lambda x: x.get("id", ""))

    save_json(state_path, state)
    save_json(meta_path, meta)
    print(f"synced clip stats into: {state_path}")
    print(f"synced clip stats into: {meta_path}")
    print(f"chapter-meta entries now: {len(meta['chapters'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
