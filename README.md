<div align="center">

# 墨枢 · NovelClaw

**中文网文爆款写作 · 多 Agent 协同系统**

> 「让 AI 像人一样写网文，而不是像 AI 一样写网文。」

[![License: MIT](https://img.shields.io/badge/License-MIT-DC2626.svg?style=flat-square)](LICENSE)
[![Codex](https://img.shields.io/badge/Codex-Plugin%20Ready-7C3AED.svg?style=flat-square)](codex-marketplace/)
[![Version](https://img.shields.io/badge/version-v0.2.0-059669.svg?style=flat-square)](https://github.com/Louis0719/NovelClaw/releases)

</div>

<p align="center">
  <img src="assets/hero-banner.png" alt="墨枢 Hero" width="100%"/>
</p>

## ✨ 为什么用墨枢？

**番茄/七猫/17K 爆款逻辑内嵌**，让 AI 写作不再是"凑字数"。

- 🏗️ **多 Agent 协同**：建筑师 / 写手 / 验证 / 审计 四角色分离，杜绝"自评自写"
- 📖 **爆款方法论**：30 字卖点 + 200 字故事核 + 五幕大纲，结构化开书
- 🚫 **去 AI 味**：20 项检测标准，自动识别并改写"机器腔"
- 📊 **评审打分**：9 维度淘汰制 + 7 维度雷达图，每章可量化
- 🧠 **记忆感知**：章节上下文自动继承，角色关系全局一致
- 🔌 **Codex 兼容**：一行命令装进 OpenAI Codex CLI

---

## 🚀 快速开始

### 方式 A：Codex CLI 安装（推荐）

```bash
# 1. 添加 NovelClaw Marketplace
codex plugin marketplace add https://github.com/Louis0719/NovelClaw --sparse codex-marketplace

# 2. 安装墨枢
codex plugin add moshu@novelclaw-marketplace
```

### 方式 B：本地克隆

```bash
git clone https://github.com/Louis0719/NovelClaw.git
cd NovelClaw
# 直接加载 skills/moshu/SKILL.md 即可使用
```

---

## 📦 插件生态（3 个 Codex 插件）

| 插件 | 简介 | 类别 |
|------|------|------|
| **🖌️ moshu** v2.1.0 | 中文网文爆款写作 AI 搭档 | Writing |
| **📖 novel-reader** v1.0.0 | 17K 等平台网文内容抓取与清洗 | Productivity |
| **🌌 tianming-novel-system** v1.0.0 | 长篇小说协同创作系统（5件套知识库） | Writing |

---

<p align="center">
  <img src="assets/codex-bg.png" alt="Codex" width="100%"/>
</p>

## 🎯 核心能力

### 🖌️ 墨枢 Moshu v2.1.0

**触发条件**

- 主动：`写小说` / `继续写第X章` / `去AI味` / `评审` / `润色`
- 被动：提到 章节 / 大纲 / 角色 / 人设 / 爽点 / 钩子 / 世界观

**能力清单**

| 模块 | 功能 |
|------|------|
| 立项 | 30字卖点 + 200字故事核 + 五幕大纲 |
| 章节 | 章节启动 → 依赖图谱 → packet-first 单章写作 |
| 评审 | 9维度淘汰制 + 7维度雷达图 |
| 润色 | 20项 AI 味检测 + 自动改写 |
| 记忆 | 章节上下文继承 + 角色关系图 |
| 风格 | 风格库采样 + 人物命名体系 |

### 📖 Novel Reader v1.0.0

- Playwright 驱动 17K 主力站 + 备用平台
- 目录抓取 + 章节阅读 + 内容清洗
- 适合素材收集 / 爆款拆解 / 风格采样

### 🌌 天命 Tianming Novel System v1.0.0

- **5 件套知识库**：《世界基石》《世界观规则》《角色档案》《档案事件》《文风样本》
- **五阶段工作流**：天命：大纲 → 规划 → 目录 → 草案 → 正文 → 体检 → 存档
- 解决长篇项目的 跨章节一致性 / 伏笔回收 / 节奏控制 / 文风稳定

---

## 🛠️ 开发者

### 本地测试 Codex 插件

```bash
# 1. 添加本地 marketplace
codex plugin marketplace add ./codex-marketplace

# 2. 查看可用插件
codex plugin list --available

# 3. 安装测试
codex plugin add moshu@novelclaw-marketplace
```

### 添加新插件

```text
codex-marketplace/
├── .agents/plugins/marketplace.json     # 顶层清单
└── plugins/
    └── your-plugin/
        ├── .codex-plugin/plugin.json   # 插件元数据
        ├── pyproject.toml
        ├── README.md
        ├── assets/{icon,logo}.png
        └── skills/your-plugin/SKILL.md
```

---

## 📊 项目指标

| 维度 | 数值 |
|------|------|
| 当前版本 | v0.2.0 |
| 核心能力 | 20 项已就位 |
| Codex 插件 | 3 个 |
| License | MIT |
| Stars | ⭐ 欢迎 Star |

---

## 📜 License

MIT © [Louis / 来财](https://github.com/Louis0719)

---

<p align="center">
  <sub>🌌 墨枢 NovelClaw · 中文网文写作的未来，从这里开始</sub>
</p>