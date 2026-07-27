#!/usr/bin/env python3
"""
build_chapter_deps.py

Build and maintain chapter-deps.json — a graph of relationships between chapters.

Relationship types:
  foreshadow       — chapter plants a thread for later payoff
  callback         — chapter resolves or picks up a previous thread
  cause-effect     — chapter event is a direct consequence of a prior one
  character-intro  — character first appears here
  object-first     — object/element first appears here
  space-first     — space first appears here
  space-return     — space is revisited after prior use
  chapter-cont     — plain narrative continuation (no specific hook)
  chapter-hook     — chapter ends with a hook targeting a future chapter

Each edge is directional (from → to), with optional metadata:
  hook: str      — description of the narrative hook
  resolved: bool — whether this thread has been paid off

Usage:
  python build_chapter_deps.py <project-dir> <chapter-id>   # single chapter
  python build_chapter_deps.py <project-dir> all            # full project rebuild
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEPS_FILE = Path(".novel-studio") / "chapter-deps.json"
DEPS_VERSION = "1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_chapter_num_re = re.compile(r"(?:ch[_-]?)?(\d+)", re.IGNORECASE)


def load_deps(root: Path) -> dict:
    f = root / DEPS_FILE
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return {"meta": {"version": DEPS_VERSION, "lastUpdated": "", "chapterOrder": []}, "chapters": {}}


def save_deps(root: Path, data: dict) -> None:
    data["meta"]["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    (root / DEPS_FILE).parent.mkdir(parents=True, exist_ok=True)
    (root / DEPS_FILE).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def chapter_id_canonical(ch: str) -> str:
    """Normalise a chapter identifier to 'ch_N' form."""
    stem = Path(ch).stem
    m = _chapter_num_re.search(stem)
    if m:
        return f"ch_{int(m.group(1))}"
    return stem.lower().replace(" ", "").replace("-", "_")


def extract_markdown_bullets(text: str, section: str) -> list[str]:
    """Pull '- bullet' lines from a named section."""
    lines, capture = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == f"### {section}" or stripped == f"## {section}":
            capture = True
            continue
        if capture and (stripped.startswith("### ") or stripped.startswith("## ")):
            break
        if capture and stripped.startswith("- "):
            item = stripped[2:].strip()
            if item:
                lines.append(item)
    return lines


def referenced_chapters(text: str) -> list[str]:
    """Find '第X章' or 'ch_N' references in prose."""
    refs = set()
    for m in re.finditer(r"(?:第(\d+)章|ch[_-]?(\d+))", text, re.IGNORECASE):
        num = m.group(1) or m.group(2)
        refs.add(f"ch_{int(num)}")
    return sorted(refs)


def find_chapter_file(root: Path, chapter_id: str) -> Path | None:
    cid = chapter_id_canonical(chapter_id)
    for pattern in [
        f"chapters/published/{cid}.md",
        f"chapters/published/{cid}.txt",
        f"chapters/{cid}.md",
        f"text/{cid}.md",
        f"{cid}.md",
    ]:
        p = root / pattern
        if p.exists():
            return p
    return None


def is_first_appearance(
    chapter_id: str,
    root: Path,
    obj_name: str,
    dep_data: dict,
) -> bool:
    """True if obj_name does not appear in any earlier chapter's packet/summary."""
    obj_lower = obj_name.lower()
    order = dep_data.get("meta", {}).get("chapterOrder", [])
    if chapter_id in order:
        earlier = order[: order.index(chapter_id)]
    else:
        earlier = []
    for ch in earlier:
        for fname in [f"{ch}-packet.md", f"{ch}-summary.md"]:
            f = root / ".novel-studio" / "packets" / fname
            if not f.exists():
                f = root / ".novel-studio" / "summaries" / fname
            if f.exists() and obj_lower in f.read_text().lower():
                return False
    return True


