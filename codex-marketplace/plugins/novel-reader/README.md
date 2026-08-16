# Novel Reader

> 国内主流小说网站内容抓取与清洗

## 简介

用 Playwright 读取国内主流小说网站（17K 主力 + 备用平台），支持：
- 📚 目录抓取
- 📖 单章/批量章节阅读
- 🧹 内容清洗（去广告/格式化/统一编码）

## ⚠️ 前置依赖（必须）

本插件依赖 **Playwright**（Python 包 + Chromium 浏览器），**装 Codex 插件前**先装好：

```bash
pip install playwright
playwright install chromium
```

> 这两个是 Python 依赖，Codex CLI 不会自动跑 pip。如果跳过这一步，插件会报 `playwright not found` 错误。

## 安装

> **前置条件**：`codex --version` ≥ 0.142.5 + 上面的 Playwright 已装

```bash
# 1. 添加 NovelClaw marketplace
codex plugin marketplace add https://github.com/Louis0719/NovelClaw --sparse codex-marketplace

# 2. 安装 Novel Reader
codex plugin add novel-reader@novelclaw-marketplace
```

## 使用示例

- 抓取《xxx》最新50章
- 把第123章清洗后保存到本地
- 列出这本书的目录

## 适用场景

- 网文素材收集
- 爆款拆解分析
- 风格采样与作者研究

## License

MIT