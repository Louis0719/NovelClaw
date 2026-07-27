# Novel Studio / 小说创作工作台

A unified long-form fiction studio for **project governance, packet-first chapter writing, project-level style modeling, chapter startup workflows, serialization management, review, and low-token context orchestration**.

一个统一的长篇小说创作工作台，覆盖：**项目治理、packet-first 单章写作、项目级母风格建模、章节启动工作流、连载管理、审校，以及低 token 上下文装载编排**。

It is not a black-box tool that “writes the whole novel for you”. It is a structured fiction operating system for long-running projects:

它不是“自动替你写完整本小说”的黑箱工具，而是一个更像操作系统的长期创作工作台：

- structure the project before writing / 写之前先把项目结构搭稳
- stabilize chapter inputs with packet, summary, style overlay, and object state summary / 写的时候用 packet、summary、style overlay、对象状态摘要稳住输入
- reduce reliance on full chapter rereads / 降低对前文章节全文反复回读的依赖
- keep project style, object state, and workflow emergence aligned / 让项目母风格、对象状态和章节工作流始终对齐

---

## Core Capabilities / 核心能力

### Regression Guard / 回归防漂移
- lightweight smoke regression for scaffold + doctor + chapter-full chain / 为脚手架 + doctor + chapter-full 主链路提供轻量回归护栏
- fixture-oriented validation without committing a whole sample novel / 用 fixture 思路做验证，而不是提交一整套样板小说

### 1. Project Governance / 项目治理
- project skeleton creation / 项目骨架创建
- core/world/subsettings layering / 总设定、规则层、子设定分层
- chapter flow vs brainstorm flow separation / 正文流与发散流分离
- entrypoint layering: README / project-notes / nav / 入口层级分工
- naming conventions and card systems / 命名规范与卡片系统

### 2. Packet-First Chapter Writing / Packet-First 单章写作
- chapter startup packet workflow / 章节启动 packet 工作流
- summary-first continuation / 先摘要、后续写
- object state summaries / 对象状态摘要
- lower-token chapter input packs / 低 token 单章输入包
- fulltext escalation only when necessary / 仅在必要时升级回读全文

### 3. Project Style Model / 项目级风格模型
- mother-style card generation / 项目母风格卡生成
- style extraction from published chapters first / 已发布章节优先的风格提取
- chapter style overlay / 单章风格调用说明
- style consistency checking / 风格一致性检查

### 4. Serialization Management / 连载管理
- chapter summaries and project state / 连载状态跟踪与章节摘要
- pacing, hook, and continuity checks / 节奏、钩子、承接检查
- active indexes for low-token retrieval / 面向低 token 的活动索引

### 5. Review & Polishing / 审校与润色
- logic review / 逻辑检查
- characterization review / 人设检查
- timeline review / 时间线检查
- style polish and de-AI editing / 文风优化与去 AI 味
- internal capability name: `humanize`; user-facing Chinese alias: **去AI味** / 内部能力名统一为 `humanize`，用户侧中文别名统一叫 **去AI味**

### 6. Semi-Automation / 半自动工作流
- init workflow / 初始化工作流
- chapter startup / 章节启动
- style-full / 风格链接入
- chapter-full / 章节可写状态报告
- writeback / refresh / style check / 回写、刷新与风格检查
- workflow runner / 统一 workflow 入口
- `humanize` / **去AI味** mode for chapter-sidecar polishing pass / 面向章节旁路稿的去AI味工作流入口（支持 `light / medium / heavy`，默认 `medium`）

---

### Smoke Regression / 最小回归校验

When you want to verify that the scaffold and core workflow still match the documented standard, run:

```bash
python3 scripts/smoke_regression.py
```

What it validates:
- init scaffold
- governance audit / workflow doctor
- chapter startup packet generation
- chapter-full minimal output set

### Doctor / 双层审计

When you want a fast project health check, run:

```bash
python3 scripts/workflow_runner.py <project-dir> ch_0001 doctor
```

