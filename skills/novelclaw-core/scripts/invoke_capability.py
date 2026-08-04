#!/usr/bin/env python3
"""
墨枢能力调用脚本（NovelClaw Capability Invoker）

命令行接口，调用墨枢（NovelClaw）的 20 项核心能力。

用法：
    python invoke_capability.py --list
    python invoke_capability.py --capability <slug> --input <text> [--output <file>]
    python invoke_capability.py --capability <slug> --input <text> --output <file> --api-key <key>

支持的能力：
    plot_strategy, retrieve_context, enrich_character, enrich_world,
    draft_chapter, rewrite_chapter, finalize,
    idea_analyzer, analyzer, evaluator, judge,
    consistency_checker, realtime_editor, turning_point_tracker

配置：
    API key 读取顺序：
    1. 命令行 --api-key 参数
    2. 环境变量 MINIMAX_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY
    3. ~/.openclaw/credentials/ 中的配置（如果存在）

API：
    默认使用 MiniMax API（OPENAI兼容），可通过 --provider 切换。
    支持：minimax, deepseek, openai 等兼容 OpenAI ChatAPI 的 Provider。
"""

import argparse
import json
import os
import sys
import textwrap
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 配置和 Capability 注册
# ---------------------------------------------------------------------------

CAPABILITY_LIST = [
    ("plot_strategy", "情节策略", "Plot Strategy", "Claw 动作",
     "在起草正文前规划章节推进、冲突升级与关键转折点。"),
    ("retrieve_context", "上下文检索", "Context Retrieval", "Claw 动作",
     "把相关的动态记忆、事实信息和最近写作状态重新拉回当前循环。"),
    ("enrich_character", "人物强化", "Character Enrichment", "Claw 动作",
     "强化人物动机、关系网络、行为边界和角色一致性。"),
    ("enrich_world", "世界观强化", "World Enrichment", "Claw 动作",
     "明确世界规则、场景约束、设定事实和可复用的正典信息。"),
    ("draft_chapter", "章节起草", "Draft Chapter", "核心写作",
     "生成当前章节的主体正文草稿。"),
    ("rewrite_chapter", "章节重写", "Rewrite Chapter", "核心写作",
     "当质量、节奏或长度不达标时，对草稿进行重写或压缩。"),
    ("finalize", "定稿", "Finalize", "核心写作",
     "当当前候选稿达到可接受标准后完成定稿。"),
    ("idea_analyzer", "创意分析", "Idea Analyzer", "辅助技能",
     "把粗糙想法整理为包含题材、角色、目标和约束的稳定提案。"),
    ("analyzer", "任务分析", "Task Analyzer", "辅助技能",
     "判断当前步骤更需要规划、起草、修订还是收束整理。"),
    ("evaluator", "评估器", "Evaluator", "辅助技能",
     "评估候选稿的一致性、节奏、情绪力度和任务匹配度。"),
    ("judge", "裁决器", "Judge", "辅助技能",
     "当多个章节候选结果接近时，用于做最终裁决。"),
    ("consistency_checker", "一致性检查", "Consistency Checker", "辅助技能",
     "检查人物、世界观、时间线和既有事实之间的连续性。"),
    ("realtime_editor", "实时编辑", "Realtime Editor", "辅助技能",
     "定位草稿中的薄弱片段并执行针对性的修订。"),
    ("turning_point_tracker", "转折点追踪", "Turning Point Tracker", "辅助技能",
     "追踪章节是否在真正推动故事向前发展。"),
]

CAPABILITY_MAP = {slug: (name_zh, name_en, category, desc) for slug, name_zh, name_en, category, desc in CAPABILITY_LIST}


# ---------------------------------------------------------------------------
# LLM 调用
# ---------------------------------------------------------------------------

