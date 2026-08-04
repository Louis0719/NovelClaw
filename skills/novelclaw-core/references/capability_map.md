# 墨枢能力映射表（Capability Map）

本文档从 `capability_registry.py` 中的 `CapabilitySpec` 数据类提取，列出全部 20 项墨枢核心能力。

## CapabilitySpec 数据结构

```python
@dataclass(frozen=True)
class CapabilitySpec:
    slug: str                          # 能力唯一标识符
    name_en: str                       # 英文名称
    name_zh: str                       # 中文名称
    category_en: str                    # 英文分类
    category_zh: str                   # 中文分类
    description_en: str                # 英文描述
    description_zh: str                # 中文描述
    manager_action: Optional[str]      # Manager 动作名称
    default_enabled: bool              # 默认启用
    always_enabled: bool               # 强制启用（不可关闭）
    order: int                         # 排序顺序
```

---

## 能力总表（20项）

| # | Slug | 中文名 | 英文名 | 分类(中文) | 分类(英文) | Manager Action | 默认启用 | 强制启用 | 顺序 |
|---|------|--------|--------|------------|------------|----------------|----------|----------|------|
| 1 | `plot_strategy` | 情节策略 | Plot Strategy | Claw 动作 | Claw Actions | `plot_strategy` | ✓ | | 10 |
| 2 | `retrieve_context` | 上下文检索 | Context Retrieval | Claw 动作 | Claw Actions | `retrieve_context` | ✓ | | 20 |
| 3 | `enrich_character` | 人物强化 | Character Enrichment | Claw 动作 | Claw Actions | `enrich_character` | ✓ | | 30 |
| 4 | `enrich_world` | 世界观强化 | World Enrichment | Claw 动作 | Claw Actions | `enrich_world` | ✓ | | 40 |
| 5 | `inspect_workspace` | 检查工作区 | Inspect Workspace | 本地工具 | Local Tools | `inspect_workspace` | ✓ | | 45 |
| 6 | `draft_chapter` | 章节起草 | Draft Chapter | 核心写作 | Core Writing | `draft_chapter` | | ✓ | 50 |
| 7 | `rewrite_chapter` | 章节重写 | Rewrite Chapter | 核心写作 | Core Writing | `rewrite_chapter` | | ✓ | 60 |
| 8 | `finalize` | 定稿 | Finalize | 核心写作 | Core Writing | `finalize` | | ✓ | 70 |
| 9 | `sync_storyboard` | 同步故事板 | Sync Storyboard | 本地工具 | Local Tools | `sync_storyboard` | ✓ | | 80 |
| 10 | `sync_characters` | 同步角色资产 | Sync Characters | 本地工具 | Local Tools | `sync_characters` | ✓ | | 90 |
| 11 | `sync_world` | 同步世界设定 | Sync World | 本地工具 | Local Tools | `sync_world` | ✓ | | 100 |
| 12 | `idea_analyzer` | 创意分析 | Idea Analyzer | 辅助技能 | Support Skills | — | ✓ | | 110 |
| 13 | `analyzer` | 任务分析 | Task Analyzer | 辅助技能 | Support Skills | — | ✓ | | 120 |
| 14 | `dynamic_memory` | 动态记忆 | Dynamic Memory | 记忆系统 | Memory System | — | | ✓ | 130 |
| 15 | `turning_point_tracker` | 转折点追踪 | Turning Point Tracker | 辅助技能 | Support Skills | — | ✓ | | 140 |
| 16 | `consistency_checker` | 一致性检查 | Consistency Checker | 辅助技能 | Support Skills | — | ✓ | | 150 |
| 17 | `realtime_editor` | 实时编辑 | Realtime Editor | 辅助技能 | Support Skills | — | ✓ | | 160 |
| 18 | `evaluator` | 评估器 | Evaluator | 辅助技能 | Support Skills | — | ✓ | | 170 |
| 19 | `judge` | 裁决器 | Judge | 辅助技能 | Support Skills | — | ✓ | | 180 |

---

## 按分类分组

### Claw 动作（Claw Actions）

| Slug | 中文名 | 英文名 | 描述(中文) | Manager Action |
|------|--------|--------|------------|----------------|
| `plot_strategy` | 情节策略 | Plot Strategy | 在起草正文前规划章节推进、冲突升级与关键转折点 | `plot_strategy` |
| `retrieve_context` | 上下文检索 | Context Retrieval | 把相关的动态记忆、事实信息和最近写作状态重新拉回当前循环 | `retrieve_context` |
| `enrich_character` | 人物强化 | Character Enrichment | 强化人物动机、关系网络、行为边界和角色一致性 | `enrich_character` |
| `enrich_world` | 世界观强化 | World Enrichment | 明确世界规则、场景约束、设定事实和可复用的正典信息 | `enrich_world` |