Current `doctor` runs three layers:
- `governance_audit.py`：查骨架、入口、目录与文档漂移
- `consistency_audit.py`：查 `state / chapter-meta / chapter files / packet-first artifacts` 是否互相一致
- `naming_lint.py`：查文件名是否开始把状态、版本、临时标记塞进名字里

Reference:
- `references/fixtures-minimal-layered-project.md`
- `references/scripts-index.md`

---

## v0.8.0 Highlights / v0.8.0 更新亮点

Highlights / 亮点：
- **人物命名指南与命名库**：新增 `references/character-naming-guide.md`（人物命名方法论，覆盖仙侠/古代/民国/都市/农村5类题材+少数民族+外国人，共7类命名规范）和 `references/character-naming-library.md`（按题材×时代×社会环境×家庭审美分层的名字参考池）；都市/农村题材再细分50/60、70/80、90/00、10/20四个代际
- **Humanize 写作综合指南**：`references/humanize-style-guide.md` 整合了完整的去AI味规则体系、AI味句式黑名单（5类）、改稿流程（6步+极简四连）、6+1版本提示词模板，可直接给模型调用
- **网文风格库扩展**：新增6张风格卡（诡秘之主、大奉打更人、第一序列、凡人修仙传、章尾Hook、信息解释控制），覆盖作品级+技巧级风格
- **派/帮/教/宗/门组织命名规则卡**：`references/faction-naming-guide.md` 提供完整的江湖/仙侠势力命名框架与判定口诀
- **章节依赖图谱**：`build_chapter_deps.py` 自动维护 `chapter-deps.json`，防止伏笔断线（v0.6.9引入）
- **Humanize 工作流整合**：`humanize` 能力（对外中文别名：**去AI味**）已接入 chapter-full 报告，支持 light/medium/heavy 三档，默认 medium，输出旁路稿不覆盖原章（v0.6.9引入）
- **Packet-First 写作**：chapter packet、summary-first、对象状态摘要、最小输入包（v0.6.9引入）
- **风格库模式**：可调用已沉淀的风格参考卡，生成可执行风格约束与提示词模板（v0.6.9引入）

---

## v0.7.0 Highlights / v0.7.0 更新亮点

- **Humanize 写作综合指南**：`references/humanize-style-guide.md` 整合了完整的去AI味规则体系、AI味句式黑名单（5类）、改稿流程（6步+极简四连）、6+1版本提示词模板，可直接给模型调用
- **网文风格库扩展**：新增6张风格卡（诡秘之主、大奉打更人、第一序列、凡人修仙传、章尾Hook、信息解释控制），覆盖作品级+技巧级风格
- **派/帮/教/宗/门组织命名规则卡**：`references/faction-naming-guide.md` 提供完整的江湖/仙侠势力命名框架与判定口诀
- **章节依赖图谱**：`build_chapter_deps.py` 自动维护 `chapter-deps.json`，防止伏笔断线（v0.6.9引入）
- **Humanize 工作流整合**：`humanize` 能力（对外中文别名：**去AI味**）已接入 chapter-full 报告，支持 light/medium/heavy 三档，默认 medium，输出旁路稿不覆盖原章（v0.6.9引入）
- **Packet-First 写作**：chapter packet、summary-first、对象状态摘要、最小输入包（v0.6.9引入）
- **风格库模式**：可调用已沉淀的风格参考卡，生成可执行风格约束与提示词模板（v0.6.9引入）

---

## v0.6.9 Highlights / v0.6.9 更新亮点

- **章节依赖图谱**：新增 `build_chapter_deps.py`，自动维护 `chapter-deps.json`，防止伏笔断线
- **Humanize 工作流整合**：`humanize` 能力（对外中文别名：**去AI味**）已接入 chapter-full 报告，支持 light/medium/heavy 三档，默认 medium，输出旁路稿不覆盖原章
- **Packet-First 写作**：chapter packet、summary-first、对象状态摘要、最小输入包
- **风格库模式**：可调用已沉淀的风格参考卡，生成可执行风格约束与提示词模板
