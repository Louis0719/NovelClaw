#!/usr/bin/env python3
"""
style_check.py

Create a style-consistency check file for a chapter and, when available,
embed a few relevant sections from the current project style card for reference.
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
    if len(sys.argv) < 3:
        print("usage: style_check.py <project-dir> <chapter-id>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]
    out = root / ".novel-studio" / "logs" / f"{chapter_id}-style-check.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    style_card = root / "settings" / "subsettings" / "project-style-card.md"
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    style_ref = str(style_card.relative_to(root)) if style_card.exists() else "（未找到项目风格卡）"

    lines = [
        f"# {chapter_id} 风格一致性检查",
        "",
        f"- 项目风格卡：`{style_ref}`",
        f"- chapter packet：`{packet.relative_to(root)}`",
        f"- style overlay：`{overlay.relative_to(root)}`",
        "",
    ]

    if style_card.exists():
        lines += ["## 项目母风格参考摘录", ""]
        lines += extract_sections(style_card.read_text(), TARGET_HEADINGS)

    lines += [
        "## 检查清单",
        "",
        "- [ ] 句子节奏仍像这本书",
        "- [ ] 对话气质没有偏离项目母风格",
        "- [ ] 感官描写方式仍符合项目习惯",
        "- [ ] 信息释放方式没有突然变味",
        "- [ ] 情绪表达没有越出项目边界",
        "- [ ] 章末钩子仍符合本书钩子习惯",
        "- [ ] 这章只是任务不同，不是风格断裂",
    ]

    out.write_text("\n".join(lines) + "\n")
    print(f"prepared style check scaffold for {chapter_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
