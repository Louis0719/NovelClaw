---
name: novel-reader
description: 用 Playwright 读取国内小说网站（17K主力 + 备用平台），支持目录、章节阅读、内容清洗。
homepage: 
metadata:
  {
    "openclaw":
      {
        "emoji": "📖",
        "requires": { "bins": ["playwright"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "pip",
              "package": "playwright",
              "bins": ["python3"],
              "label": "Install playwright (pip install playwright && playwright install chromium)"
            }
          ]
      }
  }
---

# 小说阅读器 (novel-reader)

用 Playwright 读取小说网站章节内容，支持去广告清洗。

## 平台支持

| 平台 | 状态 | 备注 |
|------|------|------|
| **17K小说网** | ✅ 主力 | 免费章节完全可读，目录+正文 |
| 起点中文网 | ⚠️ 部分 | 需APP或特殊URL |
| 晋江文学城 | ⚠️ 部分 | 章节URL可构造 |
| 飞卢小说网 | ⚠️ 部分 | 部分章节可读 |
| 纵横中文网 | ❌ 限流 | IP限制 |
| 番茄/七猫 | ❌ 不可用 | 需登录/APP |

## 命令行用法

```bash
# 获取书籍目录
python3 novel_reader.py toc <书籍ID或URL>

# 读章节
python3 novel_reader.py read <书籍ID> <章节ID>

# 直接读任意章节URL
python3 novel_reader.py url https://www.17k.com/chapter/3631088/49406154.html

# 测试所有平台
python3 novel_reader.py sites
```

## 示例

```bash
# 获取目录
python3 novel_reader.py toc 3631088
# → 找到 541 章，列出前100章

# 读指定章节
python3 novel_reader.py read 3631088 49406154

# 从URL直接读
python3 novel_reader.py url https://www.17k.com/chapter/3631088/49406155.html
```

## 工作流程

1. **找书** → 访问 `https://www.17k.com` 搜索书名，获取书籍ID
2. **获取目录** → `toc <书籍ID>` → 找到章节ID
3. **读章节** → `read <书籍ID> <章节ID>` → 纯正文输出

## AI 调用方式

在 Agent 中使用时，直接调用 `read_url()` 函数：

```python
result = await read_url("https://www.17k.com/chapter/3631088/49406154.html")
# result = {'paragraphs': [...], 'raw_len': N, 'para_count': N}
```

返回已清洗的段落列表，可直接用于分析/总结。

## 局限

- 免费章节可读；VIP付费章节需要登录Cookie（暂未实现）
- 部分平台IP限制，需要换IP或用Cookie
- 每次读取约3-5秒（等待JS渲染）