def load_api_key_from_openclaw_config() -> Optional[str]:
    """从 ~/.openclaw/credentials/ 或其他已知位置尝试加载 API key。"""
    # 已知环境变量优先级最高
    for env_key in ["MINIMAX_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"]:
        val = os.getenv(env_key, "").strip()
        if val:
            return val

    # 尝试从 openclaw credentials 读取（常见结构）
    credentials_dir = os.path.expanduser("~/.openclaw/credentials")
    if os.path.isdir(credentials_dir):
        for fname in os.listdir(credentials_dir):
            fpath = os.path.join(credentials_dir, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    # 尝试解析 JSON
                    try:
                        data = json.loads(content)
                        for key in ["api_key", "key", "token", "secret"]:
                            if key in data and str(data[key]).strip():
                                return str(data[key]).strip()
                    except json.JSONDecodeError:
                        # 非JSON，按 key=value 格式解析
                        for line in content.splitlines():
                            line = line.strip()
                            if "=" in line and not line.startswith("#"):
                                k, v = line.split("=", 1)
                                k = k.strip()
                                v = v.strip()
                                if k in ("api_key", "key", "token"):
                                    return v
                except Exception:
                    pass

    return None


def build_llm_client(
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> "LLMClient":
    """
    构建 LLM 客户端（延迟导入避免无谓依赖）。
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    if not base_url:
        # MiniMax API 默认端点
        base_url = "https://api.minimax.chat/v1"

    if not model:
        model = "MiniMax-Text-01"

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    client._model = model
    return client


def call_llm(
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """调用 LLM 并返回内容字符串。"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"ERROR: LLM API call failed: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# 能力 Prompt 构建
# ---------------------------------------------------------------------------

def build_system_prompt(slug: str, is_en: bool = False) -> str:
    """根据能力 slug 返回对应的 system prompt。"""
    if is_en:
        return "You are NovelClaw's core capability module. Follow the user's instructions precisely."
    return "你正在使用墨枢的核心能力模块。请按照用户的指令执行任务。"


def build_capability_prompt(slug: str, user_input: str, is_en: bool = False) -> str:
    """根据能力 slug 和用户输入构建 capability-specific prompt。"""

    prompts = {

        "plot_strategy": {
            "zh": f"""你是一个专业的网文情节规划专家。请为以下故事构思进行章节推进规划和冲突升级设计：

{user_input}

请提供：
1. 主要情节点列表（至少5个关键转折）
2. 每章的核心冲突设计
3. 章节间的节奏安排
4. 伏笔埋设与回收计划
请用中文详细输出。""",
            "en": f"""As a plot strategy expert, please plan the chapter progression and conflict escalation for:

{user_input}

Provide:
1. Key plot points (at least 5 major turning points)
2. Core conflict design for each chapter
3. Pacing rhythm across chapters
4. Foreshadowing and payoff plan"""
        },

        "retrieve_context": {
            "zh": f"""你是一个上下文检索专家。请根据以下输入，模拟从记忆系统中检索相关内容：

{user_input}

请以 JSON 格式输出模拟检索到的相关上下文：
{{"retrieved_context": "...", "relevant_facts": [...], "memory_bank_hits": [...]}}""",
            "en": f"""As a context retrieval expert, simulate retrieving relevant context from memory for:

{user_input}

Output simulated retrieval results in JSON format."""
        },

        "enrich_character": {
            "zh": f"""你是一个专业的人物塑造专家。请强化以下人物设定：

{user_input}

请提供：
1. 强化后的人物动机描述
2. 人物关系网络扩展
3. 行为边界和性格一致性设计
4. 人物成长弧线
5. 关键场景中的行为预测""",
            "en": f"""As a character enrichment expert, strengthen the following character design:

{user_input}

Provide enhanced motives, relationship networks, behavioral boundaries, and character consistency design."""
        },

        "enrich_world": {
            "zh": f"""你是一个世界观设计专家。请强化以下世界设定：

{user_input}

请提供：
1. 明确的世界规则体系
2. 场景约束条件
3. 可复用的正典设定
4. 世界内在逻辑一致性检查""",
            "en": f"""As a worldbuilding expert, strengthen the following world design:

{user_input}

Provide world rules, scene constraints, canonical facts, and internal logic consistency."""
        },

        "draft_chapter": {
            "zh": f"""你是一名长篇小说写作专家。请根据以下大纲撰写章节正文：

{user_input}

写作要求：
1. 严格遵循给定大纲
2. 保持与上文连续
3. 只输出小说正文，不输出提纲
4. 长度控制在 1500-3000 字
5. 注重情节推进和人物塑造""",
            "en": f"""As an expert fiction writer, draft the chapter based on:

{user_input}

Requirements: follow the outline, maintain continuity, prose only, 1500-3000 words."""
        },

        "rewrite_chapter": {
            "zh": f"""你是一个专业的文本编辑专家。请对以下章节草稿进行重写或压缩：

{user_input}

重写要求：
1. 提升质量：消除逻辑漏洞、增强情感张力
2. 调整节奏：过长则压缩，过短则延展
3. 保持风格一致
4. 只输出重写后的正文""",
            "en": f"""As a professional editor, rewrite or compress the following chapter draft:

{user_input}

Improve quality, adjust pacing, maintain style, output revised prose only."""
        },

        "finalize": {
            "zh": f"""请确认以下章节已达到可发布标准，并输出定稿标记：

{user_input}

检查项：
1. 情节完整、逻辑自洽
2. 人物行为一致
3. 无明显错别字或语病
4. 节奏合理、高潮到位
如果达标，输出"定稿确认"和最终文本。""",
            "en": f"""Confirm the following chapter is ready for publication:

{user_input}

Check: completeness, logic, character consistency, pacing, climax."""
        },

        "idea_analyzer": {
            "zh": f"""你是一个创意分析专家。请把以下粗糙想法整理为稳定的写作提案：

{user_input}

请输出：
1. 故事类型/题材
2. 主要角色设定（至少2个）
3. 核心冲突设计
4. 故事目标与约束
5. 初步的大纲方向""",
            "en": f"""As an idea analyzer, refine the following rough idea into a stable writing brief:

{user_input}

Output: genre, main characters, core conflict, goals, constraints, outline direction."""
        },

        "analyzer": {
            "zh": f"""你是一个任务分析专家。请判断以下写作任务更需要什么：

{user_input}

选项：A. 规划（planning）B. 起草（drafting）C. 修订（revising）D. 收束（finalizing）
并简述判断理由。""",
            "en": f"""As a task analyzer, determine what the following writing task needs most:

{user_input}

Options: A. planning B. drafting C. revising D. finalizing"""
        },

        "evaluator": {
            "zh": f"""你是一个专业的创意评估专家。请评估以下文本：

{user_input}

请以 JSON 格式输出评估报告：
{{
  "overall_score": 0-1,
  "coherence": 0-1,
  "novelty": 0-1,
  "logic": 0-1,
  "pacing": 0-1,
  "suggestions": ["建议1", "建议2"]
}}""",
            "en": f"""As a creative writing evaluator, assess the following text:

{user_input}

Output JSON: {{"overall_score": 0-1, "coherence": 0-1, "novelty": 0-1, "logic": 0-1, "pacing": 0-1, "suggestions": []}}"""
        },

        "judge": {
            "zh": f"""你是一个公正的文学裁判。请对以下两个章节候选进行裁决：

{user_input}

请以 JSON 格式输出裁决报告：
{{
  "candidate": {{"Relevance": 0-10, "Coherence": 0-10, "Empathy": 0-10, "Surprise": 0-10, "Creativity": 0-10, "Complexity": 0-10, "overall": 0-10}},
  "reference": {{...}},
  "winner": "candidate"|"reference"|"tie",
  "notes": ["理由1", "理由2"]
}}""",
            "en": f"""You are a fair literary judge. Score two chapter candidates:

{user_input}

Output JSON: {{"candidate": {{...}}, "reference": {{...}}, "winner": "...", "notes": [...]}}"""
        },

        "consistency_checker": {
            "zh": f"""你是一个一致性检查专家。请检查以下内容的一致性：

{user_input}

检查维度：
1. 人物行为与设定一致性
2. 世界观规则一致性
3. 时间线逻辑
4. 已建立事实的连续性

输出 JSON：
{{"issues": ["问题1", "问题2"], "consistency_score": 0-1}}""",
            "en": f"""As a consistency checker, verify continuity across characters, world, timeline, and established facts:

{user_input}

Output JSON: {{"issues": [], "consistency_score": 0-1}}"""
        },

        "realtime_editor": {
            "zh": f"""你是一个实时编辑专家。请对以下文本进行薄弱片段检测和针对性修改：

{user_input}

检测并修复：
1. 逻辑跳跃和突兀转折
2. 重复性问题
3. 节奏失衡
4. 情感断裂
5. 人物行为漂移

输出修改后的完整文本。""",
            "en": f"""As a realtime editor, detect weak spots and apply targeted revisions to:

{user_input}

Detect and fix: logic jumps, repetition, pacing issues, emotional disconnects, character drift."""
        },

        "turning_point_tracker": {
            "zh": f"""你是一个转折点追踪专家。请分析以下章节是否在真正推动故事：

{user_input}

分析维度：
1. 是否有明确的情节推进
2. 冲突是否升级
3. 人物是否有成长或变化
4. 是否有新的信息/转折引入

输出 JSON：
{{"advancing": true/false, "turning_points": [...], "notes": "..."}}""",
            "en": f"""As a turning point tracker, analyze if the following chapter meaningfully advances the story:

{user_input}

Output JSON: {{"advancing": true/false, "turning_points": [], "notes": "..."}}"""
        },
    }

    entry = prompts.get(slug)
    if not entry:
        # 通用 prompt
        if is_en:
            return f"Please process the following input using the '{slug}' capability:\n\n{user_input}"
        return f"请使用墨枢的 '{slug}' 能力处理以下输入：\n\n{user_input}"

    return entry.get("en" if is_en else "zh", entry.get("zh", "")).format(input=user_input)


# ---------------------------------------------------------------------------
# 主逻辑
# ---------------------------------------------------------------------------

def list_capabilities():
    """打印所有可用能力列表。"""
    print("\n=== 墨枢（NovelClaw）核心能力列表 ===\n")
    print(f"{'Slug':<30} {'中文名':<12} {'分类':<10} {'说明'}")
    print("-" * 100)
    for slug, name_zh, name_en, category, desc in CAPABILITY_LIST:
        print(f"{slug:<30} {name_zh:<12} {category:<10} {desc[:50]}")
    print()


def invoke_capability(
    slug: str,
    user_input: str,
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    is_en: bool = False,
) -> Dict[str, Any]:
    """调用指定能力并返回结果。"""
    if slug not in CAPABILITY_MAP and slug not in [s for s, *_ in CAPABILITY_LIST]:
        print(f"ERROR: Unknown capability slug: {slug}", file=sys.stderr)
        print(f"Run with --list to see available capabilities.", file=sys.stderr)
        sys.exit(1)

    client = build_llm_client(api_key, base_url, model)

    system_prompt = build_system_prompt(slug, is_en=is_en)
    capability_prompt = build_capability_prompt(slug, user_input, is_en=is_en)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": capability_prompt},
    ]

    result_text = call_llm(client, model or "MiniMax-Text-01", messages, temperature=0.7)

    # 尝试解析 JSON
    parsed = None
    try:
        # 尝试提取 JSON 块
        text = result_text.strip()
        json_start = text.find("{")
        if json_start >= 0:
            # 找到第一个 { 到最后一个 }
            depth = 0
            in_str = False
            esc = False
            last_brace = -1
            for i, ch in enumerate(text[json_start:], start=json_start):
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                elif ch == '"':
                    in_str = True
                elif ch == "{":
                    if depth == 0:
                        last_brace = i
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        json_text = text[json_start:i+1]
                        try:
                            parsed = json.loads(json_text)
                            break
                        except json.JSONDecodeError:
                            pass
    except Exception:
        pass

    return {
        "capability": slug,
        "raw": result_text,
        "parsed": parsed,
        "success": True,
    }


def main():
    parser = argparse.ArgumentParser(
        description="墨枢能力调用工具 - NovelClaw Core Capability Invoker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
Examples:
  %(prog)s --list
  %(prog)s --capability plot_strategy --input "都市玄幻，主角获得上古传承"
  %(prog)s --capability evaluator --input "待评估的文本内容..."
  %(prog)s --capability judge --input "候选A内容\\n---\\n候选B内容" --output result.json
        """),
    )

    parser.add_argument(
        "--list", "-l", action="store_true",
        help="列出所有可用能力"
    )
    parser.add_argument(
        "--capability", "-c", type=str,
        help="能力 slug（如 plot_strategy, evaluator, judge）"
    )
    parser.add_argument(
        "--input", "-i", type=str,
        help="输入文本或指令"
    )
    parser.add_argument(
        "--output", "-o", type=str,
        help="输出文件路径（JSON格式）"
    )
    parser.add_argument(
        "--api-key", type=str,
        help="API Key（优先于环境变量）"
    )
    parser.add_argument(
        "--base-url", type=str,
        help="API Base URL（如 https://api.minimax.chat/v1）"
    )
    parser.add_argument(
        "--model", type=str,
        help="模型名称（如 MiniMax-Text-01）"
    )
    parser.add_argument(
        "--en", action="store_true",
        help="使用英文模式"
    )

    args = parser.parse_args()

    # 列出能力
    if args.list:
        list_capabilities()
        return

    # 检查必要参数
    if not args.capability or not args.input:
        parser.print_help()
        print("\nERROR: --capability and --input are required.", file=sys.stderr)
        sys.exit(1)

    # 获取 API Key
    api_key = args.api_key or os.getenv("MINIMAX_API_KEY") or load_api_key_from_openclaw_config()
    if not api_key:
        print("ERROR: No API key found. Set MINIMAX_API_KEY env var or use --api-key.", file=sys.stderr)
        sys.exit(1)

    # 调用能力
    result = invoke_capability(
        slug=args.capability,
        user_input=args.input,
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        is_en=args.en,
    )

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    else:
        print("\n=== 墨枢能力调用结果 ===")
        print(f"能力: {result['capability']}")
        print(f"成功: {result['success']}")
        if result.get("parsed"):
            print(f"\n解析结果:\n{json.dumps(result['parsed'], ensure_ascii=False, indent=2)}")
        else:
            print(f"\n原始输出:\n{result['raw']}")


if __name__ == "__main__":
    main()
