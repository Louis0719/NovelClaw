# 评估报告格式（Evaluation Report）

本文档从 `evaluator_agent.py` 提取评估报告的 JSON 结构、字段说明和输出示例。

---

## EvaluatorAgent 输出格式

### `generate()` 方法返回格式

```python
{
    "agent": str,          # "创意评估Agent" 或 "Evaluator Agent"
    "role": str,           # "evaluator"
    "content": str,        # 原始LLM输出（JSON字符串）
    "parsed": dict,         # 解析后的JSON字典
    "type": str,           # "evaluation"
}
```

### `evaluate_multiple()` 方法返回格式

```python
{
    "evaluation": {
        "coherence_score": float,   # 0.0-1.0
        "novelty_score": float,    # 0.0-1.0
        "overall_score": float,    # 0.0-1.0
        "emotional_score": float,  # 0.0-1.0
        "suggestions": List[str]   # 改进建议列表
    },
    "raw": dict  # 原始 generate() 结果
}
```

---

## 评估维度说明

| 字段 | 中文名 | 类型 | 范围 | 说明 |
|------|--------|------|------|------|
| `overall_score` | 综合分数 | float | 0.0-1.0 | 综合质量评估，权重最高的指标 |
| `coherence` / `coherence_score` | 连贯性 | float | 0.0-1.0 | 文本内部逻辑自洽程度 |
| `novelty` / `novelty_score` | 新颖性 | float | 0.0-1.0 | 创意和独特性程度 |
| `logic` | 逻辑性 | float | 0.0-1.0 | 情节推进的逻辑合理性 |
| `pacing` | 节奏 | float | 0.0-1.0 | 叙事节奏把控能力 |
| `emotional_score` / `emotional` | 情绪力度 | float | 0.0-1.0 | 情感共鸣和感染力 |
| `suggestions` | 改进建议 | List[str] | — | 具体改进建议列表 |

---

## 评分标准参考

### 分数区间参考

| 分数区间 | 质量等级 | 说明 |
|----------|----------|------|
| 0.9-1.0 | 优秀 | 达到专业发表水准 |
| 0.75-0.89 | 良好 | 有小幅改进空间 |
| 0.6-0.74 | 可接受 | 基本可用，需修订 |
| 0.4-0.59 | 较差 | 需要较大修改 |
| 0.0-0.39 | 很差 | 需要重写 |

### 通过阈值

- **默认通过阈值**：`overall_score >= 0.6`
- **高质量阈值**：`overall_score >= 0.75`
- **多维度要求**：`coherence >= 0.5` 且 `novelty >= 0.5`

---

## 输出示例

### JSON 输出示例（中文模式）

```json
{
  "overall_score": 0.72,
  "coherence": 0.75,
  "novelty": 0.68,
  "logic": 0.70,
  "pacing": 0.72,
  "suggestions": [
    "第三章的转折略显突兀，建议增加情感铺垫",
    "主角的动机在中期有些模糊，需要强化内心描写",
    "建议在高潮前增加一个小的挫折来增加张力"
  ]
}
```

### 规范化后格式（用于奖励系统）

```json
{
  "coherence_score": 0.75,
  "novelty_score": 0.68,
  "overall_score": 0.72,
  "emotional_score": 0.72,
  "suggestions": [
    "第三章的转折略显突兀，建议增加情感铺垫",
    "主角的动机在中期有些模糊，需要强化内心描写",
    "建议在高潮前增加一个小的挫折来增加张力"
  ]
}
```

### 解析失败时的默认兜底

```python
{
    "overall_score": 0.6,
    "coherence": 0.6,
    "novelty": 0.6,
    "logic": 0.6,
    "pacing": 0.6,
    "suggestions": ["Refine transitions", "Tighten logic"]
}
```

---

## JudgeAgent 裁决报告格式

### 输出格式（JSON）

```json
{
  "candidate": {
    "Relevance": 8,
    "Coherence": 7,
    "Empathy": 8,
    "Surprise": 6,
    "Creativity": 7,
    "Complexity": 7,
    "overall": 7.2
  },
  "reference": {
    "Relevance": 8,
    "Coherence": 8,
    "Empathy": 7,
    "Surprise": 7,
    "Creativity": 6,
    "Complexity": 8,
    "overall": 7.3
  },
  "winner": "reference",
  "notes": [
    "Reference version has better coherence overall",
    "Candidate wins on surprise factor but loses on empathy"
  ]
}
```

### 六维度说明（JudgeAgent）

| 维度 | 英文名 | 分值范围 | 说明 |
|------|--------|----------|------|
| Relevance | 相关性 | 0-10 | 与主题/需求的契合度 |
| Coherence | 连贯性 | 0-10 | 叙事结构和逻辑的自洽程度 |
| Empathy | 移情 | 0-10 | 引发读者情感共鸣的能力 |
| Surprise | 出人意料 | 0-10 | 反转和意外情节的质量 |
| Creativity | 创意 | 0-10 | 独特性和创新程度 |
| Complexity | 复杂度 | 0-10 | 叙事层次和深度 |
| overall | 综合分 | 0-10 | 各维度加权平均 |

### 裁决结果

| 值 | 含义 |
|----|------|
| `"candidate"` | 候选版本胜出 |
| `"reference"` | 参考版本胜出 |
| `"tie"` | 平局 |

---

## 评估报告使用流程

```
生成文本（WriterAgent）
    ↓
EvaluatorAgent.evaluate_multiple([writer_result])
    ↓
检查 overall_score >= 0.6 ?
    ├── 是 → 检查 coherence >= 0.5 && novelty >= 0.5 ?
    │       ├── 是 → 通过，进入下一章或 Finalize
    │       └── 否 → RealtimeEditor 针对性修改
    └── 否 → Rewrite（重写）
                ↓
            重新评估
```

---

## 字段映射关系

EvaluatorAgent 支持两种字段命名：

| 原始字段（中文模式） | 规范化字段（奖励系统） |
|---------------------|---------------------|
| `coherence` | `coherence_score` |
| `novelty` | `novelty_score` |
| `overall_score` | `overall_score` |
| `pacing` 或 `logic` | `emotional_score` |

`_normalize_scores()` 方法负责将各种命名变体统一为规范字段名。

---

## temperature 设置

EvaluatorAgent 的 `temperature` 比配置值低 0.2，使评估结果更稳定确定：

```python
response = self.llm_client.chat(
    messages=messages,
    temperature=max(0.1, self.config.temperature - 0.2),
)
```

JudgeAgent 同样降低 temperature：

```python
response = self.llm_client.chat(
    messages=messages,
    temperature=max(0.1, self.config.temperature - 0.2),
    max_tokens=1200,
)
```
