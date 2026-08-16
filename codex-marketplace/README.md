# 墨枢 NovelClaw Codex Marketplace

> 中文网文写作 AI 插件生态 — 多Agent协同 · 去AI味 · 爆款方法论 · 天命评审

通过 [OpenAI Codex CLI](https://github.com/openai/codex) 一键安装墨枢生态所有 AI 写作插件。

> **前置条件**：`codex --version` 应 **≥ 0.142.5**，否则请先运行 `codex update`

## 🚀 快速安装

### 1. 添加 NovelClaw Marketplace

```bash
# 方式A：推荐（Sparse 拉取，只下载 codex-marketplace/ 子目录，加速 ~80%）
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
# 应看到：
#   moshu@novelclaw-marketplace                  installed
#   novel-reader@novelclaw-marketplace           installed
#   tianming-novel-system@novelclaw-marketplace  installed
```

### 4. 升级已装插件

```bash
codex plugin upgrade moshu@novelclaw-marketplace    # 升级单个
codex plugin marketplace upgrade novelclaw-marketplace  # 升级整个 marketplace
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

```text
codex-marketplace/
├── .agents/plugins/marketplace.json     # 顶层清单（policy.authentication 只支持 ON_INSTALL / ON_USE，不支持 NONE）
└── plugins/
    └── your-plugin/
        ├── .codex-plugin/plugin.json   # 插件元数据（interface.composerIcon 和 logo 路径必须存在）
        ├── pyproject.toml              # dependencies 字段作为插件运行时依赖参考
        ├── README.md
        ├── assets/
        │   ├── icon.png                # 必需，512x512 推荐
        │   └── logo.png                # 必需，16:9 推荐
        └── skills/
            └── your-plugin/
                └── SKILL.md            # plugin.json 的 skills 字段指向此处（默认 ./skills/）
```

### 本地测试

```bash
codex plugin marketplace add ./codex-marketplace
codex plugin list --available
codex plugin add your-plugin@novelclaw-marketplace    # 测试安装
codex plugin remove your-plugin@novelclaw-marketplace  # 测完清理
```

---

## ❓ Troubleshooting

| 错误信息 | 原因 | 修复 |
|---------|------|------|
| `marketplace 不包含 plugin` | 漏了 `--sparse codex-marketplace` | 重跑带 `--sparse codex-marketplace` |
| `unknown variant NONE` | marketplace.json 的 authentication 字段写错 | 改为 `ON_INSTALL` 或 `ON_USE` |
| `找不到 SKILL.md` | skills/ 子目录命名与 plugin.json 的 name 不一致 | 确保 `plugins/<name>/skills/<name>/SKILL.md` 三处一致 |
| `plugin icon 不存在` | assets/icon.png 或 logo.png 缺失或路径错 | 检查 plugin.json 的 `interface.composerIcon` 路径 |
| `playwright not found`（仅 novel-reader） | Python 依赖未装 | `pip install playwright && playwright install chromium` |

## 📜 License

MIT

## 🔗 链接

- 主仓库: https://github.com/Louis0719/NovelClaw
- Codex CLI: https://github.com/openai/codex
- 作者主页: https://github.com/Louis0719
