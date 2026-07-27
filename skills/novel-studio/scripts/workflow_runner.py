#!/usr/bin/env python3
"""
workflow_runner.py

Lightweight workflow entrypoint for the current novel-studio scaffold chain.
Supports mode switches and minimal self-healing orchestration logic.
"""

from pathlib import Path
import subprocess
import sys
import json
from datetime import datetime, timezone


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_STAGE = "chapter-full / packet-first / style-aware / object-summary / input-pack v2"


def default_state_data(project_name: str) -> dict:
    return {
        "project": project_name,
        "volume": "",
        "version": "0.1.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "status": "active",
        "writing_mode": "packet-first",
        "summary": {
            "total_chapters_planned": 0,
            "chapters_published": 0,
            "chapters_candidate": 0,
            "chapters_draft": 0,
            "chapters_reference_only": 0,
        },
        "current_phase": "",
        "main_strand": {
            "quest": "",
            "fire": "",
            "constellation": "",
        },
        "active_conflicts": [],
        "key_open_threads": [],
        "strand_balance": {
            "quest_last推进": "",
            "fire_last推进": "",
            "constellation_last推进": "",
        },
    }


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def run_py(script: Path, *args: str) -> None:
    cmd = [sys.executable, str(script), *args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def note(msg: str) -> None:
    print(f"[note] {msg}")


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)
        note(f"prepared scaffold: {path}")


def ensure_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        note(f"prepared json scaffold: {path}")


def match_from_packet(packet: Path, folder: Path, section_name: str, limit: int = 5) -> list[Path]:
    if not packet.exists() or not folder.exists():
        return []
    text = packet.read_text().splitlines()
    capture = False
    wanted = []
    for line in text:
        stripped = line.strip()
        if stripped == f"### {section_name}":
            capture = True
            continue
        if capture and stripped.startswith("### "):
            break
        if capture and stripped.startswith("- "):
            item = stripped[2:].strip().lower()
            if item:
                wanted.append(item)
    matched = []
    for p in sorted(folder.glob("*.md")):
        stem = p.stem.lower()
        if stem in {"readme", "scene-index"}:
            continue
        if any(w and w in stem for w in wanted):
            matched.append(p)
            if len(matched) >= limit:
                break
    return matched


def extract_usage_hint(path: Path) -> str:
    if not path.exists():
        return ""
    lines = path.read_text().splitlines()
    capture = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## 一句话写作说明":
            capture = True
            continue
        if capture and stripped.startswith("## "):
            break
        if capture and stripped.startswith("- "):
            return stripped[2:].strip()
    return ""


def next_report_version(logs_dir: Path, chapter_id: str) -> int:
    """Find the next sequential version number for this chapter's report."""
    if not logs_dir.exists():
        return 1
    existing = sorted(logs_dir.glob(f"{chapter_id}-chapter-full-report-v*.md"))
    if not existing:
        return 1
    highest = 0
    for p in existing:
        for part in p.stem.split("-"):
            if part.startswith("v") and part[1:].isdigit():
                num = int(part[1:])
                if num > highest:
                    highest = num
                break
    return highest + 1


