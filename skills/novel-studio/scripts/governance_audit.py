#!/usr/bin/env python3
"""
governance_audit.py

Lightweight governance audit for layered Novel Studio projects.

Checks whether a project roughly follows the expected layered packet-first
structure and reports common drift:
- missing entrypoints
- missing key folders
- missing .novel-studio kernel files
- state/meta schema mismatches
- chapter status directories vs chapter-meta coverage
- nav/docs references that point to missing files

This is intentionally heuristic and non-destructive.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys


SKIP_EXACT_TOKENS = {
    "README.md",
    "docs/project-notes.md",
    "nav/",
    "settings/",
    "workflow/",
    "chapters/",
    "brainstorm/",
    "analysis/",
    ".novel-studio/",
}

SKIP_TOKEN_PARTS = [
    "...",
    "../",
    "./",
    " | ",
    "text\n",
    "fanchenlu/\n",
]


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


def strip_fenced_blocks(text: str) -> str:
    lines = text.splitlines()
    out = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def find_backticked_paths(text: str) -> list[str]:
    out: list[str] = []
    parts = strip_fenced_blocks(text).split("`")
    for i in range(1, len(parts), 2):
        token = parts[i].strip()
        if "/" in token or token.endswith(".md") or token.endswith(".json"):
            out.append(token)
    return out


def should_skip_reference(token: str) -> bool:
    if token in SKIP_EXACT_TOKENS:
        return True
    if token.startswith("http://") or token.startswith("https://"):
        return True
    if any(ch in token for ch in ["<", "{", "}", "|", "*", "…"]):
        return True
    if any(part in token for part in SKIP_TOKEN_PARTS):
        return True
    if " / " in token:
        return True
    if token.endswith("/"):
        return True
    return False


def resolve_doc_reference(base: Path, root: Path, token: str) -> Path:
    if token.startswith("/"):
        return Path(token)
    if token.startswith("./") or token.startswith("../"):
        return (base.parent / token).resolve()
    if "/" not in token:
        return base.parent / token
    return root / token


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: governance_audit.py <project-dir>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"project not found: {root}")
        return 1

    required_dirs = [
        root / "analysis",
        root / "brainstorm",
        root / "chapters",
        root / "docs",
        root / "nav",
        root / "settings",
        root / "settings" / "core",
        root / "settings" / "world",
        root / "settings" / "subsettings",
        root / "workflow",
        root / ".novel-studio",
        root / ".novel-studio" / "summaries",
        root / ".novel-studio" / "packets",
        root / ".novel-studio" / "indexes",
        root / ".novel-studio" / "logs",
    ]

    recommended_dirs = [
        root / "chapters" / "published",
        root / "chapters" / "candidates",
        root / "chapters" / "early-drafts",
        root / "chapters" / "drafts",
        root / "chapters" / "revisions",
        root / "chapters" / "clips",
        root / "chapters" / "retired",
        root / "settings" / "subsettings" / "characters",
        root / "settings" / "subsettings" / "relationships",
        root / "settings" / "subsettings" / "timeline",
        root / "settings" / "subsettings" / "foreshadowing",
        root / "settings" / "subsettings" / "spaces",
        root / "settings" / "subsettings" / "scenes",
        root / "settings" / "subsettings" / "events",
        root / "settings" / "subsettings" / "items",
    ]

    required_files = [
        root / "README.md",
        root / "docs" / "project-notes.md",
        root / ".novel-studio" / "state.json",
        root / ".novel-studio" / "chapter-meta.json",
    ]

    recommended_files = [
        root / "chapters" / "README.md",
        root / "docs" / "README.md",
        root / "nav" / "README.md",
        root / "nav" / "characters.md",
        root / "nav" / "outline.md",
        root / "nav" / "timeline.md",
        root / "nav" / "foreshadowing.md",
        root / "nav" / "state_tracking.md",
        root / "settings" / "README.md",
        root / "settings" / "subsettings" / "README.md",
        root / "settings" / "subsettings" / "project-style-card.md",
        root / "workflow" / "README.md",
        root / "workflow" / "chapter-progress.md",
        root / "workflow" / "outline-next-chapters.md",
        root / ".novel-studio" / "README.md",
        root / ".novel-studio" / "indexes" / "active-characters.md",
        root / ".novel-studio" / "indexes" / "active-events.md",
        root / ".novel-studio" / "indexes" / "active-spaces.md",
        root / ".novel-studio" / "indexes" / "active-scenes.md",
        root / ".novel-studio" / "indexes" / "active-clips.md",
        root / ".novel-studio" / "indexes" / "pending-foreshadowing.md",
    ]

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    for path in required_dirs:
        if not path.exists() or not path.is_dir():
            errors.append(f"missing required dir: {rel(path, root)}")

    for path in recommended_dirs:
        if not path.exists() or not path.is_dir():
            warnings.append(f"missing recommended dir: {rel(path, root)}")

    for path in required_files:
        if not path.exists() or not path.is_file():
            errors.append(f"missing required file: {rel(path, root)}")

    for path in recommended_files:
        if not path.exists() or not path.is_file():
            warnings.append(f"missing recommended file: {rel(path, root)}")

    state_path = root / ".novel-studio" / "state.json"
    meta_path = root / ".novel-studio" / "chapter-meta.json"
    state, state_err = load_json(state_path)
    meta, meta_err = load_json(meta_path)

    if state_err:
        errors.append(f"state.json {state_err}")
    else:
        for key in [
            "project",
            "volume",
            "last_updated",
            "status",
            "writing_mode",
            "current_phase",
            "active_conflicts",
            "key_open_threads",
        ]:
            if key not in state:
                warnings.append(f"state.json missing recommended field: {key}")

    if meta_err:
        errors.append(f"chapter-meta.json {meta_err}")
    else:
        chapters = meta.get("chapters")
        if not isinstance(chapters, list):
            errors.append("chapter-meta.json field 'chapters' must be a list")
            chapters = []
        seen_ids: set[str] = set()
        for item in chapters:
            if not isinstance(item, dict):
                warnings.append("chapter-meta.json contains non-object chapter entry")
                continue
            cid = item.get("id")
            if not cid:
                warnings.append("chapter-meta.json contains entry without id")
                continue
            if cid in seen_ids:
                warnings.append(f"duplicate chapter id in chapter-meta.json: {cid}")
            seen_ids.add(cid)
            for key in ["title", "status", "summary"]:
                if key not in item:
                    warnings.append(f"chapter-meta entry {cid} missing recommended field: {key}")
            if "clipStats" not in item:
                warnings.append(f"chapter-meta entry {cid} missing recommended field: clipStats")

        chapter_files = []
        for folder in [
            root / "chapters" / "published",
            root / "chapters" / "candidates",
            root / "chapters" / "early-drafts",
            root / "chapters" / "drafts",
            root / "chapters" / "revisions",
        ]:
            if folder.exists():
                chapter_files.extend(folder.glob("ch_*.md"))

        chapter_ids_from_files = {p.name.split("-")[0] for p in chapter_files if p.name.startswith("ch_")}
        missing_meta = sorted(chapter_ids_from_files - seen_ids)
        for cid in missing_meta:
            warnings.append(f"chapter file exists but chapter-meta has no entry: {cid}")

    for path in [root / "docs" / "project-notes.md", root / "nav" / "README.md", root / "README.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in find_backticked_paths(text):
            if should_skip_reference(token):
                continue
            candidate = resolve_doc_reference(path, root, token)
            if not candidate.exists():
                warnings.append(f"referenced path missing in {rel(path, root)}: {token}")

    if (root / "nav" / "state_tracking.md").exists() and not state_path.exists():
        warnings.append("nav/state_tracking.md exists but .novel-studio/state.json is missing")

    if (root / "settings" / "subsettings" / "project-style-card.md").exists():
        notes.append("project style card present")

    report_lines = [
        f"# Governance Audit — {root.name}",
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
        report_lines.append("- 先补齐 required dirs / files，再继续 workflow。")
    if warnings:
        report_lines.append("- 再看 warnings，决定是修结构、补 state/meta，还是更新入口文档。")
    if not errors and not warnings:
        report_lines.append("- 当前未见明显治理漂移，可继续正常使用 packet-first workflow。")

    print("\n".join(report_lines))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
