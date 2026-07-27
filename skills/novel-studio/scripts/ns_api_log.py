#!/usr/bin/env python3
"""
ns_api_log.py

View and manage the Novel Studio direct API call log.

Log file lives under the Novel Studio skill directory (NOT the novel project):
  <novel-studio-skill>/.novel-studio/logs/api-calls.json

- Keeps last 100 records across all projects
- Recent 10 keep full detail (inputFiles, requestPreview, etc.)
- Older 90 keep metadata only

Usage:
  python3 scripts/ns_api_log.py                    # auto-detect skill dir
  python3 scripts/ns_api_log.py --skill-dir <path>  # explicit skill dir
  python3 scripts/ns_api_log.py --json              # JSON output
  python3 scripts/ns_api_log.py --full              # table with full detail
  python3 scripts/ns_api_log.py --summary           # summary stats only
  python3 scripts/ns_api_log.py --recent 5          # last N entries only
  python3 scripts/ns_api_log.py --errors            # error entries only
  python3 scripts/ns_api_log.py --project fanchenlu # filter by project name
  python3 scripts/ns_api_log.py --chapter ch_004    # filter by chapter ID
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import argparse
import json
import sys

LOG_FILE = "api-calls.json"


def default_skill_dir() -> Path:
    """Auto-detect the Novel Studio skill directory from this script's location."""
    return Path(__file__).resolve().parent.parent


def load_log(skill_dir: Path) -> list[dict]:
    log_path = skill_dir / ".novel-studio" / "logs" / LOG_FILE
    if not log_path.exists():
        print(f"Log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)
    try:
        entries = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            print("Log file is not a valid JSON array", file=sys.stderr)
            sys.exit(1)
        return entries
    except Exception as e:
        print(f"Failed to read log: {e}", file=sys.stderr)
        sys.exit(1)


def format_ts(iso: str) -> str:
    """Convert ISO timestamp to local short format."""
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        return iso[:16]


def status_icon(status: str) -> str:
    return {"ok": "✅", "error": "❌", "dry-run": "📋"}.get(status, "❓")


def format_tokens(usage: dict | None) -> str:
    if not usage:
        return "-"
    inp = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    out = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    return f"{inp}→{out}"


def format_chars(n: int | None) -> str:
    if n is None:
        return "-"
    if n < 1000:
        return str(n)
    return f"{n / 1000:.1f}k"


def short_project(path: str) -> str:
    """Extract a short project name from the full path."""
    return Path(path).name


def print_table(entries: list[dict], full_detail: bool = False) -> None:
    """Print a human-readable table."""
    if not entries:
        print("(no entries)")
        return

    headers = ["#", "时间", "项目", "章节", "状态", "模型", "耗时", "tokens", "输入", "输出"]
    if full_detail:
        headers.append("详细")

    # Calculate column widths
    widths = [len(h) for h in headers]
    rows: list[list[str]] = []
    for i, e in enumerate(entries, 1):
        row = [
            str(i),
            format_ts(e.get("timestamp", "")),
            short_project(e.get("project", "-")),
            e.get("chapterId", "-"),
            f"{status_icon(e.get('status', ''))} {e.get('status', '-')}",
            e.get("model", "-"),
            f"{e.get('elapsedSeconds', '-')}s" if e.get("elapsedSeconds") is not None else "-",
            format_tokens(e.get("usage")),
            format_chars(e.get("inputChars")),
            format_chars(e.get("outputChars")),
        ]
        if full_detail:
            detail_parts = []
            if e.get("inputFiles"):
                files = ", ".join(f["path"] for f in e["inputFiles"][:3])
                if len(e.get("inputFiles", [])) > 3:
                    files += f" +{len(e['inputFiles']) - 3}"
                detail_parts.append(f"📁 {files}")
            if e.get("requestPreview"):
                detail_parts.append(f"📄 {e['requestPreview']}")
            if e.get("error"):
                detail_parts.append(f"⚠️ {e['error'][:120]}")
            row.append(" | ".join(detail_parts) if detail_parts else "-")
        rows.append(row)

    for i, w in enumerate(widths):
        for row in rows:
            widths[i] = max(widths[i], len(row[i]))

    # Print header
    header_line = " │ ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("─" * len(header_line))

    # Print rows
    for row in rows:
        print(" │ ".join(c.ljust(w) for c, w in zip(row, widths)))

    print(f"\n共 {len(entries)} 条记录")


def print_summary(entries: list[dict]) -> None:
    """Print aggregate summary."""
    total = len(entries)
    ok_count = sum(1 for e in entries if e.get("status") == "ok")
    error_count = sum(1 for e in entries if e.get("status") == "error")
    dry_count = sum(1 for e in entries if e.get("status") == "dry-run")

    models: dict[str, int] = {}
    projects: dict[str, int] = {}
    total_input_tokens = 0
    total_output_tokens = 0
    total_elapsed = 0.0

    for e in entries:
        model = e.get("model", "unknown")
        models[model] = models.get(model, 0) + 1
        proj = short_project(e.get("project", "unknown"))
        projects[proj] = projects.get(proj, 0) + 1
        usage = e.get("usage") or {}
        total_input_tokens += usage.get("input_tokens") or usage.get("prompt_tokens") or 0
        total_output_tokens += usage.get("output_tokens") or usage.get("completion_tokens") or 0
        total_elapsed += e.get("elapsedSeconds") or 0

    print("═" * 50)
    print(f"📊 Novel Studio API 调用日志摘要")
    print("═" * 50)
    print(f"  总记录数:     {total}")
    print(f"  ✅ 成功:      {ok_count}")
    print(f"  ❌ 失败:      {error_count}")
    print(f"  📋 干运行:    {dry_count}")
    print(f"  总 tokens:    {total_input_tokens} → {total_output_tokens}")
    print(f"  总耗时:       {total_elapsed:.1f}s")
    print()
    if projects:
        print("项目分布:")
        for proj, count in sorted(projects.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"  {proj:30s} {count:3d} {bar}")
    print()
    print("模型使用:")
    for model, count in sorted(models.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 20)
        print(f"  {model:30s} {count:3d} {bar}")


def main() -> int:
    ap = argparse.ArgumentParser(description="View Novel Studio direct API call log")
    ap.add_argument("--skill-dir", type=str, default=None,
                    help="Path to Novel Studio skill directory (auto-detected if omitted)")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--full", action="store_true", help="Show full detail for all entries")
    ap.add_argument("--summary", action="store_true", help="Show summary statistics only")
    ap.add_argument("--recent", type=int, default=0, help="Show only last N entries")
    ap.add_argument("--errors", action="store_true", help="Show error entries only")
    ap.add_argument("--project", type=str, default="", help="Filter by project name (partial match)")
    ap.add_argument("--chapter", type=str, default="", help="Filter by chapter ID")
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve() if args.skill_dir else default_skill_dir()
    entries = load_log(skill_dir)

    # Filters
    if args.errors:
        entries = [e for e in entries if e.get("status") == "error"]
    if args.project:
        entries = [e for e in entries if args.project.lower() in short_project(e.get("project", "")).lower()]
    if args.chapter:
        entries = [e for e in entries if e.get("chapterId") == args.chapter]
    if args.recent > 0:
        entries = entries[-args.recent:]

    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0

    if args.summary:
        print_summary(entries)
        return 0

    print_table(entries, full_detail=args.full)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