def build_workflow_routing(
    summary: Path,
    packet: Path,
    style_card: Path,
    style_overlay: Path,
    object_summary: Path,
    indexes: Path,
) -> tuple[str, list[str]]:
    has_summary = summary.exists() and summary.stat().st_size >= 80
    has_packet = packet.exists() and packet.stat().st_size >= 120
    has_style_card = style_card.exists()
    has_style_overlay = style_overlay.exists()
    has_object_summary = object_summary.exists() and object_summary.stat().st_size >= 80
    has_indexes = indexes.exists() and any(indexes.glob("*.md"))

    can_write = has_summary and has_packet and has_style_overlay and has_object_summary

    if can_write:
        if packet.stat().st_size < 140 and object_summary.stat().st_size < 120:
            return (
                "极简直写路线（轻量输入包）",
                [
                    "当前章已具备核心输入层（summary + packet + style overlay + object summary）",
                    "建议直接用 chapter-full-report 中的极简输入包开始写正文",
                    "如写到一半对象承接卡壳，再回头补 object state 全文",
                ],
            )
        else:
            return (
                "标准路线（稳守输入包）",
                [
                    "当前章已具备完整核心输入层",
                    "建议直接用 chapter-full-report 中的标准输入包开始写正文",
                    "全程保持 packet 对象清单在前台，承接稳定时无需升级",
                ],
            )

    missing = []
    if not has_packet:
        missing.append("packet")
    if not has_style_overlay:
        missing.append("style overlay")
    if not has_object_summary:
        missing.append("object summary")
    if not has_summary:
        missing.append("summary")
    if not has_indexes:
        missing.append("indexes")

    if "packet" in missing or "style overlay" in missing:
        return (
            "先补完核心结构层",
            [
                f"缺少：{', '.join(missing)}",
                "建议先跑：scripts/workflow_runner.py <root> <chapter> style-full <project>",
                "这会依次生成 packet → style overlay → object summary",
            ],
        )

    if "object summary" in missing:
        return (
            "先生成对象状态摘要",
            [
                "packet 和 style overlay 已就绪，建议先生成 object summary",
                "建议跑：scripts/build_object_state_summary.py <root> <chapter>",
                "object summary 就绪后即可进入标准路线",
            ],
        )

    if not has_indexes:
        return (
            "先刷新活动索引",
            [
                "核心结构层已具备，建议先跑 refresh 建立活动索引",
                "建议跑：scripts/workflow_runner.py <root> <chapter> refresh",
                "indexes 就绪后整体上下文层会更完整",
            ],
        )

    return (
        "等待补全",
        [f"还缺：{', '.join(missing)}，请先补齐后再运行 chapter-full"],
    )


def build_humanize_recommendation(
    summary: Path,
    packet: Path,
    style_overlay: Path,
    object_summary: Path,
) -> tuple[str, str, list[str]]:
    """Return (level, recommendation, reasons)."""
    reasons = []
    total_size = 0
    for p in [summary, packet, style_overlay, object_summary]:
        if p.exists():
            total_size += p.stat().st_size

    if summary.exists() and summary.stat().st_size < 120:
        reasons.append("summary 偏薄，正文容易补写成解释腔")
    if packet.exists() and packet.stat().st_size < 180:
        reasons.append("packet 偏薄，章节约束不足时更容易出现模型套话")
    if object_summary.exists() and object_summary.stat().st_size < 120:
        reasons.append("对象状态层偏薄，人物动作与语气容易被写平")
    if style_overlay.exists() and style_overlay.stat().st_size < 120:
        reasons.append("style overlay 偏薄，文气约束不够，容易出现统一模型腔")

    if not reasons and total_size > 0:
        return (
            "light",
            "可选去AI味",
            ["当前结构层较完整，若正文初稿出现解释腔、句式过工或人物统一腔，再做一轮轻量去AI味即可"],
        )

    if len(reasons) >= 3:
        return (
            "medium",
            "建议写完后先去AI味，再考虑发布/定稿",
            reasons,
        )

    return (
        "light",
        "建议做一轮轻量去AI味",
        reasons or ["当前章节建议在正式定稿前做一轮轻修，压掉明显 AI 味"],
    )


