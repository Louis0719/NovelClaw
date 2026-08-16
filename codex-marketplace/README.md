# 墨枢 NovelClaw Codex Marketplace

> 中文网文写作 AI 插件生态 — 多Agent协同 · 去AI味 · 爆款方法论 · 天命评审

通过 [OpenAI Codex CLI](https://github.com/openai/codex) 一键安装墨枢生态所有 AI 写作插件。

## 🚀 快速安装

### 1. 添加 NovelClaw Marketplace

```bash
# 方式A：完整下载（推荐）
codex plugin marketplace add https://github.com/Louis0719/NovelClaw --sparse codex-marketplace

# 方式B：本地路径（开发调试）
codex plugin marketplace add ./codex-marketplace
```

### 2. 安装插件

```bash
# 墨枢 — 中文网文爆款写作
codex plugin add moshu@novelclaw-marketplace

# 网文阅读器 — 17K 等平台内容抓取
codex plugin add novel-reader@novelclaw-marketplace

# 天命 — 长篇小说协同创作系统
codex plugin add tianming-novel-system@novelclaw-marketplace
```

### 3. 查看已装

```bash
codex plugin list
```

## 📦 插件列表

| 插件 | 版本 | 类别 | 简介 |
|------|------|------|------|
| **moshu** 墨枢 | 2.1.0 | Writing | 中文网文爆款写作 AI 搭档 |
| **novel-reader** | 1.0.0 | Productivity | 国内小说网站内容抓取 |
| **tianming-novel-system** 天命 | 1.0.0 | Writing | 长篇小说协同创作系统 |

## 🎯 插件能力速览

### 🖌️ 墨枢
- 30字卖点 + 200字故事核方法论
- 20项AI味自动检测标准
- 9维度淘汰制评审 + 7维度雷达图
- 番茄/七猫/17K爆款逻辑内嵌

### 📖 Novel Reader
- Playwright 驱动 17K 主力站
- 目录抓取 + 章节阅读 + 内容清洗
- 适合素材收集/爆款拆解/风格采样

### 🌌 天命
- 5件套知识库（《世界基石》《世界观规则》《角色档案》《档案事件》《文风样本》）
- 大纲→草案→正文→体检→存档五阶段工作流
- 解决跨章节世界观一致性、伏笔回收、节奏控制、文风稳定

## 🛠️ 开发者

### 添加新插件

```bash
codex-marketplace/
├── .agents/plugins/marketplace.json     # 顶层清单
└── plugins/
    └── your-plugin/
        ├── .codex-plugin/plugin.json   # 插件元数据
        ├── pyproject.toml
        ├── README.md
        ├── assets/
        │   ├── icon.png
        │   └── logo.png
        └── skills/
            └── your-plugin/
                └── SKILL.md
```

### 本地测试

```bash
codex plugin marketplace add ./codex-marketplace
codex plugin list --available
codex plugin add your-plugin@novelclaw-marketplace
```

## 📜 License

MIT

## 🔗 链接

- 主仓库: https://github.com/Louis0719/NovelClaw
- Codex CLI: https://github.com/openai/codex
- 作者主页: https://github.com/Louis0719