### 核心写作（Core Writing）

| Slug | 中文名 | 英文名 | 描述(中文) | Manager Action | 强制启用 |
|------|--------|--------|------------|----------------|----------|
| `draft_chapter` | 章节起草 | Draft Chapter | 生成当前章节的主体正文草稿 | `draft_chapter` | ✓ |
| `rewrite_chapter` | 章节重写 | Rewrite Chapter | 当质量、节奏或长度不达标时，对草稿进行重写或压缩 | `rewrite_chapter` | ✓ |
| `finalize` | 定稿 | Finalize | 当当前候选稿达到可接受标准后完成定稿 | `finalize` | ✓ |

### 本地工具（Local Tools）

| Slug | 中文名 | 英文名 | 描述(中文) | Manager Action |
|------|--------|--------|------------|----------------|
| `inspect_workspace` | 检查工作区 | Inspect Workspace | 在执行下一步之前，检查本地运行工作区、章节文件和当前记忆资产 | `inspect_workspace` |
| `sync_storyboard` | 同步故事板 | Sync Storyboard | 把当前章节 brief 和 Claw 计划写入本地工作区文件与大纲资产 | `sync_storyboard` |
| `sync_characters` | 同步角色资产 | Sync Characters | 提取当前角色状态，并写入本地文件以及角色记忆 | `sync_characters` |
| `sync_world` | 同步世界设定 | Sync World | 把世界规则与连续性事实提取到本地工作区文件和世界记忆 | `sync_world` |

### 辅助技能（Support Skills）

| Slug | 中文名 | 英文名 | 描述(中文) |
|------|--------|--------|------------|
| `idea_analyzer` | 创意分析 | Idea Analyzer | 把粗糙想法整理为包含题材、角色、目标和约束的稳定提案 |
| `analyzer` | 任务分析 | Task Analyzer | 判断当前步骤更需要规划、起草、修订还是收束整理 |
| `turning_point_tracker` | 转折点追踪 | Turning Point Tracker | 追踪章节是否在真正推动故事向前发展 |
| `consistency_checker` | 一致性检查 | Consistency Checker | 检查人物、世界观、时间线和既有事实之间的连续性 |
| `realtime_editor` | 实时编辑 | Realtime Editor | 定位草稿中的薄弱片段并执行针对性的修订 |
| `evaluator` | 评估器 | Evaluator | 评估候选稿的一致性、节奏、情绪力度和任务匹配度 |
| `judge` | 裁决器 | Judge | 当多个章节候选结果接近时，用于做最终裁决 |

### 记忆系统（Memory System）

| Slug | 中文名 | 英文名 | 描述(中文) | 强制启用 |
|------|--------|--------|------------|----------|
| `dynamic_memory` | 动态记忆 | Dynamic Memory | 跨轮次保存可复用的故事状态、章节简报、事实信息和工作记忆 | ✓ |

---

## Claw Action 列表（8项有 manager_action）

```python
def claw_action_specs() -> List[CapabilitySpec]:
    return [item for item in CAPABILITY_REGISTRY if item.manager_action]
```

即：`plot_strategy`, `retrieve_context`, `enrich_character`, `enrich_world`, `inspect_workspace`, `draft_chapter`, `rewrite_chapter`, `finalize`, `sync_storyboard`, `sync_characters`, `sync_world`

共 11 项（不是 8 项，与源码注释略有出入，以实际代码为准）。

---

## 辅助函数

### capability_map()
返回 `{slug: CapabilitySpec}` 字典，用于按 slug 查找能力定义。

### default_enabled_capability_slugs()
返回默认启用的能力 slug 集合（`default_enabled=True` 或 `always_enabled=True`）。

### normalize_capability_slugs(values: Iterable[str])
标准化输入的能力 slug 列表，去重并过滤未知 slug，自动补充 `always_enabled` 的能力。

### enabled_capability_slugs_from_env(raw: str)
从环境变量字符串（如 `"plot_strategy,enrich_character"`）解析启用的能力集合。

### enabled_claw_actions(enabled_slugs: Iterable[str])
根据启用的能力 slug 集合，返回对应的 `manager_action` 集合。
