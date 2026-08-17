#!/usr/bin/env python3
"""Validate every JSON file parses cleanly."""
from __future__ import annotations
import json, sys
from pathlib import Path

EXCLUDE = {"__pycache__", "node_modules", ".git", ".venv", "venv", "dist", "build"}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = []
    checked = 0
    for p in sorted(root.rglob("*.json")):
        if any(part in EXCLUDE for part in p.relative_to(root).parts):
            continue
        if not p.is_file():
            continue
        checked += 1
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append((p, str(e)))
    print(f"Checked {checked} JSON files")
    if errors:
        print(f"\n❌ {len(errors)} invalid:", file=sys.stderr)
        for p, msg in errors:
            print(f"  {p.relative_to(root)}: {msg}", file=sys.stderr)
        return 1
    print("✅ All JSON files valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
