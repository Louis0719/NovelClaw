# 墨枢（NovelClaw）

<div align="center">

**中文长篇网文 · 多 Agent 协同写作工作台**

> 「让百万字小说，从第一章到完本，人设一致、伏笔不丢、机器腔归零。」

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Writing%20Workspace-009688?style=flat-square&logo=fastapi&logoColor=white)
![Scope](https://img.shields.io/badge/Scope-Long--Form%20Fiction-F97316?style=flat-square)
![Mode](https://img.shields.io/badge/Mode-Chapter%20Control%20%26%20Memory-0f766e?style=flat-square)
[![License: MIT](https://img.shields.io/badge/License-MIT-DC2626.svg?style=flat-square)](LICENSE)
[![Release](https://img.shields.io/badge/version-v0.3.1-059669.svg?style=flat-square)](https://github.com/Louis0719/NovelClaw/releases)

[🇬🇧 English README](README.md) ·
[快速开始](#快速开始) ·
[核心能力](#核心能力) ·
[架构](#架构) ·
[路线图](#路线图)

</div>

---

## 这是什么？

**墨枢**（NovelClaw）是专为中文网文作者设计的**结构化长篇创作工作台**。它不是"输入 prompt → 一次出稿"的一次性工具，而是把写作组织成：

- 📝 **持续会话** — 章节之间保持上下文，不丢设定
- 🧠 **记忆银行** — 角色关系、世界观、伏笔随章节自动积累
- 🔍 **可检查输出** — 每章生成内容可审阅、可修改、可回退
- 🤖 **9 角色 Agent 协作** — 写手 / 评审 / 角色 / 世界 / 情节 / 检索 / 评估 / 构思 各司其职，杜绝"自评自写"

## 痛点 → 方案

| 写百万字必踩的坑 | 墨枢怎么解 |
|---|---|
| AI 写的"机写味"被编辑一眼识破 | 20 项去 AI 味检测，生成即检测 |
| 写到 30 万字人设 OOC、世界观崩了 | 记忆银行（Memory Bank）跨章节追踪 |
| 埋了 15 条伏笔，结局忘了 10 条 | Storyboard 可视化所有线索，已收/未收一眼看清 |
| 每次续写都要复述前情 | Session 上下文自动继承 |
| 不知道均订卡在哪 | 内嵌番茄/七猫爆款逻辑，逐章评审打分 |

## 核心能力

### ✍️ 章节级写作控制
- 逐章生成，可审阅后再确认
- Session 上下文跨章节保留
- 章节进度实时监控（`progress.log`）
- 生成内容可编辑、可回退

### 🧠 记忆银行（Memory Bank）
- 角色设定自动追踪（性格变化、外貌、关系）
- 世界观规则持久存储
- 章节摘要自动积累
- 记忆快照可导出、可复用

### 🔍 去 AI 味检测
- 20 项 AI 味检测标准
- 实时预警 + 修复建议
- 覆盖过渡词、句式、结构等维度

### 📊 爆款评审
- 9 维度淘汰制评审
- 逐章打分 + 改进建议
- 卖点强化 / 节奏诊断

## 9 个 Agent 角色

| Agent | 职责 |
|---|---|
| `writer_agent` | 章节正文写作 |
| `character_agent` | 角色设定与人设一致性 |
| `world_agent` | 世界观规则与设定一致性 |
| `plot_agent` | 情节线索管理与伏笔追踪 |
| `judge_agent` | 六维度评分裁判（相关性/连贯/共情/惊喜/创意/复杂度）|
| `evaluator_agent` | 多维度评估打分 |
| `retrieval_agent` | 上下文检索（RAG） |
| `idea_copilot_agent` | 创意构思辅助 |
| `base_agent` | Agent 基类与共享能力 |

## 快速开始

<details open>
<summary><b>🐳 Docker 部署（推荐）</b></summary>

**Windows：**
```batch
docker-start.bat
```

**Linux/Mac：**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

🌐 访问地址：
```text
公开入口   http://localhost:8010/select-mode
MultiAgent http://localhost:8011/dashboard
墨枢主站   http://localhost:8012/dashboard
```

</details>

<details>
<summary><b>💻 Windows 一键启动</b></summary>

```powershell
.\START_LOCAL.bat
```

访问：`http://127.0.0.1:8012/dashboard`

</details>

> 📖 **完整操作手册**：Docker 详细配置、`.env` 设置、API Token、Claw Mode 分步教程见 [README.md](README.md)（英文版）。

## 架构

```
┌─────────────────────────────────────────────┐
│  Portal (8010) — 公开入口，分发到工作区       │
└─────────────┬───────────────────────────────┘
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
┌────────┐ ┌─────────┐ ┌────────────┐
│MultiAg.│ │NovelClaw│ │ Auth Portal│
│ (8011) │ │ (8012)  │ │            │
│ 构思   │ │ 核心写作│ │            │
└────────┘ └────┬────┘ └────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
 ┌─────────┐      ┌──────────┐
 │ 9 Agents│      │ Memory   │
 │ 协同    │      │ Bank     │
 └─────────┘      └──────────┘
```

## 路线图

- [x] **v0.3.1** — Moshu 成本控制（Haiku 打分模式，降本 90%）
- [x] **v0.3.0** — Moshu 去 AI 味升级（5 大新能力 + 全量 bug 修复）
- [x] **v0.2.0** — Codex Plugin 兼容首发（moshu / novel-reader / tianming 三插件）
- [ ] **v1.0** — 番茄/七猫平台数据对接，爆款榜实时分析
- [ ] **v1.1** — 多人协作模式（工作室版）

## 文档索引

- 🇬🇧 [README.md](README.md) — 完整英文文档 + Claw Mode 操作手册
- 📦 [Releases](https://github.com/Louis0719/NovelClaw/releases) — 版本发布记录
- ⚖️ [MIT License](LICENSE)

---

<div align="center">

**如果墨枢帮你写出了爆本，欢迎点个 ⭐ 鼓励一下**

<sub>Made with 🖌️ by Louis · 墨枢开发组</sub>

</div>