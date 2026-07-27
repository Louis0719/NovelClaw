#!/usr/bin/env python3
"""
consistency_audit.py

Check whether a layered Novel Studio project's state, chapter-meta, chapter files,
and packet-first artifacts are internally consistent.

Focus:
- chapter-meta status vs actual chapter directories
- chapter-meta hasPacket / hasSummary vs actual files
- state.summary counters vs actual chapter distributions
- state.strand_balance references vs known chapter ids
- obvious chapter-id duplication / shape issues

This complements governance_audit.py:
- governance_audit.py checks skeleton / docs / entrypoints
- consistency_audit.py checks internal state alignment
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
    "clips": "clip",
}

PRIMARY_STATUS_DIRS = {"published", "candidates", "early-drafts", "drafts"}


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def load_json(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid json: {exc}"


def chapter_id_from_name(name: str) -> str | None:
    if not name.startswith("ch_"):
        return None
    return name.split("-")[0]


def collect_chapter_files(root: Path) -> tuple[dict[str, list[Path]], dict[str, set[str]]]:
    files_by_id: dict[str, list[Path]] = {}
    ids_by_status = {status: set() for status in set(STATUS_BY_DIR.values())}
    clip_files: list[Path] = []

    for dirname, status in STATUS_BY_DIR.items():
        folder = root / "chapters" / dirname
        if not folder.exists():
            continue
        pattern = "*.md" if dirname == "clips" else "ch_*.md"
        for path in sorted(folder.glob(pattern)):
            if dirname == "clips":
                clip_files.append(path)
                ids_by_status.setdefault(status, set()).add(path.stem)
                continue
            cid = chapter_id_from_name(path.name)
            if not cid:
                continue
            files_by_id.setdefault(cid, []).append(path)
            ids_by_status.setdefault(status, set()).add(cid)

    return files_by_id, ids_by_status, clip_files


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: consistency_audit.py <project-dir>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"project not found: {root}")
        return 1

    state_path = root / ".novel-studio" / "state.json"
    meta_path = root / ".novel-studio" / "chapter-meta.json"
    state, state_err = load_json(state_path)
    meta, meta_err = load_json(meta_path)

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if state_err:
        errors.append(f"state.json {state_err}")
    if meta_err:
        errors.append(f"chapter-meta.json {meta_err}")
    if errors:
        print("# Consistency Audit\n")
        for item in errors:
            print(f"- {item}")
        return 2

    files_by_id, ids_by_status, clip_files = collect_chapter_files(root)
    chapter_ids_from_files = set(files_by_id)

    chapters = meta.get("chapters")
    if not isinstance(chapters, list):
        errors.append("chapter-meta.json field 'chapters' must be a list")
        chapters = []

    meta_by_id: dict[str, dict] = {}
    for item in chapters:
        if not isinstance(item, dict):
            warnings.append("chapter-meta contains non-object entry")
            continue
        cid = item.get("id")
        if not cid:
            warnings.append("chapter-meta contains entry without id")
            continue
        if cid in meta_by_id:
            warnings.append(f"duplicate chapter id in chapter-meta: {cid}")
        meta_by_id[cid] = item

    chapter_ids_from_meta = set(meta_by_id)

    # 1) Meta coverage vs file coverage
    for cid in sorted(chapter_ids_from_files - chapter_ids_from_meta):
        warnings.append(f"chapter file exists but chapter-meta has no entry: {cid}")
    for cid in sorted(chapter_ids_from_meta - chapter_ids_from_files):
        warnings.append(f"chapter-meta entry exists but no chapter file found: {cid}")

    # 2) Status alignment
    for cid, paths in sorted(files_by_id.items()):
        item = meta_by_id.get(cid)
        if not item:
            continue
        primary_paths = [p for p in paths if p.parent.name in PRIMARY_STATUS_DIRS]
        revision_paths = [p for p in paths if p.parent.name == "revisions"]
        expected_statuses = {STATUS_BY_DIR.get(p.parent.name) for p in primary_paths if p.parent.name in STATUS_BY_DIR}
        expected_statuses.discard(None)
        actual_status = item.get("status")
        if len(expected_statuses) == 1:
            expected_status = next(iter(expected_statuses))
            if actual_status and actual_status != expected_status:
                warnings.append(
                    f"chapter-meta status mismatch for {cid}: meta={actual_status}, files imply={expected_status}"
                )
        elif len(expected_statuses) > 1:
            warnings.append(
                f"chapter appears in multiple active status directories: {cid} -> {', '.join(sorted(rel(p, root) for p in primary_paths))}"
            )

        if revision_paths:
            notes.append(
                f"chapter has revision-layer files: {cid} -> {', '.join(sorted(rel(p, root) for p in revision_paths))}"
            )

    # 3) hasPacket / hasSummary alignment
    for cid, item in sorted(meta_by_id.items()):
        packet = root / ".novel-studio" / "packets" / f"{cid}-packet.md"
        summary = root / ".novel-studio" / "summaries" / f"{cid}-summary.md"
        has_packet_meta = item.get("hasPacket")
        has_summary_meta = item.get("hasSummary")
        if has_packet_meta is not None and has_packet_meta != packet.exists():
            warnings.append(f"hasPacket mismatch for {cid}: meta={has_packet_meta}, file_exists={packet.exists()}")
        if has_summary_meta is not None and has_summary_meta != summary.exists():
            warnings.append(f"hasSummary mismatch for {cid}: meta={has_summary_meta}, file_exists={summary.exists()}")

    # 3b) clipStats alignment
    for cid, item in sorted(meta_by_id.items()):
        clip_stats = item.get("clipStats")
        chapter_clip_files = []
        for path in clip_files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if f"chapter: {cid}" in text:
                chapter_clip_files.append(path)
        actual_clip_stats = {
            "total": len(chapter_clip_files),
            "active": len([p for p in chapter_clip_files if "status: active" in p.read_text(encoding="utf-8", errors="ignore")]),
            "merged": len([p for p in chapter_clip_files if "status: merged" in p.read_text(encoding="utf-8", errors="ignore")]),
            "archived": len([p for p in chapter_clip_files if "status: archived" in p.read_text(encoding="utf-8", errors="ignore")]),
            "discarded": len([p for p in chapter_clip_files if "status: discarded" in p.read_text(encoding="utf-8", errors="ignore")]),
        }
        if clip_stats is None:
            warnings.append(f"chapter-meta entry missing clipStats: {cid}")
        elif clip_stats != actual_clip_stats:
            warnings.append(f"clipStats mismatch for {cid}: meta={clip_stats}, actual={actual_clip_stats}")

    # 4) state.summary counters vs actual file distribution
    summary_block = state.get("summary") if isinstance(state, dict) else None
    if isinstance(summary_block, dict):
        actual_counts = {
            "chapters_published": len(ids_by_status.get("published", set())),
            "chapters_candidate": len(ids_by_status.get("candidate", set())),
            "chapters_draft": len(ids_by_status.get("draft", set())),
            "chapters_reference_only": len({
                cid
                for cid, paths in files_by_id.items()
                if any(p.parent.name == "revisions" for p in paths) and cid not in ids_by_status.get("published", set()) and cid not in ids_by_status.get("candidate", set()) and cid not in ids_by_status.get("draft", set())
            }),
            "clips_total": len(clip_files),
            "clips_active": len([p for p in clip_files if 'status: active' in p.read_text(encoding='utf-8', errors='ignore')]),
            "clips_merged": len([p for p in clip_files if 'status: merged' in p.read_text(encoding='utf-8', errors='ignore')]),
            "clips_archived": len([p for p in clip_files if 'status: archived' in p.read_text(encoding='utf-8', errors='ignore')]),
            "clips_discarded": len([p for p in clip_files if 'status: discarded' in p.read_text(encoding='utf-8', errors='ignore')]),
            "clips_unassigned": len([p for p in clip_files if 'chapter: unassigned' in p.read_text(encoding='utf-8', errors='ignore')]),
        }
        for key, actual in actual_counts.items():
            if key in summary_block and summary_block.get(key) != actual:
                warnings.append(f"state.summary mismatch for {key}: state={summary_block.get(key)}, actual={actual}")
    else:
        warnings.append("state.json missing summary block")

    # 5) strand balance references
    strand_balance = state.get("strand_balance") if isinstance(state, dict) else None
    if isinstance(strand_balance, dict):
        for key, value in strand_balance.items():
            if value and value not in chapter_ids_from_meta and value not in chapter_ids_from_files:
                warnings.append(f"state.strand_balance points to unknown chapter: {key} -> {value}")

    # 6) current phase vs visible chapter presence (light heuristic)
    current_phase = state.get("current_phase") if isinstance(state, dict) else None
    if current_phase and not chapter_ids_from_files:
        warnings.append("state.current_phase is set but no chapter files were found")

    # 7) Notes
    if chapter_ids_from_files:
        notes.append(f"chapter files detected: {len(chapter_ids_from_files)}")
    if clip_files:
        notes.append(f"clip files detected: {len(clip_files)}")
    if chapter_ids_from_meta:
        notes.append(f"chapter-meta entries detected: {len(chapter_ids_from_meta)}")

    report_lines = [
        f"# Consistency Audit — {root.name}",
        "",
        f"Project root: `{root}`",
        "",
        "## Summary",
        "",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        f"- Notes: {len(notes)}",
        "",
    ]

    def add_section(title: str, items: list[str]) -> None:
        report_lines.append(f"## {title}")
        report_lines.append("")
        if items:
            report_lines.extend([f"- {item}" for item in items])
        else:
            report_lines.append("- None")
        report_lines.append("")

    add_section("Errors", errors)
    add_section("Warnings", warnings)
    add_section("Notes", notes)

    result = "pass"
    if errors:
        result = "fail"
    elif warnings:
        result = "warn"

    report_lines += [
        "## Result",
        "",
        f"- Audit result: `{result}`",
        "",
        "## Suggested next actions",
        "",
    ]

    if errors:
        report_lines.append("- 先修复 JSON / meta 结构错误，再继续其他 workflow。")
    if warnings:
        report_lines.append("- 对照 warnings，同步修 state / chapter-meta / chapter files / packet-first 产物。")
    if not errors and not warnings:
        report_lines.append("- 当前未见明显状态互相打架，可继续正常使用 workflow。")

    print("\n".join(report_lines))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
