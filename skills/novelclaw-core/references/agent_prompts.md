# Agent 系统文档

墨枢内置 8 个专业化 Agent，全部继承自 `BaseAgent`。本文档从各 Agent 源码中提取角色定义、system_prompt 和核心方法签名。

---

## BaseAgent — 基础类

### 类定义
```python
class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        config: Config,
        llm_client: LLMClient,
        retriever: Optional[Retriever] = None,
        memory_system: Optional[MemorySystem] = None,
        static_kb: Optional[StaticKnowledgeBase] = None
    )
```

### 核心属性
- `name` — Agent 名称
- `role` — 角色标识（plot/character/world/retrieval/writer/evaluator/judge）
- `system_prompt` — 系统提示词
- `conversation_history` — 对话历史列表

### 核心方法

#### `generate(prompt, context=None) -> Dict`
抽象方法，子类必须实现。返回格式：
```python
{
    "agent": str,   # Agent 名称
    "role": str,    # 角色标识
    "content": str,  # 生成的内容
    "type": str,     # 类型标签
    # ... 其他子类特定字段
}
```

#### `_build_messages(prompt, context=None, use_rag=True, topic=None, use_memory=True, use_static_kb=True, genre=None, style_tags=None) -> List[Dict]`
构建发送给 LLM 的消息列表，包含：
1. system_prompt
2. 动态记忆上下文（来自 MemorySystem）
3. Claw 工作记忆上下文
4. 外部静态知识库的风格参考（可选）
5. RAG 检索到的上下文（可选）
6. 对话历史（最近 5 轮）
7. 当前用户 prompt

#### `_get_claw_memory_banks() -> List[str]`
按 role 返回需要访问的 Claw Memory Bank 列表：
- `plot`: task_briefs, story_premise, style_guide, chapter_briefs, scene_cards, continuity_facts, working_set
- `character`: task_briefs, chapter_briefs, entity_state, relationship_state, revision_notes, working_set
- `world`: task_briefs, chapter_briefs, world_state, continuity_facts, revision_notes, working_set
- `retrieval`: task_briefs, chapter_briefs, entity_state, world_state, continuity_facts, tool_observations, working_set
- `writer`: task_briefs, story_premise, style_guide, chapter_briefs, entity_state, relationship_state, world_state, continuity_facts, revision_notes, working_set

---

## WriterAgent — 写作Agent

### 类定义
```python
class WriterAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
        target_length: Optional[int] = None,
        target_min_chars: Optional[int] = None,
        target_max_chars: Optional[int] = None,
    ) -> Dict
```

### 角色定位
- **中文**：你是一名长篇小说写作专家，擅长在既有人物、情节和世界观基础上写连贯正文。
- **英文**：Expert long-form fiction writer.

### System Prompt（中文模式）
```
你是一名长篇小说写作专家，擅长在既有人物、情节和世界观基础上写连贯正文。
硬性规则：
1) 严格遵循给定大纲与设定，不无依据扩写；
2) 保持与上文连续，不跳章，不重复；
3) 只输出小说正文，不输出提纲或列表；
4) 信息不足时优先延展既有线索，而不是凭空设定。
```

### 返回格式
```python
{
    "agent": "写作Agent",
    "role": "writer",
    "content": "生成的正文...",
    "type": "writer"
}
```

### 长度控制
- `target_min_chars` / `target_max_chars` 优先于 `target_length`
- 若指定范围，按范围输出；否则按 `target_length * 0.9 ~ 1.12` 控制
- 无目标时默认 1000-1800 字（中文）或 1000-1800 words（英文）

---

## PlotAgent — 情节构建Agent

### 类定义
```python
class PlotAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
    ) -> Dict
```

### 角色定位
- **中文**：你是一个专业的情节构建专家。
- **英文**：Professional plot designer.

