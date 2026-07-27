#!/usr/bin/env python3
"""
observer_description_check.py

Lightweight observer-description checker for Novel Studio.
Flags common third-party description risks:
- direct author praise / label-heavy praise
- crowd-cheer cliches
- weak concrete reaction grounding
- omniscient information leak phrases

Usage:
  python3 scripts/observer_description_check.py <text-file> [subject]
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

DIRECT_PRAISE = [
    "很强", "强大", "可怕", "恐怖", "惊人", "厉害", "不凡", "非同一般", "深不可测", "无人能敌", "压迫感", "敬畏",
]
CROWD_CLICHES = [
    "全场震惊", "众人震惊", "所有人都", "倒吸一口凉气", "恐怖如斯", "纷纷露出", "一片哗然", "鸦雀无声",
]
REACTION_ANCHORS = [
    "后退", "沉默", "停", "收", "放下", "抬头", "低头", "看", "盯", "改口", "称呼", "上报", "撤", "退", "按", "握", "松开", "没说话", "不说话", "咽", "吞", "避开",
]
OMNI_LEAKS = [
    "他不知道", "她不知道", "没人知道", "谁也不知道", "真正的原因", "事实上", "其实", "注定", "后来才知道",
]
OBSERVER_MARKERS = [
    "旁边", "门口", "后排", "掌柜", "捕快", "弟子", "众人", "有人", "那人", "对方", "老人", "孩子", "路人", "目击", "报告", "名单", "会议",
]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_paragraph(paragraph: str, idx: int, subject: str | None) -> dict:
    issues = []
    praise_hits = [w for w in DIRECT_PRAISE if w in paragraph]
    crowd_hits = [w for w in CROWD_CLICHES if w in paragraph]
    reaction_count = sum(paragraph.count(w) for w in REACTION_ANCHORS)
    omni_hits = [w for w in OMNI_LEAKS if w in paragraph]
    observer_hits = [w for w in OBSERVER_MARKERS if w in paragraph]

    if crowd_hits:
        issues.append({"level": "suggest", "type": "crowd_cliche", "detail": f"疑似群体尬吹/弹幕式反应：{', '.join(crowd_hits)}"})

    if len(praise_hits) >= 2 and reaction_count == 0:
        issues.append({"level": "suggest", "type": "direct_praise_without_reaction", "detail": f"直接评价词偏多且缺少具体反应：{', '.join(praise_hits[:8])}"})

    if omni_hits:
        issues.append({"level": "must", "type": "information_leak", "detail": f"疑似第三方信息越权/上帝视角：{', '.join(omni_hits)}"})

    if observer_hits and praise_hits and reaction_count == 0:
        issues.append({"level": "suggest", "type": "observer_labeling", "detail": "有观察者标记和评价词，但缺少行为后果或微反应"})

    if subject and subject in paragraph and len(praise_hits) >= 3:
        issues.append({"level": "optional", "type": "subject_overpraised", "detail": f"被描述对象 `{subject}` 附近评价词密度偏高，考虑改成第三方反应"})

    return {
        "paragraph": idx,
        "chars": len(paragraph),
        "praise_hits": praise_hits,
        "crowd_hits": crowd_hits,
        "reaction_count": reaction_count,
        "observer_hits": observer_hits,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: observer_description_check.py <text-file> [subject]")
        return 1
    path = Path(sys.argv[1]).expanduser().resolve()
    subject = sys.argv[2] if len(sys.argv) >= 3 else None
    text = path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)
    results = [check_paragraph(p, i + 1, subject) for i, p in enumerate(paragraphs)]
    issue_count = sum(len(r["issues"]) for r in results)
    must_count = sum(1 for r in results for item in r["issues"] if item["level"] == "must")
    out = {
        "file": str(path),
        "subject": subject,
        "paragraphs": len(paragraphs),
        "issue_count": issue_count,
        "must_count": must_count,
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2 if must_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
