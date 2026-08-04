# Memory Bank 工作原理

墨枢的记忆系统（MemorySystem）负责跨轮次保存故事状态、事实信息和生成历史，用于减少幻觉和保持一致性。

---

## 架构概览

```
MemorySystem
├── memory_index.json        # 主索引（JSON文件）
├── VectorStore (可选)       # 向量存储（ChromaDB）
└── DocumentProcessor        # 文档处理器（用于embedding）
```

### 记忆类型索引（memory_index.json）

```python
{
    "schema_version": 2,
    "texts": [],            # 生成的正文
    "outlines": [],         # 大纲
    "characters": [],        # 人物
    "world_settings": [],    # 世界观设定
    "plot_points": [],       # 情节要点
    "fact_cards": [],       # 事实卡片
    "claw": {
        # 16个 Claw Memory Banks
    }
}
```

---

## Claw Memory Banks（16个Bank）

```python
CLAW_BANKS = (
    "session_profile",       # 会话配置（语言、模式等）
    "language_profile",      # 语言配置
    "user_preferences",      # 用户偏好
    "task_briefs",           # 任务简报
    "story_premise",         # 故事前提
    "style_guide",           # 风格指南
    "chapter_briefs",        # 章节简报
    "scene_cards",           # 场景卡片
    "entity_state",          # 实体状态（人物状态快照）
    "relationship_state",     # 关系状态
    "world_state",           # 世界状态
    "continuity_facts",      # 连续性事实
    "tool_observations",     # 工具观察结果
    "decision_log",          # 决策日志
    "revision_notes",         # 修订笔记
    "working_set",           # 工作集（滚动摘要等）
)
```

### 记忆项结构

每条记忆项包含：
```python
{
    "id": str,              # 唯一ID，如 "claw_chapter_briefs_20260804_213000_0"
    "bank": str,            # 所属Bank
    "topic": str,           # 主题（用于过滤）
    "content": str,         # 内容文本
    "timestamp": str,       # ISO格式时间戳
    "metadata": dict        # 额外元数据（如 chapter=n）
}
```

---

## 存储机制

### 双重存储

每条记忆同时存储在两个地方：

1. **memory_index.json**（主索引）
   - 结构化存储，所有 Bank 共享
   - 持久化到磁盘
   - 支持快速元数据过滤

2. **VectorStore（ChromaDB）**（可选）
   - 向量嵌入存储，支持语义检索
   - 由 `DocumentProcessor` 处理文本并生成 embedding
   - 仅当 `enable_rag=True` 且 `embedding_model` 非空时启用

### 存储方法

```python
store_claw_memory(
    bank: str,              # Bank名称
    content: str,           # 内容
    topic: str,             # 主题
    metadata: dict,          # 额外元数据
    store_vector: bool      # 是否同时存向量（默认True）
)
```

存储时：
1. 将 content 传给 `DocumentProcessor` 进行分块
2. 为每个 chunk 生成 embedding
3. 同时写入 `memory_index["claw"][bank]` 和 `VectorStore`

---

## 检索机制

### 检索入口：`get_relevant_context()`

这是生成时最常用的检索方法，按以下顺序组合上下文：

#### 1. 固定注入（Fixed Parts）
不依赖向量检索，保证召回：

- **滚动摘要**（`rolling_summary`）：全局进度摘要，最近1条
- **最近章节摘要**（`chapter_summary`）：最近2章摘要
- **关键事实卡片**（`fact_card`）：最近6个

#### 2. Claw 工作记忆
```python
build_claw_context(
    topic=topic,
    current_goal=query[:180],
    banks=[...],
    limit_per_bank=1
)
```
按 Bank 依次输出最新条目。

#### 3. 向量语义检索

```python
retrieve_memories(
    query=query,
    memory_types=["outline", "plot_point", "fact_card"],
    topic=topic,
    top_k=10
)
```

检索后按类型分组注入：
- **人物信息**（type=character）
- **大纲**（type=outline）
- **世界观设定**（type=world_setting）
- **情节要点**（type=plot_point）
- **事实卡片**（type=fact_card）

---

## 向量检索流程

```
query 文本
    ↓
DocumentProcessor.get_embeddings([query])
    ↓
VectorStore.search(embedding, top_k, filter_metadata)
    ↓
返回相似文档列表 [{text, metadata, distance}, ...]
```

### 过滤条件
- `type` — 记忆类型
- `topic` — 主题

### 回退策略
当向量检索失败时，退化为 `_lexical_search()`（词项匹配）：

