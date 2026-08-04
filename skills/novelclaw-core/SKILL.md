---
name: novelclaw-core
description: "墨枢核心写作能力：章节写作/评估打分/去AI味检测/一致性检查/情节策略/角色强化/世界观强化/记忆同步。独立 Skill，与天命系统并列。触发词：墨枢、写作、网文、去AI味、章节起草、评审、打分。"
---

# NovelClaw Core Skill — 墨枢核心能力

## 概述

**墨枢**（NovelClaw Core）是专为 AI 网文写作工具设计的 20 项核心能力接口。它为 OpenClaw Agent 提供完整的中文网文创作能力，包括情节策略、人物强化、世界观构建、上下文检索、动态记忆、质量评审等核心功能。

墨枢基于 `capability_registry.py` 中的 CapabilitySpec 定义，支持 Claw 动作（ClawActions）、辅助技能（Support Skills）、记忆系统（Memory System）、本地工具（Local Tools）四大分类。

---

## 能力指令集（20项）

| # | 中文名 | 英文名 | Slug | 说明 | Manager Action | 分类 |
|---|--------|--------|------|------|----------------|------|
| 1 | 情节策略 | Plot Strategy | `plot_strategy` | 在起草正文前规划章节推进、冲突升级与关键转折点 | `plot_strategy` | Claw 动作 |
| 2 | 上下文检索 | Context Retrieval | `retrieve_context` | 把相关的动态记忆、事实信息和最近写作状态重新拉回当前循环 | `retrieve_context` | Claw 动作 |
| 3 | 人物强化 | Character Enrichment | `enrich_character` | 强化人物动机、关系网络、行为边界和角色一致性 | `enrich_character` | Claw 动作 |
| 4 | 世界观强化 | World Enrichment | `enrich_world` | 明确世界规则、场景约束、设定事实和可复用的正典信息 | `enrich_world` | Claw 动作 |
| 5 | 检查工作区 | Inspect Workspace | `inspect_workspace` | 在执行下一步之前，检查本地运行工作区、章节文件和当前记忆资产 | `inspect_workspace` | 本地工具 |
| 6 | 章节起草 | Draft Chapter | `draft_chapter` | 生成当前章节的主体正文草稿 | `draft_chapter` | 核心写作 |
| 7 | 章节重写 | Rewrite Chapter | `rewrite_chapter` | 当质量、节奏或长度不达标时，对草稿进行重写或压缩 | `rewrite_chapter` | 核心写作 |
| 8 | 定稿 | Finalize | `finalize` | 当当前候选稿达到可接受标准后完成定稿 | `finalize` | 核心写作 |
| 9 | 同步故事板 | Sync Storyboard | `sync_storyboard` | 把当前章节 brief 和 Claw 计划写入本地工作区文件与大纲资产 | `sync_storyboard` | 本地工具 |
| 10 | 同步角色资产 | Sync Characters | `sync_characters` | 提取当前角色状态，并写入本地文件以及角色记忆 | `sync_characters` | 本地工具 |
| 11 | 同步世界设定 | Sync World | `sync_world` | 把世界规则与连续性事实提取到本地工作区文件和世界记忆 | `sync_world` | 本地工具 |
| 12 | 创意分析 | Idea Analyzer | `idea_analyzer` | 把粗糙想法整理为包含题材、角色、目标和约束的稳定提案 | — | 辅助技能 |
| 13 | 任务分析 | Task Analyzer | `analyzer` | 判断当前步骤更需要规划、起草、修订还是收束整理 | — | 辅助技能 |
| 14 | 动态记忆 | Dynamic Memory | `dynamic_memory` | 跨轮次保存可复用的故事状态、章节简报、事实信息和工作记忆 | — | 记忆系统 |
| 15 | 转折点追踪 | Turning Point Tracker | `turning_point_tracker` | 追踪章节是否在真正推动故事向前发展 | — | 辅助技能 |
| 16 | 一致性检查 | Consistency Checker | `consistency_checker` | 检查人物、世界观、时间线和既有事实之间的连续性 | — | 辅助技能 |
| 17 | 实时编辑 | Realtime Editor | `realtime_editor` | 定位草稿中的薄弱片段并执行针对性的修订 | — | 辅助技能 |
| 18 | 评估器 | Evaluator | `evaluator` | 评估候选稿的一致性、节奏、情绪力度和任务匹配度 | — | 辅助技能 |
| 19 | 裁决器 | Judge | `judge` | 当多个章节候选结果接近时，用于做最终裁决 | — | 辅助技能 |

---

## 指令分类

### Claw 动作（Claw Actions）
- `plot_strategy` — 情节策略
- `retrieve_context` — 上下文检索
- `enrich_character` — 人物强化
- `enrich_world` — 世界观强化

### 核心写作（Core Writing）
- `draft_chapter` — 章节起草（always_enabled）
- `rewrite_chapter` — 章节重写（always_enabled）
- `finalize` — 定稿（always_enabled）

### 本地工具（Local Tools）
- `inspect_workspace` — 检查工作区
- `sync_storyboard` — 同步故事板
- `sync_characters` — 同步角色资产
- `sync_world` — 同步世界设定

### 辅助技能（Support Skills）
- `idea_analyzer` — 创意分析
- `analyzer` — 任务分析
- `turning_point_tracker` — 转折点追踪
- `consistency_checker` — 一致性检查
- `realtime_editor` — 实时编辑
- `evaluator` — 评估器
- `judge` — 裁决器

### 记忆系统（Memory System）
- `dynamic_memory` — 动态记忆（always_enabled）

---

## Agent 体系

墨枢内置 8 个专业化 Agent：

