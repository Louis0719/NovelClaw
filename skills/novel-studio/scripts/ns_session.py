#!/usr/bin/env python3
"""
ns_session.py

Novel Studio session state management with crash/interruption protection.

Each project tracks its own session state in:
  <project>/.novel-studio/session-state.json

The global config maintains a pointer to the last active project:
  <novel-studio-skill>/.novel-studio/global-config.json → lastProject

When a session is unexpectedly interrupted (status="active" on next entry),
the recovery flow presents the last work mode, last successful session,
and last failed session so the user can resume where they left off.

Usage:
  python3 scripts/ns_session.py start <project> --task <desc> [--type <type>] [--chapter <id>] [--work-mode <mode>] [--context <text>]
  python3 scripts/ns_session.py complete <project> [--summary <text>]
  python3 scripts/ns_session.py fail <project> --error <msg> [--suggestions <...>]
  python3 scripts/ns_session.py status <project> [--json]
  python3 scripts/ns_session.py clear <project>
  python3 scripts/ns_session.py global-last [--json]              # show global last-project pointer
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import sys
import uuid

# ── paths ──────────────────────────────────────────────────────────────

SESSION_FILE = "session-state.json"
GLOBAL_CONFIG_DIR = Path(__file__).resolve().parent.parent / ".novel-studio"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "global-config.json"
MAX_HISTORY = 20


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def session_path(project_dir: Path) -> Path:
    ns_dir = project_dir / ".novel-studio"
    ns_dir.mkdir(parents=True, exist_ok=True)
    return ns_dir / SESSION_FILE


def _ts_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ── session state read/write ───────────────────────────────────────────

def read_session(project_dir: Path) -> dict | None:
    sp = session_path(project_dir)
    if not sp.exists():
        return None
    try:
        return json.loads(sp.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_session(project_dir: Path, data: dict) -> None:
    sp = session_path(project_dir)
    sp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_entry(status: str, *, task: str, task_type: str = "", chapter_id: str = "",
                 work_mode: str = "", context: str = "", error: str = "",
                 suggestions: str = "", summary: str = "") -> dict:
    entry = {
        "id": _short_id(),
        "status": status,
        "startedAt": _ts_now(),
        "updatedAt": _ts_now(),
        "task": task,
        "taskType": task_type,
        "chapterId": chapter_id,
        "workMode": work_mode,
        "context": context,
    }
    if status == "failed":
        entry["error"] = error[:1000]
        entry["errorSuggestions"] = suggestions
    if status == "completed" and summary:
        entry["summary"] = summary[:500]
    return entry


# ── global last-project pointer ────────────────────────────────────────

def read_global_config() -> dict | None:
    if not GLOBAL_CONFIG_PATH.exists():
        return None
    try:
        return json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_global_config(cfg: dict) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_global_last_project(project_dir: Path) -> None:
    """Update global lastProject pointer to this project."""
    cfg = read_global_config() or {}
    cfg["lastProject"] = str(project_dir.resolve())
    # Don't lose existing fields (workMode, directApi, etc.)
    write_global_config(cfg)


# ── commands ───────────────────────────────────────────────────────────

def cmd_start(project_dir: Path, task: str, task_type: str = "",
              chapter_id: str = "", work_mode: str = "", context: str = "") -> int:
    """Mark a new session as active. Overwrites any existing currentSession."""
    existing = read_session(project_dir) or {}

    # Save old currentSession to history before overwriting
    old_current = existing.get("currentSession")
    if old_current and old_current.get("status") == "completed":
        existing["lastSuccessful"] = old_current
    elif old_current and old_current.get("status") == "failed":
        existing["lastFailed"] = old_current

    # Save old currentSession to history
    if old_current and old_current.get("id"):
        history = existing.get("sessionHistory") or []
        history.append(old_current)
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]
        existing["sessionHistory"] = history

    entry = _build_entry(
        "active",
        task=task,
        task_type=task_type,
        chapter_id=chapter_id,
        work_mode=work_mode,
        context=context,
    )
    existing["currentSession"] = entry
    existing["projectRoot"] = str(project_dir.resolve())
    existing.setdefault("lastSuccessful", None)
    existing.setdefault("lastFailed", None)

    write_session(project_dir, existing)
    _update_global_last_project(project_dir)

    print(f"✅ 会话已启动")
    print(f"   任务:    {task}")
    if task_type:
        print(f"   类型:    {task_type}")
    if chapter_id:
        print(f"   章节:    {chapter_id}")
    print(f"   工作模式: {work_mode or 'N/A'}")
    return 0


def cmd_complete(project_dir: Path, summary: str = "") -> int:
    existing = read_session(project_dir)
    if not existing or not existing.get("currentSession"):
        print("⚠️  没有活跃的会话", file=sys.stderr)
        return 1

    current = existing["currentSession"]
    current["status"] = "completed"
    current["updatedAt"] = _ts_now()
    if summary:
        current["summary"] = summary[:500]

    # Move to lastSuccessful
    existing["lastSuccessful"] = current
    existing["currentSession"] = None

    write_session(project_dir, existing)
    print("✅ 会话已完成")
    if summary:
        print(f"   摘要: {summary}")
    return 0


def cmd_fail(project_dir: Path, error: str, suggestions: str = "") -> int:
    existing = read_session(project_dir)
    if not existing or not existing.get("currentSession"):
        print("⚠️  没有活跃的会话", file=sys.stderr)
        return 1

    current = existing["currentSession"]
    current["status"] = "failed"
    current["updatedAt"] = _ts_now()
    current["error"] = error[:1000]
    current["errorSuggestions"] = suggestions

    existing["lastFailed"] = current
    existing["currentSession"] = None

    write_session(project_dir, existing)
    print(f"❌ 会话失败已记录")
    print(f"   错误: {error[:200]}")
    return 0


def _format_entry(entry: dict | None, label: str) -> list[str]:
    if not entry:
        return []
    lines = [f"  {label}:"]
    lines.append(f"    会话ID:   {entry.get('id', '-')}")
    lines.append(f"    时间:     {entry.get('startedAt', '-')[:19]}")
    lines.append(f"    工作模式: {entry.get('workMode', '-')}")
    lines.append(f"    任务:     {entry.get('task', '-')}")
    if entry.get("taskType"):
        lines.append(f"    任务类型: {entry.get('taskType')}")
    if entry.get("chapterId"):
        lines.append(f"    章节:     {entry.get('chapterId')}")
    if entry.get("status") == "failed":
        lines.append(f"    错误:     {entry.get('error', '-')[:200]}")
        if entry.get("errorSuggestions"):
            lines.append(f"    建议:     {entry.get('errorSuggestions')}")
    if entry.get("summary"):
        lines.append(f"    摘要:     {entry.get('summary')}")
    return lines


def cmd_status(project_dir: Path, as_json: bool = False) -> int:
    data = read_session(project_dir)
    if not data:
        print("ℹ️  该项目暂无会话记录", file=sys.stderr)
        return 0

    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    current = data.get("currentSession")
    last_ok = data.get("lastSuccessful")
    last_err = data.get("lastFailed")
    history = data.get("sessionHistory") or []

    if not current and not last_ok and not last_err:
        print("ℹ️  该项目暂无会话记录")
        return 0

    # Check if interrupted
    is_interrupted = current is not None and current.get("status") == "active"

    if is_interrupted:
        print("╔" + "═" * 58 + "╗")
        print("║  ⚠️  检测到未正常结束的会话（可能被中断）" + " " * 12 + "║")
        print("╚" + "═" * 58 + "╝")
        print()

    print("═══ Novel Studio 项目会话状态 ═══")
    print(f"  项目:  {data.get('projectRoot', str(project_dir))}")
    print()

    if current:
        icon = {"active": "🟡", "completed": "✅", "failed": "❌"}.get(current.get("status", ""), "❓")
        status_text = {"active": "进行中（可能已中断）", "completed": "已完成", "failed": "已失败"}.get(
            current.get("status", ""), current.get("status", "")
        )
        lines = _format_entry(current, f"{icon} 当前会话 [{status_text}]")
        for line in lines:
            print(line)
        print()

    for entry, label in [(last_ok, "✅ 上次成功"), (last_err, "❌ 上次失败")]:
        if entry and entry != current:
            lines = _format_entry(entry, label)
            for line in lines:
                print(line)
            print()

    if history:
        recent = [h for h in history if h.get("status") != "active" and h != current]
        if recent:
            print(f"  📜 最近 ({min(5, len(recent))} 条):")
            for h in recent[-5:]:
                icon = "✅" if h.get("status") == "completed" else "❌"
                print(f"    {icon} {h.get('startedAt', '-')[:19]}  {h.get('task', '-')[:60]}")

    print()
    if is_interrupted:
        print("💡 操作建议:")
        print("   1. 继续当前任务 → 无需操作，系统模型已接管")
        print("   2. 清除中断状态 → python3 scripts/ns_session.py clear <project>")
        print("   3. 查看详情     → python3 scripts/ns_session.py status <project> --json")

    return 0


def cmd_clear(project_dir: Path) -> int:
    sp = session_path(project_dir)
    if sp.exists():
        sp.unlink()
        print("✅ 会话状态已清除")
    else:
        print("ℹ️  没有需要清除的会话记录")
    return 0


def cmd_global_last(as_json: bool = False) -> int:
    cfg = read_global_config()
    if not cfg or not cfg.get("lastProject"):
        print("ℹ️  全局尚未记录最后活跃项目", file=sys.stderr)
        return 0

    lp = cfg["lastProject"]
    interrupted = cfg.get("lastProjectInterrupted", False)

    if as_json:
        print(json.dumps({
            "lastProject": lp,
            "lastProjectInterrupted": interrupted,
        }, ensure_ascii=False, indent=2))
        return 0

    print("═══ Novel Studio 全局最后项目 ═══")
    print(f"  项目路径:  {lp}")
    print(f"  是否中断:  {'⚠️ 是' if interrupted else '✅ 否'}")
    print(f"  项目存在:  {'✅ 是' if Path(lp).exists() else '❌ 否（路径可能已变更）'}")

    # Check project-level session state
    proj_path = Path(lp)
    if proj_path.exists():
        session_data = read_session(proj_path)
        if session_data:
            current = session_data.get("currentSession")
            if current and current.get("status") == "active":
                print()
                print(f"  🟡 该项目有活跃会话（可能中断）:")
                print(f"     任务: {current.get('task', '-')}")
                if current.get("chapterId"):
                    print(f"     章节: {current.get('chapterId')}")

    return 0


# ── main ───────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Novel Studio session state management")
    sub = ap.add_subparsers(dest="cmd", help="Command")

    # start
    p_start = sub.add_parser("start", help="Start a new session")
    p_start.add_argument("project", type=str, help="Project directory")
    p_start.add_argument("--task", type=str, required=True, help="Task description")
    p_start.add_argument("--type", dest="task_type", type=str, default="", help="Task type")
    p_start.add_argument("--chapter", type=str, default="", help="Chapter ID")
    p_start.add_argument("--work-mode", type=str, default="", help="Work mode (system/direct)")
    p_start.add_argument("--context", type=str, default="", help="Additional context")

    # complete
    p_complete = sub.add_parser("complete", help="Mark current session as completed")
    p_complete.add_argument("project", type=str, help="Project directory")
    p_complete.add_argument("--summary", type=str, default="", help="Completion summary")

    # fail
    p_fail = sub.add_parser("fail", help="Mark current session as failed")
    p_fail.add_argument("project", type=str, help="Project directory")
    p_fail.add_argument("--error", type=str, required=True, help="Error message")
    p_fail.add_argument("--suggestions", type=str, default="", help="Error suggestions")

    # status
    p_status = sub.add_parser("status", help="Show session status")
    p_status.add_argument("project", type=str, help="Project directory")
    p_status.add_argument("--json", action="store_true", help="JSON output")

    # clear
    p_clear = sub.add_parser("clear", help="Clear session state")
    p_clear.add_argument("project", type=str, help="Project directory")

    # global-last
    p_glast = sub.add_parser("global-last", help="Show global last-project pointer")
    p_glast.add_argument("--json", action="store_true", help="JSON output")

    args = ap.parse_args()

    if args.cmd == "start":
        project_dir = Path(args.project).resolve()
        return cmd_start(project_dir, args.task, args.task_type,
                        args.chapter, args.work_mode, args.context)

    elif args.cmd == "complete":
        project_dir = Path(args.project).resolve()
        return cmd_complete(project_dir, args.summary)

    elif args.cmd == "fail":
        project_dir = Path(args.project).resolve()
        return cmd_fail(project_dir, args.error, args.suggestions)

    elif args.cmd == "status":
        project_dir = Path(args.project).resolve()
        return cmd_status(project_dir, args.json)

    elif args.cmd == "clear":
        project_dir = Path(args.project).resolve()
        return cmd_clear(project_dir)

    elif args.cmd == "global-last":
        return cmd_global_last(args.json)

    else:
        ap.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