```python
def _lexical_search(query, memory_types, topic, top_k):
    # 1. 精确匹配 query（权重 +8）
    # 2. token 重叠（每个 +1）
    # 3. topic 匹配（+1.5）
    # 按 score 排序返回 top_k
```

---

## 各类记忆的存储方法

| 方法 | 存储内容 | Bank | 向量存储 |
|------|----------|------|----------|
| `store_chapter_claw_state()` | 章节状态快照 | chapter_briefs, working_set, continuity_facts, revision_notes | ✓ (部分) |
| `store_generated_text()` | 生成的正文 | texts | ✓ |
| `store_outline()` | 大纲 | outlines | ✓ |
| `store_character()` | 人物信息 | characters | ✓ |
| `store_world_setting()` | 世界设定 | world_settings | ✓ |
| `store_plot_point()` | 情节要点 | plot_points | ✓ |
| `store_fact_card()` | 事实卡片 | fact_cards | ✓ |
| `store_claw_memory()` | 通用Claw记忆 | 任意Bank | ✓ |

---

## Claw Context 构建流程

`build_claw_context(topic, current_goal, banks, limit_per_bank)` 的输出格式：

```
=== CURRENT GOAL ===
[当前目标文本]

=== TASK_BRIEFS (2) ===
[条目内容...]

=== STORY_PREMISE (1) ===
[条目内容...]

=== STYLE_GUIDE (1) ===
[条目内容...]

=== CHAPTER_BRIEFS (3) ===
[chapter=5] [outline]
...

=== ENTITY_STATE (1) ===
[条目内容...]

=== CONTINUITY_FACTS (2) ===
[条目内容...]
...
```

每个 Bank 只取最近 `limit_per_bank` 条。

---

## Retriever（动态知识库检索器）

独立于 MemorySystem 的 RAG 模块：

```python
class Retriever:
    enabled: bool                    # enable_rag 配置
    vector_store: VectorStore
    document_processor: DocumentProcessor
    
    def retrieve(query, top_k, filter_metadata) -> List[Dict]
    def retrieve_with_context(query, context, top_k) -> str
    def add_knowledge(text, metadata)
```

与 MemorySystem 的区别：
- **Retriever**：面向外部知识的动态检索（外部文档、参考资料）
- **MemorySystem**：面向生成历史的内部状态管理

---

## StaticKnowledgeBase（静态知识库）

外部大型语料库存储，用于风格参考和减少幻觉：

```python
class StaticKnowledgeBase:
    knowledge_store: VectorStore      # 独立向量库
    document_processor: DocumentProcessor
    
    # 添加数据
    add_novel(novel_text, title, author, genre, style_tags)
    add_creative_text(text, title, text_type, style_tags)
    add_plot_reference(plot_text, title, genre, style_tags)
    
    # 检索
    retrieve_style_reference(query, genre, style_tags, top_k) -> List[Dict]
    retrieve_plot_reference(query, genre, style_tags, top_k) -> List[Dict]
    
    # 上下文构建
    get_style_context(query, genre, style_tags, top_k) -> str
    get_plot_context(query, genre, style_tags, top_k) -> str
```

### 索引分类
```python
{
    "novels": [...],           # 小说
    "creative_texts": [...],   # 创意文本
    "styles": [...],          # 风格（保留字段）
    "plot_references": [...],  # 情节参考
    "total_documents": int     # 总chunk数
}
```

---

## 记忆类型到 Bank 的映射

| 记忆类型 | 主要Bank | 说明 |
|----------|----------|------|
| 章节状态 | chapter_briefs, working_set | 章节简报和滚动摘要 |
| 人物状态 | entity_state, relationship_state | 角色快照和关系 |
| 世界状态 | world_state, continuity_facts | 世界规则和事实 |
| 修订记录 | revision_notes | 评估建议和一致性问题 |
| 决策记录 | decision_log | 工具调用决策 |
| 工具观察 | tool_observations | 工具执行结果 |

---

## 主题过滤（Topic-based Isolation）

所有记忆都与 `topic`（主题）关联，确保不同故事的记忆不会混淆：

```python
# 存储时指定 topic
memory_system.store_claw_memory("chapter_briefs", content, topic="我的玄幻小说")

# 检索时按 topic 过滤
context = memory_system.get_relevant_context(query, topic="我的玄幻小说", ...)
```

`_topic_matches()` 支持的匹配规则：
- 空 topic → 匹配所有
- `"*"` / `"global"` → 匹配所有
- 精确匹配
- 子串包含匹配
