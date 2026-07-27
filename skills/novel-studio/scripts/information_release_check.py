#!/usr/bin/env python3
"""
information_release_check.py

Lightweight information-release checker for Novel Studio.
Flags common exposition risks:
- explanation-heavy phrases
- too many causal summary markers
- dialogue explaining known facts
- premature truth-reveal smell words

Usage:
  python3 scripts/information_release_check.py <text-file>
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

EXPOSITION_MARKERS = ["也就是说", "换句话说", "简单来说", "原来", "事实上", "其实", "真正的原因", "这意味着", "因此", "所以"]
TRUTH_REVEAL = ["真相", "秘密", "答案", "原因", "本质", "规则", "体系", "机制", "全部", "彻底"]
CARRIER_WORDS = ["看", "听", "闻", "摸", "碰", "证据", "纸", "血", "痕", "报告", "消息", "档案", "反应", "沉默", "改口", "试探"]
KNOWN_FACT_DIALOGUE = ["你知道", "正如你所知", "我们都知道", "之前说过", "早就知道"]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def check_paragraph(paragraph: str, idx: int) -> dict:
    issues = []
    exposition_hits = [w for w in EXPOSITION_MARKERS if w in paragraph]
    truth_hits = [w for w in TRUTH_REVEAL if w in paragraph]
    carrier_count = sum(paragraph.count(w) for w in CARRIER_WORDS)
    known_hits = [w for w in KNOWN_FACT_DIALOGUE if w in paragraph]

    if len(exposition_hits) >= 2:
        issues.append({"level": "suggest", "type": "exposition_dense", "detail": f"解释连接词偏密：{', '.join(exposition_hits)}"})
    if len(truth_hits) >= 3 and carrier_count == 0:
        issues.append({"level": "suggest", "type": "truth_without_carrier", "detail": f"真相/机制类词偏多但缺少物证、行动或反应载体：{', '.join(truth_hits[:8])}"})
    if known_hits:
        issues.append({"level": "suggest", "type": "known_fact_dialogue", "detail": f"疑似角色互讲已知信息：{', '.join(known_hits)}"})
    if len(paragraph) > 180 and carrier_count <= 1 and len(exposition_hits) >= 1:
        issues.append({"level": "suggest", "type": "long_explanation", "detail": "长段解释缺少足够场景载体，考虑拆到行动/物证/反应中"})

    return {
        "paragraph": idx,
        "chars": len(paragraph),
        "exposition_hits": exposition_hits,
        "truth_hits": truth_hits,
        "carrier_count": carrier_count,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: information_release_check.py <text-file>")
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
