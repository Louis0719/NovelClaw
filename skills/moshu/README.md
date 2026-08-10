# 墨枢 · Moshu

> 「让AI像人一样写网文，而不是像AI一样写网文。」

中文网文 AI 写作搭档。内置网文去 AI 味体系 + 爆款逻辑 + 天命写作流。

## 功能

- **三流程写作体系**：立项 → 章节写作 → 自查
- **14 维去 AI 味检测**：元叙事 / 系统文 / 都市文 / 词汇 / 节奏 / 过渡词…
- **改写三档位**：minimal / standard / aggressive
- **记忆银行**：world_state.json + 伏笔追踪

## 安装

将 `skills/moshu/` 复制到你的 OpenClaw workspace skills 目录：

```bash
cp -r skills/moshu ~/.openclaw/skills/
# 或复制到项目 workspace
cp -r skills/moshu /path/to/your/project/.agents/skills/
```

重启 OpenClaw 后自动加载。

## 触发词

**主动触发：**
- "写小说"、"写网文"、"继续写第X章"
- "去AI味"、"自查第X章"、"帮我检查"
- "润色"、"改写"、"优化"

**被动触发：**
- 提到章节 / 大纲 / 角色 / 人设 / 爽点 / 虐点 / 钩子 / 世界观

## 文件结构

```
skills/moshu/
├── SKILL.md                    # 主技能文件
├── CHANGELOG.md                # 更新历史
└── templates/                 # 配套模板
    ├── world_state.json.example
    ├── 角色档案.md.example
    └── 伏笔追踪.md.example
```

## 改写档位说明

| 档位 | 适用范围 |
|------|----------|
| minimal | 只替换高频词，不动句式 |
| standard | 替换全部 P0+P1 问题词，调整过渡词 |
| aggressive | 重写段落结构，调整句长分布，补充细节 |

## 版权

MIT License
