#!/usr/bin/env python3
"""
build_style_packet.py

Generate a chapter style overlay scaffold and pull in a few key sections from
project-level mother style when available.
"""

from pathlib import Path
import sys


TARGET_HEADINGS = [
    "## 四、叙事气质",
    "## 五、句子与段落习惯",
    "## 六、对话质感",
    "## 七、感官描写方式",
    "## 十、章末钩子习惯",
    "## 十二、一句话母风格总结",
]


def extract_sections(text: str, headings: list[str]) -> list[str]:
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line in headings:
            out.append(line)
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                out.append(lines[i])
                i += 1
            out.append("")
            continue
        i += 1
    return out


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: build_style_packet.py <project-dir> <chapter-id> <project-style-card-path>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    style_card_arg = sys.argv[3]
    style_card = root / style_card_arg
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"

    out = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {chapter_id} 风格调用说明",
        "",
        f"- 继承的项目风格卡：`{style_card_arg}`",
        f"- chapter packet：`{packet.relative_to(root)}`",
        "",
    ]

    if style_card.exists():
        lines += ["## 项目母风格参考摘录", ""]
        lines += extract_sections(style_card.read_text(), TARGET_HEADINGS)

    lines += [
        "## 本章局部风格偏移",
        "- 节奏：",
        "- 对话密度：",
        "- 氛围浓度：",
        "- 信息释放方式：",
        "- 情绪表达方式：",
        "",
        "## 本章不可偏离的母风格底线",
        "- ",
        "- ",
        "- ",
    ]

    out.write_text("\n".join(lines) + "\n")
    print(f"prepared chapter style overlay scaffold: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