def write_structured_summary(
    report_path: Path,
    chapter_id: str,
    version_tag: str,
    can_write: bool,
    route_label: str,
    route_steps: list[str],
    recommendation: str,
    recommendation_reason: str,
    humanize_level: str,
    humanize_recommendation: str,
    humanize_reasons: list[str],
    risks: list[str],
    input_pack_default: Path,
    usage_hint: str,
    ready_items: list[tuple[str, bool, Path]],
    missing: list[str],
) -> Path:
    """Write a machine-readable JSON summary alongside the markdown report."""
    summary_path = report_path.with_suffix(".json")
    data = {
        "chapter": chapter_id,
        "reportVersion": version_tag,
        "reportStage": REPORT_STAGE,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "canWrite": can_write,
        "workflowRoute": route_label,
        "workflowRouteSteps": route_steps,
        "inputPackRecommendation": recommendation,
        "inputPackReason": recommendation_reason,
        "humanize": {
            "internalName": "humanize",
            "displayName": "去AI味",
            "recommended": humanize_recommendation,
            "level": humanize_level,
            "reasons": humanize_reasons,
            "sidecarOutputPattern": ".novel-studio/logs/<chapter>-humanize-pass.md"
        },
        "inputPackDefault": str(input_pack_default.name),
        "inputPackUsageHint": usage_hint,
        "risks": risks,
        "chapterOverview": f".novel-studio/logs/{chapter_id}-chapter-overview.md",
        "readyItems": [
            {"label": label, "ready": ok, "path": str(path.relative_to(path.parents[1])) if path.exists() else str(path)}
            for label, ok, path in ready_items
        ],
        "missingItems": missing,
    }
    summary_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    note(f"structured summary written: {summary_path}")
    return summary_path


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: workflow_runner.py <project-dir> <chapter-id> <mode> [project-name-or-level]")
        print("modes: startup | style | style-full | chapter-full | humanize | writeback | refresh | deps | deps-all | doctor | overview | clip-overview | clip-stats-sync | full")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    mode = sys.argv[3]
    project_name = sys.argv[4] if len(sys.argv) >= 5 else root.name
    humanize_level_arg = sys.argv[4] if len(sys.argv) >= 5 else "medium"

    style_card = root / "settings" / "subsettings" / "project-style-card.md"
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    style_overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    object_summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-objects.md"
    indexes = root / ".novel-studio" / "indexes"
    summaries = root / ".novel-studio" / "summaries"
    summary = summaries / f"{chapter_id}-summary.md"
    state_json = root / ".novel-studio" / "state.json"
    meta_json = root / ".novel-studio" / "chapter-meta.json"
    logs_dir = root / ".novel-studio" / "logs"
    input_pack_default = logs_dir / f"{chapter_id}-input-pack.md"

    if mode == "startup":
        run_py(SCRIPT_DIR / "chapter_startup.py", str(root), chapter_id)
    elif mode == "style":
        if not style_card.exists():
            note("project style card not found; consider running extract_project_style.py first")
        run_py(SCRIPT_DIR / "style_check.py", str(root), chapter_id)
    elif mode == "style-full":
        if not style_card.exists():
            note("project style card not found; extracting project style scaffold now")
            run_py(SCRIPT_DIR / "extract_project_style.py", str(root), project_name)
        if not packet.exists():
            note("chapter packet not found; startup will prepare one")
            run_py(SCRIPT_DIR / "chapter_startup.py", str(root), chapter_id)
        if style_card.exists() and not style_overlay.exists():
            run_py(SCRIPT_DIR / "build_style_packet.py", str(root), chapter_id, str(style_card.relative_to(root)))
        run_py(SCRIPT_DIR / "style_check.py", str(root), chapter_id)
    elif mode == "chapter-full":
        if not summary.exists():
            ensure_file(
                summary,
                f"# {chapter_id} 摘要\n\n## 一、本章发生了什么\n- \n\n## 二、人物停在哪\n- \n\n## 三、事件推进到哪\n- \n\n## 四、空间 / 场景状态变化\n- \n\n## 五、时间锚点\n- \n\n## 六、下一章承接点\n- \n",
            )
        if not packet.exists():
            run_py(SCRIPT_DIR / "chapter_startup.py", str(root), chapter_id)
        if not style_card.exists():
            note("project style card not found; extracting project style scaffold now")
            run_py(SCRIPT_DIR / "extract_project_style.py", str(root), project_name)
        if style_card.exists() and not style_overlay.exists():
            run_py(SCRIPT_DIR / "build_style_packet.py", str(root), chapter_id, str(style_card.relative_to(root)))
        if not object_summary.exists() and packet.exists():
            run_py(SCRIPT_DIR / "build_object_state_summary.py", str(root), chapter_id)
        if not indexes.exists():
            note("indexes directory not found; refresh will prepare it")
            run_py(SCRIPT_DIR / "index_refresh.py", str(root))
        run_py(SCRIPT_DIR / "build_input_pack.py", str(root), chapter_id)
        run_py(SCRIPT_DIR / "chapter_overview.py", str(root), chapter_id)
        run_py(SCRIPT_DIR / "clip_stats_sync.py", str(root))

        version_num = next_report_version(logs_dir, chapter_id)
        version_tag = f"v{version_num}"
        startup_report = logs_dir / f"{chapter_id}-chapter-full-report-{version_tag}.md"

        ready_items = [
            ("summary", summary.exists(), summary),
            ("chapter packet", packet.exists(), packet),
            ("project style card", style_card.exists(), style_card),
            ("style overlay", style_overlay.exists(), style_overlay),
            ("object state summary", object_summary.exists(), object_summary),
            ("indexes", indexes.exists(), indexes),
        ]
        lines = [f"# {chapter_id} 可写状态报告", ""]
        lines += [
            "## 生成信息",
            "",
            f"- 生成时间（UTC）：{datetime.now(timezone.utc).isoformat()}",
            f"- 报告版本：{version_tag}",
            f"- 报告阶段：{REPORT_STAGE}",
            f"- packet 状态：{'present' if packet.exists() else 'missing'}",
            f"- style overlay 状态：{'present' if style_overlay.exists() else 'missing'}",
            f"- object summary 状态：{'present' if object_summary.exists() else 'missing'}",
            "",
        ]
        missing = []
        for label, ok, path in ready_items:
            rel = path.relative_to(root) if path.exists() or path.parent.exists() else path
            mark = "x" if ok else " "
            lines.append(f"- [{mark}] {label}：`{rel}`")
            if not ok:
                missing.append(label)
        can_write = all(ok for label, ok, _ in ready_items if label != "indexes")
        lines += ["", "## 缺失项", ""]
        if missing:
            lines.extend([f"- {item}" for item in missing])
        else:
            lines.append("- 无")

        route_label, route_steps = build_workflow_routing(
            summary, packet, style_card, style_overlay, object_summary, indexes
        )
        humanize_level, humanize_recommendation, humanize_reasons = build_humanize_recommendation(
            summary, packet, style_overlay, object_summary
        )
        lines += ["", "## 本章片段 / Clips", ""]
        overview_json = logs_dir / f"{chapter_id}-chapter-overview.json"
        clips = []
        clip_stats = None
        unassigned_preview = []
        if overview_json.exists():
            try:
                overview_data = json.loads(overview_json.read_text(encoding="utf-8"))
                clips = overview_data.get("clips", [])
                clip_stats = overview_data.get("clipStats")
                unassigned_preview = overview_data.get("unassignedClipsPreview", [])
            except Exception:
                clips = []
        if clip_stats:
            lines.append(f"- total={clip_stats.get('total', 0)}, active={clip_stats.get('active', 0)}, merged={clip_stats.get('merged', 0)}, archived={clip_stats.get('archived', 0)}, discarded={clip_stats.get('discarded', 0)}")
        if clips:
            for item in clips:
                line = f"- {item.get('title', item.get('slug', 'clip'))} (`{item.get('slug', '')}`) — status={item.get('status', '')}"
                if item.get("status") == "merged" and item.get("merged_into"):
                    line += f", merged_into={item['merged_into']}"
                lines.append(line)
                if item.get("tags"):
                    lines.append(f"  - tags: {', '.join(item['tags'])}")
                lines.append(f"  - path: `{item.get('path', '')}`")
        else:
            lines.append("- 当前本章无已归属 clips")

        lines += ["", "## 未归属片段预览", ""]
        if unassigned_preview:
            for item in unassigned_preview:
                lines.append(f"- {item.get('title', item.get('slug', 'clip'))} (`{item.get('slug', '')}`) — status={item.get('status', '')}")
                if item.get("tags"):
                    lines.append(f"  - tags: {', '.join(item['tags'])}")
                lines.append(f"  - path: `{item.get('path', '')}`")
        else:
            lines.append("- 当前无未归属片段预览")

        lines += ["", "## 本章工作流路由", ""]
        lines.append(f"**路线：`{route_label}`**")
        for step in route_steps:
            lines.append(f"- {step}")

        next_actions = []
        if not summary.exists():
            next_actions.append((1, "先补 summary 或确认上一章承接信息", f"scripts/workflow_runner.py {root} {chapter_id} chapter-full {project_name}"))
        if not packet.exists():
            next_actions.append((1, "先跑 startup 生成 packet", f"scripts/workflow_runner.py {root} {chapter_id} startup"))
        if not object_summary.exists():
            next_actions.append((1, "先生成对象状态摘要", f"scripts/build_object_state_summary.py {root} {chapter_id}"))
        if not style_card.exists():
            next_actions.append((2, "先跑 style-full 或抽取项目母风格", f"scripts/workflow_runner.py {root} {chapter_id} style-full {project_name}"))
        if style_card.exists() and not style_overlay.exists():
            next_actions.append((2, "先生成章节 style overlay", f"scripts/workflow_runner.py {root} {chapter_id} style-full {project_name}"))
        if not indexes.exists():
            next_actions.append((3, "先跑 refresh 准备 active indexes", f"scripts/workflow_runner.py {root} {chapter_id} refresh"))
        if not next_actions:
            next_actions.append((0, "现在可以正式开始写正文", "直接进入正文写作"))

        next_actions.sort(key=lambda x: x[0])
        lines += ["", "## 建议优先顺序", ""]
        for idx, (_, label, cmd) in enumerate(next_actions, start=1):
            lines.append(f"{idx}. {label}")
            lines.append(f"   - 推荐命令：`{cmd}`")

        risks = []
        if summary.exists() and summary.stat().st_size < 80:
            risks.append("summary 已存在但内容很薄，承接上下文风险偏高")
        if packet.exists() and packet.stat().st_size < 120:
            risks.append("chapter packet 已存在但内容很薄，结构约束风险偏高")
        if object_summary.exists() and object_summary.stat().st_size < 80:
            risks.append("对象状态摘要已存在但内容很薄，压缩后的对象上下文仍偏弱")
        if style_card.exists() and not style_overlay.exists():
            risks.append("项目母风格已存在但本章 style overlay 缺失，章节风格跑偏风险偏高")
        if indexes.exists():
            md_files = list(indexes.glob("*.md"))
            if not md_files:
                risks.append("indexes 目录已存在但尚未形成活动索引，低 token 上下文仍偏弱")
        if not risks and can_write:
            risks.append("当前未见明显结构性风险，可进入正文写作")

        lines += ["", "## 风险提示", ""]
        lines.extend([f"- {item}" for item in risks])

        recommendation = "模型输入包（标准）"
        recommendation_reason = "当前默认建议带对象状态层，平衡 token 与承接稳定性。"
        if packet.exists() and packet.stat().st_size < 140 and object_summary.exists() and object_summary.stat().st_size < 120:
            recommendation = "模型输入包（极简）"
            recommendation_reason = "本章结构较轻，对象状态也较短，适合走更轻的输入包。"
        if object_summary.exists() and object_summary.stat().st_size >= 120:
            recommendation = "模型输入包（标准）"
            recommendation_reason = "对象状态层信息较多，建议保留标准输入包以稳住承接。"

        lines += ["", "## 输入包档位建议", ""]
        lines.append(f"- 当前推荐：{recommendation}")
        lines.append(f"- 原因：{recommendation_reason}")
        lines.append(f"- 默认输入包：`{input_pack_default.relative_to(root)}`")
        usage_hint = extract_usage_hint(input_pack_default)
        if usage_hint:
            lines.append(f"- 默认输入包使用说明：{usage_hint}")

        lines += ["", "## 去AI味建议（humanize）", ""]
        lines.append(f"- 当前建议：{humanize_recommendation}")
        lines.append(f"- 推荐强度：`{humanize_level}`")
        lines.append("- 用户侧说法：`去AI味`")
        lines.append("- 内部能力名：`humanize`")
        lines.append(f"- 推荐命令：`scripts/workflow_runner.py {root} {chapter_id} humanize`")
        lines.append("- 输出位置：`.novel-studio/logs/<chapter>-humanize-pass.md`")
        lines.append("- 当前策略：先生成旁路稿，不直接覆盖原章")
        lines.append("")
        for reason in humanize_reasons:
            lines.append(f"- {reason}")

        lines += ["", "## 建议输入包", "", "### 必带（核心输入层）", ""]
        lines += [f"- `{summary.relative_to(root)}`", f"- `{packet.relative_to(root)}`", f"- `{style_overlay.relative_to(root)}`", f"- `{object_summary.relative_to(root)}`"]
        lines += ["", "### 推荐带（增强上下文层）", ""]
        if indexes.exists():
            added = False
            for name in ["active-characters.md", "active-events.md", "active-spaces.md", "active-scenes.md", "active-clips.md", "pending-foreshadowing.md"]:
                idx = indexes / name
                if idx.exists():
                    lines.append(f"- `{idx.relative_to(root)}`")
                    added = True
            if not added:
                lines.append("- 暂无活动索引文件")
        else:
            lines.append("- 暂无 indexes，可先 refresh")

        char_dir = root / "settings" / "subsettings" / "characters"
        event_dir = root / "settings" / "subsettings" / "events"
        space_dir = root / "settings" / "subsettings" / "spaces" / "cards"
        scene_dir = root / "settings" / "subsettings" / "scenes" / "cards"
        lines += ["", "### 按需带（对象全文层）", ""]
        any_optional = False
        for title, folder, section in [
            ("人物卡", char_dir, "人物"),
            ("事件卡", event_dir, "事件"),
            ("空间卡", space_dir, "空间"),
            ("场景卡", scene_dir, "场景"),
        ]:
            matched = match_from_packet(packet, folder, section)
            if matched:
                any_optional = True
                lines.append(f"#### {title}（基于 packet 对象清单匹配）")
                lines.extend([f"- `{p.relative_to(root)}`" for p in matched])
                lines.append("")
        if not any_optional:
            lines.append("- 当前未从 packet 对象清单中匹配到更相关的附加卡片")

        lines += ["", "## 结论", f"- 当前是否适合正式写正文：{'是' if can_write else '否'}", ""]
        startup_report.parent.mkdir(parents=True, exist_ok=True)
        startup_report.write_text("\n".join(lines))
        note(f"chapter readiness report written: {startup_report}")

        # Write machine-readable JSON summary alongside the markdown report
        write_structured_summary(
            startup_report,
            chapter_id,
            version_tag,
            can_write,
            route_label,
            route_steps,
            recommendation,
            recommendation_reason,
            humanize_level,
            humanize_recommendation,
            humanize_reasons,
            risks,
            input_pack_default,
            usage_hint,
            ready_items,
            missing,
        )
    elif mode == "humanize":
        run_py(SCRIPT_DIR / "humanize_pass.py", str(root), chapter_id, humanize_level_arg)
    elif mode == "writeback":
        run_py(SCRIPT_DIR / "writeback_sync.py", str(root), chapter_id)
    elif mode == "refresh":
        run_py(SCRIPT_DIR / "index_refresh.py", str(root))
    elif mode == "deps":
        run_py(SCRIPT_DIR / "build_chapter_deps.py", str(root), chapter_id)
    elif mode == "deps-all":
        run_py(SCRIPT_DIR / "build_chapter_deps.py", str(root), "all")
    elif mode == "doctor":
        run_py(SCRIPT_DIR / "governance_audit.py", str(root))
        run_py(SCRIPT_DIR / "consistency_audit.py", str(root))
        run_py(SCRIPT_DIR / "naming_lint.py", str(root))
    elif mode == "overview":
        run_py(SCRIPT_DIR / "chapter_overview.py", str(root), chapter_id)
    elif mode == "clip-overview":
        run_py(SCRIPT_DIR / "clip_overview.py", str(root), chapter_id)
    elif mode == "clip-stats-sync":
        run_py(SCRIPT_DIR / "clip_stats_sync.py", str(root))
    elif mode == "full":
        if not packet.exists():
            note("chapter packet not found; startup will prepare one")
        if not indexes.exists():
            note("indexes directory not found; refresh will prepare it")
        if not summary.exists():
            ensure_file(
                summary,
                f"# {chapter_id} 摘要\n\n## 一、本章发生了什么\n- \n\n## 二、人物停在哪\n- \n\n## 三、事件推进到哪\n- \n\n## 四、空间 / 场景状态变化\n- \n\n## 五、时间锚点\n- \n\n## 六、下一章承接点\n- \n",
            )
        ensure_json(
            state_json,
            default_state_data(root.name),
        )
        ensure_json(meta_json, {"chapters": []})

        if not style_card.exists():
            note("project style card not found; extracting project style scaffold now")
            run_py(SCRIPT_DIR / "extract_project_style.py", str(root), project_name)
        if not packet.exists():
            run_py(SCRIPT_DIR / "chapter_startup.py", str(root), chapter_id)
        if style_card.exists() and not style_overlay.exists():
            run_py(SCRIPT_DIR / "build_style_packet.py", str(root), chapter_id, str(style_card.relative_to(root)))
        if not object_summary.exists() and packet.exists():
            run_py(SCRIPT_DIR / "build_object_state_summary.py", str(root), chapter_id)
        run_py(SCRIPT_DIR / "build_input_pack.py", str(root), chapter_id)

        run_py(SCRIPT_DIR / "writeback_sync.py", str(root), chapter_id)
        run_py(SCRIPT_DIR / "style_check.py", str(root), chapter_id)
        run_py(SCRIPT_DIR / "index_refresh.py", str(root))
    else:
        print(f"unknown mode: {mode}")
        print("modes: startup | style | style-full | chapter-full | humanize | writeback | refresh | deps | deps-all | doctor | overview | clip-overview | clip-stats-sync | full")
        return 1

    print(f"workflow mode '{mode}' completed for {chapter_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