def insert_edge(
    edges: list[dict],
    from_ch: str,
    to_ch: str,
    rel_type: str,
    hook: str = "",
    resolved: bool = False,
) -> None:
    """Deduplicating edge insert."""
    for e in edges:
        if e["from"] == from_ch and e["to"] == to_ch and e["type"] == rel_type:
            return
    edges.append({"from": from_ch, "to": to_ch, "type": rel_type, "hook": hook, "resolved": resolved})


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def build_chapter_deps(root: Path, chapter_id: str) -> dict:
    cid = chapter_id_canonical(chapter_id)
    dep_data = load_deps(root)

    packet = root / ".novel-studio" / "packets" / f"{cid}-packet.md"
    summary = root / ".novel-studio" / "summaries" / f"{cid}-summary.md"
    chapter_file = find_chapter_file(root, cid)

    packet_text = packet.read_text() if packet.exists() else ""
    summary_text = summary.read_text() if summary.exists() else ""
    chapter_text = chapter_file.read_text() if chapter_file else ""

    node = dep_data["chapters"].get(cid, {"chapter": cid, "edges": [], "foreshadowing": []})
    edges: list[dict] = list(node.get("edges", []))
    foreshadowing: list[dict] = list(node.get("foreshadowing", []))

    # ── 1. Foreshadow: "必须推进的伏笔" / "伏笔" from packet ─────────────
    packet_fores = (
        extract_markdown_bullets(packet_text, "必须推进的伏笔")
        or extract_markdown_bullets(packet_text, "伏笔")
    )
    for fs_text in packet_fores:
        if any(f.get("text") == fs_text for f in foreshadowing):
            continue
        foreshadowing.append({"text": fs_text, "status": "planted", "target": "", "fromChapter": cid})
        insert_edge(edges, cid, "future", "foreshadow", hook=fs_text)

    # ── 2. Callbacks: explicit chapter references ────────────────────────
    refs = referenced_chapters(summary_text + packet_text)
    for ref_ch in refs:
        if ref_ch == cid:
            continue
        insert_edge(edges, cid, ref_ch, "callback", hook="explicit reference in 承接/摘要")
        matched = False
        for fs in foreshadowing:
            if fs.get("fromChapter") == ref_ch and fs.get("status") == "planted":
                fs["status"] = "resolved"
                fs["target"] = cid
                matched = True
        if not matched:
            insert_edge(edges, cid, ref_ch, "callback", hook="chapter reference")

    # ── 3. Resolve marker ────────────────────────────────────────────────
    if "## 解决" in summary_text or "## 解决" in packet_text:
        for fs in foreshadowing:
            if fs.get("fromChapter") == cid and fs.get("status") == "planted":
                fs["status"] = "resolved"
                fs["target"] = cid

    # ── 4. Character first-appearance ───────────────────────────────────
    chars = extract_markdown_bullets(packet_text, "人物")
    for char in chars:
        if is_first_appearance(cid, root, char, dep_data):
            insert_edge(edges, cid, "future", "character-intro", hook=f"首次出场：{char}")
            if not any(f.get("text") == char for f in foreshadowing):
                foreshadowing.append({"text": char, "type": "character", "status": "open", "target": "", "fromChapter": cid})

    # ── 5. Space / object first-appearance ───────────────────────────────
    spaces = extract_markdown_bullets(packet_text, "空间")
    for space in spaces:
        if is_first_appearance(cid, root, space, dep_data):
            insert_edge(edges, cid, "future", "space-first", hook=f"空间首次出现：{space}")

    objects = (
        extract_markdown_bullets(packet_text, "场景")
        + extract_markdown_bullets(packet_text, "事件")
        + extract_markdown_bullets(packet_text, "物件")
    )
    for obj in objects:
        if is_first_appearance(cid, root, obj, dep_data):
            insert_edge(edges, cid, "future", "object-first", hook=f"物件首次出现：{obj}")

    # ── 6. Space returns ────────────────────────────────────────────────
    prev_first_spaces: dict[str, str] = {}
    for ch, ch_node in dep_data.get("chapters", {}).items():
        for edge in ch_node.get("edges", []):
            if edge.get("type") == "space-first":
                hook = edge.get("hook", "")
                if hook:
                    prev_first_spaces[hook.lower()] = ch

    for space in spaces:
        key = f"空间首次出现：{space}".lower()
        if key in prev_first_spaces and prev_first_spaces[key] != cid:
            insert_edge(edges, cid, prev_first_spaces[key], "space-return", hook=f"回归：{space}")

    # ── 7. Cause-effect ─────────────────────────────────────────────────
    events = extract_markdown_bullets(packet_text, "事件")
    if events:
        insert_edge(edges, cid, "future", "cause-effect", hook=f"本章事件：{events[0]}")

    # ── 8. Narrative continuation ───────────────────────────────────────
    conts = extract_markdown_bullets(packet_text, "与上一章的最小承接摘要")
    if conts:
        m = _chapter_num_re.search(cid)
        if m:
            n = int(m.group(1))
            if n > 1:
                insert_edge(edges, cid, f"ch_{n - 1}", "chapter-cont", hook="章节承接")

    # ── 9. Hook type ───────────────────────────────────────────────────
    hooks = extract_markdown_bullets(packet_text, "章末钩子类型")
    hook_type = hooks[0] if hooks else ""
    if hook_type:
        insert_edge(edges, cid, "future", "chapter-hook", hook=f"章末钩子：{hook_type}")

    # ── Write node ─────────────────────────────────────────────────────
    node["edges"] = edges
    node["foreshadowing"] = foreshadowing
    node["lastAnalyzed"] = datetime.now(timezone.utc).isoformat()
    node["hookType"] = hook_type
    dep_data["chapters"][cid] = node

    # Maintain chapter order
    order = dep_data["meta"].setdefault("chapterOrder", [])
    if cid not in order:
        m = _chapter_num_re.search(cid)
        if m:
            n = int(m.group(1))
            for i, existing in enumerate(order):
                em = _chapter_num_re.search(existing)
                if em and int(em.group(1)) > n:
                    order.insert(i, cid)
                    break
            else:
                order.append(cid)

    # Resolve "future" placeholder edges
    for ch, ch_node in dep_data["chapters"].items():
        pruned = []
        for e in ch_node.get("edges", []):
            if e.get("to") == "future":
                target = _resolve_future_edge(ch, dep_data)
                if target:
                    e["to"] = target
                else:
                    continue
            pruned.append(e)
        ch_node["edges"] = pruned

    save_deps(root, dep_data)
    return node


