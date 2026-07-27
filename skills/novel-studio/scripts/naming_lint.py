#!/usr/bin/env python3
"""
naming_lint.py

Lightweight naming lint for layered Novel Studio projects.

Focus:
- detect status words stuffed into filenames where directories should carry status
- detect repeated/final/v2-style filename drift
- detect obvious placeholder/test/temp naming
- detect non-kebab-case object files in object-card areas

The linter is intentionally heuristic and severity-based:
- errors: strong naming smells worth fixing
- warnings: possible cleanup opportunities
- notes: historical / archive-ish names that may be acceptable
"""

from __future__ import annotations

from pathlib import Path
import re
import sys


ERROR_PATTERNS = [
    r"最终最终",
    r"final-final",
    r"再改",
    r"先放这里",
    r"(?:^|[-_])temp(?:[-_.]|$)",
    r"(?:^|[-_])tmp(?:[-_.]|$)",
    r"copy",
    r"副本",
    r"(?:^|[-_])test(?:[-_.]|$)",
    r"scene\d+",
    r"new-card",
    r"人物卡最终",
]

WARNING_PATTERNS = [
    r"final",
    r"v\d+",
    r"新版",
    r"重写",
    r"rewrite",
    r"revised",
    r"new",
    r"bak",
    r"备份",
]

NOTE_PATTERNS = [
    r"2018",
    r"2026-\d{2}-\d{2}",
    r"archive",
]

OBJECT_DIR_MARKERS = [
    "settings/subsettings/characters",
    "settings/subsettings/relationships",
    "settings/subsettings/timeline",
    "settings/subsettings/foreshadowing/cards",
    "settings/subsettings/spaces/cards",
    "settings/subsettings/spaces/changes",
    "settings/subsettings/scenes/cards",
    "settings/subsettings/scenes/changes",
    "settings/subsettings/events",
    "settings/subsettings/items/cards",
    "settings/subsettings/items/changes",
]

ALLOWED_NON_KEBAB = {
    "README.md",
    "project-style-card.md",
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?\.md$")
UPPER_ID_RE = re.compile(r"^FB-\d{2}-[a-z0-9-]+\.md$")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def matches_any(patterns: list[str], text: str) -> list[str]:
    return [p for p in patterns if re.search(p, text, re.IGNORECASE)]


def in_object_area(path: Path, root: Path) -> bool:
    rp = rel(path, root)
    return any(rp.startswith(prefix) for prefix in OBJECT_DIR_MARKERS)


def is_non_kebab_object_name(path: Path, root: Path) -> bool:
    if path.name in ALLOWED_NON_KEBAB:
        return False
    if path.name == "scene-index.md":
        return False
    rp = rel(path, root)
    if not in_object_area(path, root):
        return False
    # foreshadow card ids like FB-03-xxx are allowed
    if "/foreshadowing/cards/" in rp and UPPER_ID_RE.match(path.name):
        return False
    return not KEBAB_RE.match(path.name)


def classify_warning_as_note(path: Path, root: Path, matches: list[str]) -> bool:
    rp = rel(path, root)
    if rp.startswith(".novel-studio/logs/"):
        return True
    if "/chapters/revisions/" in f"/{rp}":
        return True
    if "/docs/archive/" in f"/{rp}":
        return True
    if any(m in {r"final", r"v\d+", r"rewrite", r"revised"} for m in matches) and "/workflow/" in f"/{rp}":
        return True
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: naming_lint.py <project-dir>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"project not found: {root}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    for path in sorted(root.rglob("*.md")):
        rp = rel(path, root)
        name = path.name
        lower = name.lower()

        if "/.git/" in rp or rp.startswith(".git/"):
            continue

        if is_non_kebab_object_name(path, root):
            warnings.append(f"non-kebab object filename: {rp}")

        error_hits = matches_any(ERROR_PATTERNS, lower)
        if error_hits:
            errors.append(f"filename has strong smell ({', '.join(error_hits)}): {rp}")
            continue

        warning_hits = matches_any(WARNING_PATTERNS, lower)
        if warning_hits:
            if classify_warning_as_note(path, root, warning_hits):
                notes.append(f"historical/status-bearing filename ({', '.join(warning_hits)}): {rp}")
            else:
                warnings.append(f"filename may encode state/version in name ({', '.join(warning_hits)}): {rp}")
            continue

        note_hits = matches_any(NOTE_PATTERNS, lower)
        if note_hits:
            notes.append(f"historical/archive-ish filename ({', '.join(note_hits)}): {rp}")

    report_lines = [
        f"# Naming Lint — {root.name}",
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
        report_lines.append("- 先修明显坏味道文件名，再考虑更细的命名统一。")
    if warnings:
        report_lines.append("- 对照 warnings，优先清理把状态 / 版本塞进文件名的情况。")
    if not errors and not warnings:
        report_lines.append("- 当前未见明显命名漂移。")

    print("\n".join(report_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
