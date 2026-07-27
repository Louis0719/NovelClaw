#!/usr/bin/env python3
"""
camera_follow_check.py

Lightweight camera-follow narration checker for Novel Studio.
It does not judge literary quality; it flags common POV / camera-follow risks:
- abstract atmosphere words
- omniscient spoiler phrases
- weak sensory grounding
- judgment-before-evidence smell words

Usage:
  python3 scripts/camera_follow_check.py <text-file> [follow_target]
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ABSTRACT_WORDS = [
    "诡异", "压迫", "危险", "不祥", "恐怖", "神秘", "复杂", "微妙", "某种", "仿佛", "似乎", "显得", "令人",
]
OMNISCIENT_PATTERNS = [
    "他不知道", "她不知道", "没人知道", "谁也不知道", "多年以后", "后来才知道", "真正的原因", "事实上", "其实",
]
SENSORY_WORDS = [
    "看", "听", "闻", "摸", "碰", "冷", "热", "潮", "疼", "响", "光", "灯", "雨", "风", "气味", "声音", "脚步", "手", "眼", "抬头", "低头", "停住",
]
JUDGMENT_WORDS = ["意识到", "明白", "知道", "判断", "觉得", "确定", "发现"]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_paragraph(paragraph: str, idx: int, follow_target: str | None) -> dict:
    issues = []
    abstract_hits = [w for w in ABSTRACT_WORDS if w in paragraph]
    if len(abstract_hits) >= 3:
        issues.append({"level": "suggest", "type": "abstract_atmosphere", "detail": f"抽象气氛词偏多：{', '.join(abstract_hits[:8])}"})

    omni_hits = [w for w in OMNISCIENT_PATTERNS if w in paragraph]
    if omni_hits:
        issues.append({"level": "must", "type": "omniscient_spoiler", "detail": f"疑似上帝视角抢跑：{', '.join(omni_hits)}"})

    sensory_count = sum(paragraph.count(w) for w in SENSORY_WORDS)
    judgment_count = sum(paragraph.count(w) for w in JUDGMENT_WORDS)
    if judgment_count and sensory_count == 0:
        issues.append({"level": "suggest", "type": "judgment_without_sensory_anchor", "detail": "有判断/认知词，但缺少明显感知锚点"})

    if follow_target and follow_target not in paragraph and idx == 1:
        issues.append({"level": "optional", "type": "target_not_visible", "detail": f"首段未显式出现跟随对象：{follow_target}"})

    return {
        "paragraph": idx,
        "chars": len(paragraph),
        "sensory_count": sensory_count,
        "judgment_count": judgment_count,
        "abstract_hits": abstract_hits,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: camera_follow_check.py <text-file> [follow_target]")
        return 1
    path = Path(sys.argv[1]).expanduser().resolve()
    follow_target = sys.argv[2] if len(sys.argv) >= 3 else None
    text = path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)
    results = [check_paragraph(p, i + 1, follow_target) for i, p in enumerate(paragraphs)]
    issue_count = sum(len(r["issues"]) for r in results)
    must_count = sum(1 for r in results for item in r["issues"] if item["level"] == "must")
    out = {
        "file": str(path),
        "follow_target": follow_target,
        "paragraphs": len(paragraphs),
        "issue_count": issue_count,
        "must_count": must_count,
        "results": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 2 if must_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
