#!/usr/bin/env python3
"""
clip_manager.py

Minimal Clip manager for Novel Studio MVP.
Supports:
- create: create a clip under chapters/clips/
- list: list clips with filters
- show: show a clip's parsed metadata and content path
- update: update clip metadata/content
- rename: rename clip title and optionally slug
- status: controlled status transition
- merge: convenience wrapper for setting status=merged

This script is intentionally file-based and conservative.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re
import sys

ALLOWED_STATUS = {"active", "merged", "archived", "discarded"}
ALLOWED_TRANSITIONS = {
    "active": {"merged", "archived", "discarded"},
    "merged": {"active", "archived"},
    "archived": {"active", "discarded"},
    "discarded": {"active"},
}

FRONTMATTER_KEYS = [
    "type",
    "title",
    "chapter",
    "status",
    "created_at",
    "updated_at",
    "tags",
    "merged_into",
]


def now_local() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff\s-]", " ", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if not text:
        return f"clip-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    ascii_text = re.sub(r"[^a-z0-9-]", "", text).strip("-")
    if ascii_text:
        return ascii_text
    return f"clip-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def ensure_unique_slug(folder: Path, base_slug: str) -> str:
    candidate = base_slug
    n = 2
    while (folder / f"{candidate}.md").exists():
        candidate = f"{base_slug}-{n}"
        n += 1
    return candidate


def dump_frontmatter(data: dict) -> str:
    lines = ["---"]
    for key in FRONTMATTER_KEYS:
        value = data.get(key)
        if key == "tags":
            if not value:
                lines.append("tags: []")
            else:
                encoded = json.dumps(value, ensure_ascii=False)
                lines.append(f"tags: {encoded}")
        elif value is None:
            lines.append(f"{key}:")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


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
            if not value:
                data[key] = []
            else:
                try:
                    data[key] = json.loads(value)
                except json.JSONDecodeError:
                    data[key] = []
        else:
            data[key] = value if value != "" else None
    return data, body.lstrip("\n")


def load_clip(path: Path) -> tuple[dict, str]:
    data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return data, body


def save_clip(path: Path, data: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_frontmatter(data) + "\n\n" + body.rstrip() + "\n", encoding="utf-8")


def clip_dir(root: Path) -> Path:
    return root / "chapters" / "clips"


def find_clip(root: Path, ref: str) -> Path | None:
    folder = clip_dir(root)
    if not folder.exists():
        return None
    direct = folder / (ref if ref.endswith(".md") else f"{ref}.md")
    if direct.exists():
        return direct
    for path in sorted(folder.glob("*.md")):
        data, _ = load_clip(path)
        if data.get("title") == ref:
            return path
    return None


def create_clip(root: Path, title: str, chapter: str, tags: list[str], content: str) -> Path:
    folder = clip_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    slug = ensure_unique_slug(folder, slugify(title))
    path = folder / f"{slug}.md"
    now = now_local()
    data = {
        "type": "clip",
        "title": title,
        "chapter": chapter or "unassigned",
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "tags": tags or [],
        "merged_into": None,
    }
    save_clip(path, data, content or "")
    return path


def iter_clips(root: Path) -> list[tuple[Path, dict, str]]:
    folder = clip_dir(root)
    items = []
    if not folder.exists():
        return items
    for path in sorted(folder.glob("*.md")):
        data, body = load_clip(path)
        if data.get("type") != "clip":
            continue
        items.append((path, data, body))
    items.sort(key=lambda x: x[1].get("updated_at") or "", reverse=True)
    return items


def cmd_create(root: Path, argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: clip_manager.py <project-dir> create <title> [chapter] [tags_csv] [content_file_or_text]")
        return 1
    title = argv[0]
    chapter = argv[1] if len(argv) >= 2 and argv[1] else "unassigned"
    tags = [x.strip() for x in (argv[2] if len(argv) >= 3 else "").split(",") if x.strip()]
    content = argv[3] if len(argv) >= 4 else ""
    content_path = Path(content)
    if content and content_path.exists():
        content = content_path.read_text(encoding="utf-8")
    path = create_clip(root, title, chapter, tags, content)
    print(f"created clip: {path}")
    return 0


def cmd_list(root: Path, argv: list[str]) -> int:
    chapter = argv[0] if len(argv) >= 1 and argv[0] else None
    status = argv[1] if len(argv) >= 2 and argv[1] else None
    tag = argv[2] if len(argv) >= 3 and argv[2] else None
    items = []
    for path, data, _ in iter_clips(root):
        if chapter and data.get("chapter") != chapter:
            continue
        if status and data.get("status") != status:
            continue
        tags = data.get("tags") or []
        if tag and tag not in tags:
            continue
        items.append({
            "title": data.get("title"),
            "slug": path.stem,
            "chapter": data.get("chapter"),
            "status": data.get("status"),
            "updated_at": data.get("updated_at"),
            "tags": tags,
            "merged_into": data.get("merged_into"),
            "path": str(path.relative_to(root)),
        })
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


def cmd_show(root: Path, argv: list[str]) -> int:
    if not argv:
        print("usage: clip_manager.py <project-dir> show <title_or_slug>")
        return 1
    path = find_clip(root, argv[0])
    if not path:
        print(f"clip not found: {argv[0]}")
        return 2
    data, body = load_clip(path)
    out = dict(data)
    out["path"] = str(path.relative_to(root))
    out["content"] = body
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_update(root: Path, argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: clip_manager.py <project-dir> update <title_or_slug> <field> [value]")
        return 1
    path = find_clip(root, argv[0])
    if not path:
        print(f"clip not found: {argv[0]}")
        return 2
    field = argv[1]
    value = argv[2] if len(argv) >= 3 else ""
    data, body = load_clip(path)
    if field == "content":
        content_path = Path(value)
        body = content_path.read_text(encoding="utf-8") if value and content_path.exists() else value
    elif field == "tags":
        data[field] = [x.strip() for x in value.split(",") if x.strip()]
    elif field == "status":
        if value not in ALLOWED_STATUS:
            print(f"invalid status: {value}")
            return 2
        current = data.get("status", "active")
        if value != current and value not in ALLOWED_TRANSITIONS.get(current, set()):
            print(f"illegal status transition: {current} -> {value}")
            return 2
        data[field] = value
    else:
        if field not in FRONTMATTER_KEYS:
            print(f"unsupported field: {field}")
            return 2
        data[field] = value or None
    data["updated_at"] = now_local()
    save_clip(path, data, body)
    print(f"updated clip: {path}")
    return 0


def cmd_status(root: Path, argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: clip_manager.py <project-dir> status <title_or_slug> <new_status>")
        return 1
    return cmd_update(root, [argv[0], "status", argv[1]])


def cmd_merge(root: Path, argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: clip_manager.py <project-dir> merge <title_or_slug> [merged_into]")
        return 1
    path = find_clip(root, argv[0])
    if not path:
        print(f"clip not found: {argv[0]}")
        return 2
    data, body = load_clip(path)
    current = data.get("status", "active")
    if "merged" != current and "merged" not in ALLOWED_TRANSITIONS.get(current, set()):
        print(f"illegal status transition: {current} -> merged")
        return 2
    data["status"] = "merged"
    data["merged_into"] = argv[1] if len(argv) >= 2 and argv[1] else data.get("merged_into")
    data["updated_at"] = now_local()
    save_clip(path, data, body)
    print(f"merged clip: {path}")
    return 0


def cmd_rename(root: Path, argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: clip_manager.py <project-dir> rename <title_or_slug> <new_title> [new_slug]")
        return 1
    path = find_clip(root, argv[0])
    if not path:
        print(f"clip not found: {argv[0]}")
        return 2
    new_title = argv[1]
    new_slug = argv[2] if len(argv) >= 3 and argv[2] else None
    data, body = load_clip(path)
    data["title"] = new_title
    data["updated_at"] = now_local()
    target_path = path
    if new_slug:
        target_slug = ensure_unique_slug(path.parent, slugify(new_slug))
        target_path = path.parent / f"{target_slug}.md"
    save_clip(target_path, data, body)
    if target_path != path and path.exists():
        path.unlink()
    print(f"renamed clip: {target_path}")
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: clip_manager.py <project-dir> <create|list|show|update|rename|status|merge> ...")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    cmd = sys.argv[2]
    argv = sys.argv[3:]
    if cmd == "create":
        return cmd_create(root, argv)
    if cmd == "list":
        return cmd_list(root, argv)
    if cmd == "show":
        return cmd_show(root, argv)
    if cmd == "update":
        return cmd_update(root, argv)
    if cmd == "rename":
        return cmd_rename(root, argv)
    if cmd == "status":
        return cmd_status(root, argv)
    if cmd == "merge":
        return cmd_merge(root, argv)
    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