### System Prompt（中文模式）
```
你是一个专业的情节构建专家。你的职责是：
1. 设计引人入胜的故事主线和情节分支
2. 确保情节逻辑严密、前后呼应
3. 创造戏剧冲突和高潮
4. 保持情节的连贯性和创新性
请用中文回答，提供详细、有创意的情节设计。
```

### 特点
- `temperature` 相比配置值提高 0.1，以增加创意性
- 启用 RAG、记忆系统和静态知识库

---

## CharacterAgent — 人物塑造Agent

### 类定义
```python
class CharacterAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
    ) -> Dict
```

### 角色定位
- **中文**：你是一个专业的人物塑造专家。
- **英文**：Professional character designer.

### System Prompt（中文模式）
```
你是一个专业的人物塑造专家。你的职责是：
1. 设计立体、有深度的人物角色
2. 塑造人物的性格、背景、动机和成长弧线
3. 确保人物行为符合其性格设定
4. 创造人物之间的复杂关系
请用中文回答，提供详细、生动的人物设计。
```

---

## WorldAgent — 世界观Agent

### 类定义
```python
class WorldAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
    ) -> Dict
```

### 角色定位
- **中文**：你是一个世界观设计专家。
- **英文**：Worldbuilding expert.

### System Prompt（中文模式）
```
你是一个世界观设计专家。你的职责是：
1. 设计连贯的背景、规则、历史、文化、科技水平
2. 确保内在逻辑和约束保持一致
3. 提供可直接用于写作的具体细节
请用中文回答，提供详细、有深度的世界观设计。
```

---

## EvaluatorAgent — 创意评估Agent

### 类定义
```python
class EvaluatorAgent(BaseAgent):
    def generate(self, prompt: str, context: Optional[str] = None) -> Dict
    
    def evaluate_multiple(self, round_results: List[Dict]) -> Dict
```

### 角色定位
- **中文**：你是一个专业的创意评估专家。
- **英文**：Professional creative-writing evaluator.

### System Prompt（中文模式）
```
你是一个专业的创意评估专家。你的职责是：
1. 评估文本的新颖性、连贯性和情感一致性
2. 检查文本的逻辑一致性和结构完整性
3. 提供具体的改进建议
4. 给出0-1之间的质量分数
请用中文回答，提供详细的评估报告和改进建议。
评估结果请以JSON格式输出：
{
  "overall_score": 0-1,
  "coherence": 0-1,
  "novelty": 0-1,
  "logic": 0-1,
  "pacing": 0-1,
  "suggestions": ["建议1", "建议2", ...]
}
```

### 核心方法

#### `generate(prompt, context=None) -> Dict`
评估文本质量，返回 JSON 格式的评估报告。

#### `evaluate_multiple(round_results: List[Dict]) -> Dict`
批量评估多轮结果，返回：
```python
{
    "evaluation": {
        "coherence_score": float,
        "novelty_score": float,
        "overall_score": float,
        "emotional_score": float,
        "suggestions": List[str]
    },
    "raw": Dict  # 原始结果
}
```

#### `_normalize_scores(parsed: Dict) -> Dict`
将评估器输出规范化为奖励系统友好的分数键名。

### 特点
- `temperature` 比配置值低 0.2（更确定性）
- 不使用 RAG（`use_rag=False`）
- JSON 解析失败时返回默认分数 0.6

---

## JudgeAgent — 裁判Agent

### 类定义
```python
class JudgeAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[list] = None,
    ) -> Dict
```

### System Prompt
```
You are a fair literary judge. Score two stories on six dimensions: Relevance, Coherence, Empathy, Surprise, Creativity, Complexity. Each score 0-10. Output JSON:
{
  "candidate": {"Relevance": x, "Coherence": x, "Empathy": x, "Surprise": x, "Creativity": x, "Complexity": x, "overall": x},
  "reference": {"Relevance": x, "Coherence": x, "Empathy": x, "Surprise": x, "Creativity": x, "Complexity": x, "overall": x},
  "winner": "candidate"|"reference"|"tie",
  "notes": ["short rationale bullet(s)"]
}
Be concise and consistent.
```

