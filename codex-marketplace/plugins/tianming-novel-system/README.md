# 天命 · Tianming Novel System

> 长篇小说协同创作系统

## 简介

「天命」是面向长篇小说项目的多Agent协同创作系统。核心解决：
- ✅ 跨章节世界观一致性
- ✅ 伏笔埋设与回收
- ✅ 节奏控制
- ✅ 文风稳定

## 5件套知识库

- `世界基石.md` — 故事核心设定
- `世界观规则.md` — 世界运行规则
- `角色档案.md` — 人物档案
- `档案事件.md` — 重要事件追踪
- `文风样本.md` — 文风参考

## 工作流

```
天命：大纲 → 天命：规划 → 天命：目录 → 天命：草案 → 天命：正文 → 天命：体检 → 天命：存档
```

## 安装

> **前置条件**：`codex --version` ≥ 0.142.5

```bash
# 1. 添加 NovelClaw marketplace
codex plugin marketplace add https://github.com/Louis0719/NovelClaw --sparse codex-marketplace

# 2. 安装天命系统
codex plugin add tianming-novel-system@novelclaw-marketplace
```

## 触发指令

精确指令：`天命：大纲` / `天命：正文` / `天命：体检` / `天命：存档`
自然语言：`写小说` / `写书` / `创作小说` / `开始写作` / `帮我写章节` / `写第X章`

## License

MIT