def _resolve_future_edge(from_ch: str, dep_data: dict) -> str:
    """Find concrete target for a 'future' placeholder edge."""
    for fs in dep_data["chapters"].get(from_ch, {}).get("foreshadowing", []):
        if fs.get("status") == "resolved" and fs.get("target"):
            return fs["target"]
    m = _chapter_num_re.search(from_ch)
    if m:
        n = int(m.group(1))
        next_ch = f"ch_{n + 1}"
        if next_ch in dep_data["chapters"]:
            return next_ch
    return ""


# ---------------------------------------------------------------------------
# Project-wide rebuild
# ---------------------------------------------------------------------------

def rebuild_all(root: Path) -> None:
    dep_data = load_deps(root)
    packets_dir = root / ".novel-studio" / "packets"
    order: list[str] = []
    if packets_dir.exists():
        for p in sorted(packets_dir.glob("*-packet.md")):
            cid = chapter_id_canonical(p.stem.replace("-packet", ""))
            if cid not in order:
                order.append(cid)
    dep_data["meta"]["chapterOrder"] = order
    save_deps(root, dep_data)
    for cid in order:
        build_chapter_deps(root, cid)
    print(f"rebuilt deps for {len(order)} chapters -> {root / DEPS_FILE}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 3:
        print("usage: build_chapter_deps.py <project-dir> <chapter-id|'all'>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    target = sys.argv[2]
    if target.lower() == "all":
        rebuild_all(root)
    else:
        node = build_chapter_deps(root, target)
        edge_count = len(node.get("edges", []))
        fs_count = len(node.get("foreshadowing", []))
        print(f"updated deps for {node['chapter']}: {edge_count} edges, {fs_count} foreshadowing entries")
        print(f"  -> {root / DEPS_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
