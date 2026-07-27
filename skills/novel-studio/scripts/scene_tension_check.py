#!/usr/bin/env python3
"""
scene_tension_check.py

Lightweight scene tension checker for Novel Studio.
Flags common low-tension risks:
- no visible conflict/obstacle words
- no cost/stakes words
- dialogue-heavy paragraph with little action
- static atmosphere without decision/action

Usage:
  python3 scripts/scene_tension_check.py <text-file>
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

OBSTACLE_WORDS = ["但", "可是", "却", "拦", "挡", "阻", "不能", "不让", "拒绝", "沉默", "回避", "骗", "试探", "逼问", "反问"]
COST_WORDS = ["代价", "暴露", "失去", "来不及", "危险", "伤", "死", "疼", "怕", "损失", "耗尽", "破裂", "错过"]
ACTION_WORDS = ["走", "退", "停", "推", "拉", "按", "握", "放", "收", "抬头", "低头", "看", "盯", "问", "答", "笑", "沉默", "转身", "上前"]
STATIC_ATMOSPHERE = ["气氛", "压抑", "诡异", "安静", "沉重", "微妙", "不祥", "仿佛", "似乎"]
DECISION_WORDS = ["决定", "只好", "必须", "不能再", "转身", "开口", "伸手", "退后", "上前", "改口"]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_paragraph(paragraph: str, idx: int) -> dict:
    issues = []
    obstacle_count = sum(paragraph.count(w) for w in OBSTACLE_WORDS)
    cost_count = sum(paragraph.count(w) for w in COST_WORDS)
    action_count = sum(paragraph.count(w) for w in ACTION_WORDS)
    static_count = sum(paragraph.count(w) for w in STATIC_ATMOSPHERE)
    decision_count = sum(paragraph.count(w) for w in DECISION_WORDS)
    quote_count = paragraph.count("“") + paragraph.count("\"")

    if len(paragraph) > 100 and obstacle_count == 0 and cost_count == 0:
        issues.append({"level": "suggest", "type": "low_visible_pressure", "detail": "长段落里缺少明显阻力或代价信号"})
    if quote_count >= 4 and action_count <= 3:
        issues.append({"level": "suggest", "type": "talking_heads", "detail": "对白较多但动作/博弈承接偏少，注意空转对白"})
    if static_count >= 3 and decision_count == 0:
        issues.append({"level": "suggest", "type": "static_atmosphere", "detail": "气氛词较多但缺少明确选择"})

    return {
        "paragraph": idx,
        "chars": len(paragraph),
        "obstacle_count": obstacle_count,
        "cost_count": cost_count,
        "action_count": action_count,
        "decision_count": decision_count,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: scene_tension_check.py <text-file>")
        return 1
    path = Path(sys.argv[1]).expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)
    results = [check_paragraph(p, i + 1) for i, p in enumerate(paragraphs)]
    issue_count = sum(len(r["issues"]) for r in results)
    out = {"file": str(path), "paragraphs": len(paragraphs), "issue_count": issue_count, "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
