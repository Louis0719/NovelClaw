#!/usr/bin/env python3
"""Validate YAML frontmatter of every SKILL.md."""
from __future__ import annotations
import re, sys
from pathlib import Path

EXCLUDE = {"__pycache__", "node_modules", ".git", ".venv", "venv"}
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def parse_fm(text: str):
    if not text.startswith("---"):
        return None
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm = {}
    for line in lines[1:end]:
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = []
    checked = 0
    for path in sorted(root.rglob("SKILL.md")):
        rel = path.relative_to(root)
        if any(part in EXCLUDE for part in rel.parts):
            continue
        checked += 1
        fm = parse_fm(path.read_text(encoding="utf-8"))
        if fm is None:
            errors.append((path, "missing frontmatter"))
            continue
        if "name" not in fm:
            errors.append((path, "missing 'name'"))
        elif not NAME_RE.match(fm["name"]):
            errors.append((path, f"name '{fm['name']}' not kebab-case"))
        if "description" not in fm:
            errors.append((path, "missing 'description'"))
    if checked == 0:
        print("ℹ️  No SKILL.md files found")
        return 0
    print(f"Checked {checked} SKILL.md file(s)")
    if errors:
        for p, msg in errors:
            print(f"  {p.relative_to(root)}: {msg}", file=sys.stderr)
        return 1
    print("✅ All SKILL.md valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
