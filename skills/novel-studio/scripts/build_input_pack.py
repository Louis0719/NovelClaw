#!/usr/bin/env python3
"""
build_input_pack.py

Build chapter-scoped input pack files in multiple forms and publish one default
input-pack.md based on a simple tier recommendation.
"""

from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: build_input_pack.py <project-dir> <chapter-id>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    chapter_id = sys.argv[2]

    summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md"
    packet = root / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    style_overlay = root / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md"
    object_summary = root / ".novel-studio" / "summaries" / f"{chapter_id}-objects.md"
    indexes = root / ".novel-studio" / "indexes"

    model_min = root / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-model-min.md"
    model_std = root / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-model-std.md"
    model_default = root / ".novel-studio" / "logs" / f"{chapter_id}-input-pack.md"
    review_out = root / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-review.md"
    model_min.parent.mkdir(parents=True, exist_ok=True)

    core_min = [summary, packet, style_overlay]
    core_std = [summary, packet, style_overlay, object_summary]
    index_names = ["active-characters.md", "active-events.md", "active-spaces.md", "active-scenes.md", "active-clips.md", "pending-foreshadowing.md"]
    existing_indexes = [indexes / n for n in index_names if (indexes / n).exists()]

    min_lines = [f"# {chapter_id} 模型输入包（极简）", "", "## 核心输入", ""]
    min_lines.extend([f"- `{p.relative_to(root)}`" for p in core_min])
    min_lines += ["", "## 使用说明", "- 适合本章承接简单、对象变化少时直接使用。", "- 如果写到对象承接卡壳，再补看对象状态摘要。", ""]
    model_min.write_text("\n".join(min_lines))

    std_lines = [f"# {chapter_id} 模型输入包（标准）", "", "## 核心输入", ""]
    std_lines.extend([f"- `{p.relative_to(root)}`" for p in core_std])
    std_lines += ["", "## 使用说明", "- 适合本章对象变化更多、承接要求更高时使用。", "- 默认优先用这版来稳住对象状态与风格。", ""]
    model_std.write_text("\n".join(std_lines))

    use_min = packet.exists() and packet.stat().st_size < 140 and object_summary.exists() and object_summary.stat().st_size < 120
    chosen = model_min if use_min else model_std
    tier = "极简" if use_min else "标准"
    default_lines = [f"# {chapter_id} 模型输入包（默认）", "", f"- 当前推荐档位：{tier}", f"- 默认映射文件：`{chosen.relative_to(root)}`", "", "## 核心输入", ""]
    default_lines.extend([f"- `{p.relative_to(root)}`" for p in (core_min if use_min else core_std)])
    default_lines += ["", "## 一句话写作说明", ""]
    if use_min:
        default_lines.append("- 本章优先依赖 summary + packet + style overlay 开写；若对象承接不足，再补 object state summary。")
    else:
        default_lines.append("- 本章建议直接使用标准包，先稳住对象状态与风格，再进入正文。")
    model_default.write_text("\n".join(default_lines) + "\n")

    review_lines = [f"# {chapter_id} 人工审阅输入包", "", "## 核心输入", ""]
    review_lines.extend([f"- `{p.relative_to(root)}`" for p in core_std])
    review_lines += ["", "## 推荐带（增强上下文）", ""]
    if existing_indexes:
        review_lines.extend([f"- `{p.relative_to(root)}`" for p in existing_indexes])
    else:
        review_lines.append("- 暂无活动索引文件")
    review_lines += ["", "## 使用说明", "- 适合人在正式开写前快速核对承接、对象与风格。", "- 比模型输入版更完整，但不追求最低 token。", ""]
    review_out.write_text("\n".join(review_lines))

    print(f"prepared input pack files: {model_min} , {model_std} , {model_default} , {review_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