| Agent | 角色 | 核心方法 | 说明 |
|-------|------|----------|------|
| **WriterAgent** | 写作Agent | `generate(prompt, context, topic, target_length)` | 生成小说正文，遵循大纲和风格约束 |
| **PlotAgent** | 情节构建Agent | `generate(prompt, context, topic, genre)` | 设计故事主线和情节分支 |
| **CharacterAgent** | 人物塑造Agent | `generate(prompt, context, topic, genre)` | 设计立体人物和关系网络 |
| **WorldAgent** | 世界观Agent | `generate(prompt, context, topic, genre)` | 设定背景、规则、历史、文化 |
| **EvaluatorAgent** | 创意评估Agent | `evaluate_multiple(round_results)` | 评估文本新颖性、连贯性、情绪力度 |
| **JudgeAgent** | 裁判Agent | `generate(prompt, context)` | 六维度打分裁决赛章候选 |
| **RetrievalAgent** | 数据检索Agent | `generate(prompt, context, topic)` | 检索并整合相关背景信息 |
| **IdeaCopilotAgent** | 创意副驾 | `generate_turn(original_idea, state, reply)` | 协作式构思，将粗糙想法打磨为稳定brief |

---

## Memory Bank 系统

墨枢使用 Claw Memory Banks 跨轮次保存状态，包含 16 个 Bank：

```
session_profile, language_profile, user_preferences, task_briefs,
story_premise, style_guide, chapter_briefs, scene_cards,
entity_state, relationship_state, world_state, continuity_facts,
tool_observations, decision_log, revision_notes, working_set
```

另有 6 个基础记忆类型索引：
`generated_text`, `outline`, `character`, `world_setting`, `plot_point`, `fact_card`

---

## 质量评审标准

评估器（EvaluatorAgent）输出 JSON 格式报告：

```json
{
  "overall_score": 0.0-1.0,
  "coherence": 0.0-1.0,
  "novelty": 0.0-1.0,
  "logic": 0.0-1.0,
  "pacing": 0.0-1.0,
  "emotional_score": 0.0-1.0,
  "suggestions": ["建议1", "建议2", ...]
}
```

**评分维度**：
- **coherence** — 连贯性：文本内部逻辑是否自洽
- **novelty** — 新颖性：创意和独特性程度
- **logic** — 逻辑性：情节推进是否合理
- **pacing** — 节奏：叙事节奏把控
- **emotional_score** — 情绪力度（也称 pacing 或 logic 的加权）

**通过阈值**：通常 `overall_score >= 0.6` 为可接受

裁决器（JudgeAgent）六维度（0-10）：
`Relevance`, `Coherence`, `Empathy`, `Surprise`, `Creativity`, `Complexity`

---

## 去AI味检测（实时编辑）

RealtimeEditor 执行以下检测与修复：

1. **一致性冲突** — 检测人物行为是否与设定矛盾
2. **逻辑跳跃** — 情节推进是否突兀
3. **转折突兀** — 转折点是否缺乏铺垫
4. **人物行为漂移** — 角色性格是否一致
5. **世界观违规** — 内容是否违反设定规则
6. **节奏失衡** — 拖沓或过快
7. **情感断裂** — 情绪转换是否自然
8. **重复性问题** — 重复表达或情节
9. **信息矛盾** — 前后信息不一致
10. **高潮缺失** — 章节是否缺乏情感高潮
11. **对话僵硬** — 对白是否符合角色性格
12. **描写空洞** — 场景描写是否具体生动
13. **伏笔丢失** — 前文伏笔是否回收
14. **视角混乱** — 叙述视角是否统一
15. **时间线矛盾** — 时间顺序是否清晰
16. **背景断裂** — 场景切换是否流畅
17. **动机薄弱** — 人物行动动机是否充分
18. **冲突平淡** — 冲突是否足够激烈
19. **主题模糊** — 章节主题是否明确
20. **结局仓促** — 结尾是否处理得当

---

## 使用方式

### 方式一：CLI 调用（通过 invoke_capability.py）

```bash
# 查看所有可用能力
python scripts/invoke_capability.py --list

# 调用情节策略能力
python scripts/invoke_capability.py \
  --capability plot_strategy \
  --input "都市玄幻，主角获得上古传承，都市修炼" \
  --output result.json

# 调用评估器
python scripts/invoke_capability.py \
  --capability evaluator \
  --input "文本内容..." \
  --output eval_result.json

# 调用裁决器（两个候选）
python scripts/invoke_capability.py \
  --capability judge \
  --input "候选A...\n---\n候选B..." \
  --output judge_result.json
```

### 方式二：作为 OpenClaw Skill 集成

在 Agent 对话中直接引用：
```
请使用墨枢的 plot_strategy 能力，为以下故事构思章节推进计划：
[用户输入的故事大纲]
```

### 方式三：编程调用

```python
from novelclaw_core import NovelClawCore

core = NovelClawCore(config={"api_key": "your-key", "provider": "deepseek"})

# 情节策略
result = core.invoke("plot_strategy", {
    "prompt": "都市玄幻，主角获得上古传承",
    "context": "已设定：修炼等级分九重天..."
})

# 评估
eval_result = core.invoke("evaluator", {
    "text": "待评估的小说文本..."
})

# 裁决
judge_result = core.invoke("judge", {
    "candidate": "候选章节A内容",
    "reference": "候选章节B内容"
})
```

---

## 源码位置

- 墨枢核心：`~/openclaw-workspace/skills/NovelClaw/apps/novelclaw/`
- 能力注册：`capability_registry.py`
- Agent 实现：`agents/` (writer_agent.py, evaluator_agent.py, ...)
- 记忆系统：`rag/memory_system.py`, `rag/retriever.py`
- 实时编辑：`rag/realtime_editor.py`
- 静态知识库：`rag/static_knowledge_base.py`
