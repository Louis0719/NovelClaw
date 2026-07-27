#!/usr/bin/env python3
"""
humanize_pass.py

A lightweight first-pass humanize / 去AI味 helper for novel-studio.
Current version:
- reads a source chapter markdown
- writes a sidecar draft for manual review
- emits a structured rewrite brief
- preserves source text
- generates a rewritten draft with light / medium / heavy levels
"""

from pathlib import Path
import sys
from datetime import datetime, timezone
import re


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CHECKLIST = REPO_ROOT / "references" / "humanize-checklist.md"


def find_candidate_chapter(root: Path, chapter_id: str) -> Path | None:
    candidates = [
        root / "chapters" / "candidates" / f"{chapter_id}.md",
        root / "chapters" / "published" / f"{chapter_id}.md",
        root / "chapters" / f"{chapter_id}.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    for path in root.rglob(f"{chapter_id}.md"):
        if ".novel-studio" in path.parts:
            continue
        return path
    return None


def analyze_text(text: str) -> dict:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    lines = text.splitlines()
    sentence_count = sum(len(re.findall(r"[。！？!?]", line)) for line in lines)
    connector_hits = sum(text.count(token) for token in ["因此", "此外", "同时", "然而", "不过", "于是", "不仅", "而且"])
    ai_taste_hits = sum(text.count(token) for token in ["重要", "意味着", "某种程度上", "可以说", "本质上", "换句话说", "进一步", "某种意义上"])
    dialogue_hits = text.count("“") + text.count('"')
    action_hits = sum(text.count(token) for token in ["看", "抬", "握", "走", "站", "顿", "笑", "退", "推", "坐"])
    avg_para_len = round(sum(len(p) for p in paragraphs) / len(paragraphs), 1) if paragraphs else 0

    risks = []
    if connector_hits >= 6:
        risks.append("连接词偏多，容易出现解释腔")
    if ai_taste_hits >= 6:
        risks.append("抽象判断词偏多，AI 味偏重")
    if dialogue_hits == 0 and action_hits < 6:
        risks.append("动作与对话锚点偏少，段落可能发虚")
    if avg_para_len and avg_para_len > 120:
        risks.append("段落整体偏长，节奏可能过平")
    if sentence_count and len(paragraphs) and sentence_count / max(len(paragraphs), 1) > 5:
        risks.append("单段句子偏密，建议拆节奏")

    return {
        "paragraphCount": len(paragraphs),
        "sentenceCount": sentence_count,
        "connectorHits": connector_hits,
        "aiTasteHits": ai_taste_hits,
        "dialogueHits": dialogue_hits,
        "actionHits": action_hits,
        "avgParagraphLength": avg_para_len,
        "risks": risks,
    }


def infer_level(stats: dict) -> str:
    score = 0
    score += 1 if stats["connectorHits"] >= 6 else 0
    score += 1 if stats["aiTasteHits"] >= 6 else 0
    score += 1 if stats["dialogueHits"] == 0 else 0
    score += 1 if stats["actionHits"] < 6 else 0
    score += 1 if stats["avgParagraphLength"] and stats["avgParagraphLength"] > 120 else 0
    if score >= 4:
        return "heavy"
    if score >= 2:
        return "medium"
    return "light"


def build_revision_guidance(stats: dict, level: str) -> list[str]:
    guidance = [
        "优先删掉解释性连接词，能直说就直说。",
        "优先把抽象判断改成动作、停顿、感官或对话承载。",
        "不要追求句句工整，适当放短句、碎句、留白。",
        "人物说话尽量拉开差异，不要统一模型腔。",
    ]
    if level in {"medium", "heavy"}:
        guidance.append("本次去AI味强度不低，修稿时允许轻度拆句和节奏重排。")
    if level == "heavy":
        guidance.append("本次为 heavy 档，允许明显压缩解释腔和抽象判断，但仍不要改剧情事实。")
    if stats["connectorHits"] >= 6:
        guidance.append("本稿连接词偏多，修稿时优先压‘因此/同时/然而/此外’这一类。")
    if stats["aiTasteHits"] >= 6:
        guidance.append("本稿抽象评价词偏多，优先删‘重要/意味着/本质上/可以说’这类抬高句。")
    if stats["dialogueHits"] == 0:
        guidance.append("本稿对话锚点少，若章节允许，可补一两个短对话或内在反应点。")
    if stats["actionHits"] < 6:
        guidance.append("本稿动作动词偏少，建议多用‘看/抬/顿/退/握/坐/推’之类具体动作承情绪。")
    return guidance


def conservative_rewrite(text: str, level: str) -> str:
    rewritten = text

    replacements = [
        ("某种程度上", "有点"),
        ("可以说", "算是"),
        ("换句话说", "说白了"),
        ("本质上", "说到底"),
        ("进一步", "再往下"),
        ("某种意义上", "往轻里说"),
    ]
    if level in {"medium", "heavy"}:
        replacements += [
            ("这意味着", "这就让"),
            ("这很重要", "这事不小"),
            ("显得尤为重要", "一下子就变得扎眼"),
        ]
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)

    rewritten = re.sub(r"因此，?", "", rewritten)
    rewritten = re.sub(r"此外，?", "", rewritten)
    rewritten = re.sub(r"与此同时，?", "", rewritten)
    rewritten = re.sub(r"然而，?", "但", rewritten)
    rewritten = re.sub(r"不过，?", "但", rewritten)

    paragraphs = rewritten.split("\n\n")
    new_paragraphs = []
    for para in paragraphs:
        p = para.strip()
        if not p:
            new_paragraphs.append(para)
            continue
        if level in {"medium", "heavy"} and len(p) > 140 and "，" in p and "“" not in p:
            p = p.replace("，", "。", 1)
        if level == "heavy" and len(p) > 180 and "，" in p:
            p = p.replace("，", "。", 1)
        new_paragraphs.append(p)

    rewritten = "\n\n".join(new_paragraphs)
    return rewritten


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: humanize_pass.py <project-dir> <chapter-id> [light|medium|heavy]")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    source = find_candidate_chapter(root, chapter_id)
    if not source:
        print(f"[error] chapter source not found for: {chapter_id}")
        return 1

    logs_dir = root / ".novel-studio" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    output = logs_dir / f"{chapter_id}-humanize-pass.md"

    checklist_text = CHECKLIST.read_text(encoding="utf-8") if CHECKLIST.exists() else ""
    source_text = source.read_text(encoding="utf-8")
    stats = analyze_text(source_text)
    requested_level = sys.argv[3].strip().lower() if len(sys.argv) >= 4 else ""
    level = requested_level if requested_level in {"light", "medium", "heavy"} else infer_level(stats)
    guidance = build_revision_guidance(stats, level)
    rewritten = conservative_rewrite(source_text, level)

    lines = []
    lines.append(f"# {chapter_id} 去AI味（humanize）工作稿")
    lines.append("")
    lines.append("## 生成信息")
    lines.append("")
    lines.append(f"- 生成时间（UTC）：{datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- 来源章节：`{source.relative_to(root)}`")
    lines.append("- 内部能力名：`humanize`")
    lines.append("- 用户侧中文名：`去AI味`")
    lines.append(f"- 去AI味强度：`{level}`")
    lines.append("- 当前策略：保守旁路输出，不直接覆盖原章")
    lines.append("")
    lines.append("## 快速诊断")
    lines.append("")
    lines.append(f"- 段落数：{stats['paragraphCount']}")
    lines.append(f"- 句子数（粗略）：{stats['sentenceCount']}")
    lines.append(f"- 连接词命中：{stats['connectorHits']}")
    lines.append(f"- AI 味词命中：{stats['aiTasteHits']}")
    lines.append(f"- 对话锚点：{stats['dialogueHits']}")
    lines.append(f"- 动作动词命中：{stats['actionHits']}")
    lines.append(f"- 平均段长：{stats['avgParagraphLength']}")
    lines.append("")
    lines.append("## 去AI味风险提示")
    lines.append("")
    if stats["risks"]:
        for item in stats["risks"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 当前未见特别突出的 AI 味风险，可做轻量去AI味。")
    lines.append("")
    lines.append("## 修订指令（可直接给模型/编辑者）")
    lines.append("")
    for item in guidance:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 去AI味处理建议")
    lines.append("")
    lines.append("请对照以下原则，人工或后续脚本继续处理：")
    lines.append("")
    for raw in checklist_text.splitlines():
        lines.append(raw)
    lines.append("")
    lines.append("## 去AI味初稿（自动保守改写版）")
    lines.append("")
    lines.append(rewritten.rstrip())
    lines.append("")
    lines.append("## 原文存档")
    lines.append("")
    lines.append(source_text.rstrip())
    lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] humanize sidecar written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
