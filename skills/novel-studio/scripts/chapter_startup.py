#!/usr/bin/env python3
"""
chapter_startup.py

Prepare startup scaffolds for a new chapter.
"""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: chapter_startup.py <project-dir> <chapter-id>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]

    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    startup = root / ".novel-studio" / "logs" / f"{chapter_id}-startup-checklist.md"
    style_overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    style_check = root / ".novel-studio" / "logs" / f"{chapter_id}-style-check.md"

    packet.parent.mkdir(parents=True, exist_ok=True)
    startup.parent.mkdir(parents=True, exist_ok=True)

    if not packet.exists():
        packet.write_text(
            f"# {chapter_id} Chapter Packet\n\n"
            "## 一、本章目标\n- \n\n"
            "## 二、本章阻力\n- \n\n"
            "## 三、本章代价\n- \n\n"
            "## 四、本章结束状态\n- \n\n"
            "## 五、必须推进的伏笔\n- \n\n"
            "## 六、必须保持稳定的人物状态\n- \n\n"
            "## 七、本章对象清单\n"
            "### 人物\n- \n"
            "### 空间\n- \n"
            "### 场景\n- \n"
            "### 事件\n- \n"
            "### 时间线\n- \n"
            "### 伏笔\n- \n\n"
            "## 八、项目风格继承\n"
            f"- style overlay：`{style_overlay.relative_to(root)}`\n"
            "- 本章局部风格偏移：\n"
            "- 本章不可偏离的母风格底线：\n\n"
            "## 九、与上一章的最小承接摘要\n- \n\n"
            "## 十、本章禁止事项\n- \n\n"
            "## 十一、章末钩子类型\n- \n\n"
            f"## 十二、关联文件\n- style overlay：`{style_overlay.relative_to(root)}`\n- style check：`{style_check.relative_to(root)}`\n"
        )

    if not startup.exists():
        startup.write_text(
            f"# {chapter_id} 启动清单\n\n"
            "- [ ] 已有上一章 summary\n"
            "- [ ] 已预测本章依赖人物\n"
            "- [ ] 已预测本章依赖空间\n"
            "- [ ] 已预测本章依赖时间\n"
            "- [ ] 已预测本章依赖事件\n"
            "- [ ] 已预测本章依赖伏笔\n"
            "- [ ] 已明确本章目的\n"
            "- [ ] 已有本章框架\n"
            "- [ ] 已生成 chapter packet\n"
            "- [ ] 已列出本章预计改动哪些卡片\n"
        )

    print(f"prepared startup files for {chapter_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