### 返回格式
```python
{
    "agent": "JudgeAgent",
    "role": "judge",
    "content": "JSON字符串...",
    "type": "judgment"
}
```

### 六维度说明
| 维度 | 说明 |
|------|------|
| Relevance | 与主题/需求的契合度 |
| Coherence | 叙事连贯性 |
| Empathy | 情感共鸣/移情能力 |
| Surprise | 出人意料程度/反转质量 |
| Creativity | 创意独特性 |
| Complexity | 复杂度/层次感 |

---

## RetrievalAgent — 数据检索Agent

### 类定义
```python
class RetrievalAgent(BaseAgent):
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        topic: Optional[str] = None,
        genre: Optional[str] = None,
        style_tags: Optional[List[str]] = None,
    ) -> Dict
    
    def add_knowledge(self, text: str, metadata: Optional[Dict] = None)
```

### 角色定位
- **中文**：你是一个专业的信息检索和整合专家。
- **英文**：Information retrieval and synthesis expert.

### System Prompt（中文模式）
```
你是一个专业的信息检索和整合专家。你的职责是：
1. 根据需求检索相关的历史、文化、技术背景信息
2. 整合检索到的信息，提供准确、有用的背景知识
3. 确保信息的准确性和相关性
4. 为其他Agent提供信息支持
请用中文回答，提供清晰、有条理的信息整合。
```

### 返回格式
```python
{
    "agent": "数据检索Agent",
    "role": "retrieval",
    "content": "整合后的背景知识...",
    "retrieved_docs": List[Dict],  # 原始检索文档
    "type": "retrieval"
}
```

---

## IdeaCopilotAgent — 创意副驾

### 类定义
```python
class IdeaCopilotAgent:
    def __init__(self, provider_spec: Any, api_key: str)
    
    def generate_turn(
        self,
        *,
        original_idea: str,
        state: Dict[str, Any],
        latest_user_reply: str,
    ) -> Dict[str, Any]
    
    @staticmethod
    def load_state(raw: str) -> Dict[str, Any]
    
    @staticmethod
    def dump_state(state: Dict[str, Any]) -> str
    
    @staticmethod
    def append_user(state: Dict[str, Any], reply: str) -> Dict[str, Any]
    
    @staticmethod
    def append_assistant(state: Dict[str, Any], turn: Dict[str, Any]) -> Dict[str, Any]
    
    @staticmethod
    def latest_turn(state: Dict[str, Any]) -> Dict[str, Any]
    
    @staticmethod
    def to_generation_idea(original_idea: str, state: Dict[str, Any]) -> str
```

### 角色定位
语言路由的协作式构思 Agent，将粗糙想法打磨为稳定的写作 brief。

### `generate_turn` 返回格式
```python
{
    "role": "assistant",
    "analysis": str,          # 分析文本
    "refined_idea": str,      # 精炼后的想法
    "questions": List[str],   # 最多3个问题
    "readiness": int,         # 0-100 准备度
    "ready_hint": str,        # 准备度提示
    "language": str,          # "en" 或 "zh"
    "style_targets": List[str],
    "memory_targets": List[str]
}
```

### 状态管理
- `load_state` / `dump_state` — JSON 序列化/反序列化
- `append_user` / `append_assistant` — 向状态追加消息
- `latest_turn` — 获取最后一条助手回复

### `build_generation_idea`
将精炼后的想法和对话历史组合为生成简报（generation brief），包含：
- refind_idea 主文本
- 语言配置
- 风格目标
- 记忆目标
- 执行偏好（generation_scope, requested_chapters, chapter_pause_mode）
- 最近构思 QA

### 生成偏好（Generation Preferences）
```python
{
    "generation_scope": "auto" | "all" | "limited" | "chapter_by_chapter",
    "requested_chapters": int,
    "chapter_pause_mode": "manual_each_chapter" | "run_to_end" | "auto",
    "user_request": str
}
```
