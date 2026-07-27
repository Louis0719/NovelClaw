#!/usr/bin/env python3
"""
init_novel_project.py

Initialize a layered, packet-first novel project skeleton.

The scaffold is aligned with the project-governance and packet-first
layout validated in the fanchenlu project:
- entrypoint layering (README / docs/project-notes / nav)
- creative flow vs brainstorm flow separation
- settings split into core / world / subsettings
- .novel-studio as structured workflow kernel
"""

from pathlib import Path
import json
import sys
from datetime import datetime


ROOT_README = """# {project}\n\n这是一个长期维护的小说项目仓库。\n\n## 顶层分工\n- `chapters/`：正文创作流\n- `brainstorm/`：发散流\n- `settings/`：设定主区\n- `workflow/`：推进管理\n- `nav/`：快速摘要入口\n- `.novel-studio/`：结构化工作内核\n\n## 推荐查看顺序\n1. `README.md`\n2. `docs/project-notes.md`\n3. `nav/`\n"""

DOCS_PROJECT_NOTES = """# 项目工作入口\n\n## 当前状态\n- 当前正文状态：\n- 当前最优先任务：\n- 当前母设定收束方向：\n\n## 从这里往哪走\n\n### 要继续写正文\n1. `workflow/chapter-progress.md`\n2. `chapters/`\n3. 必要时回查 `settings/`\n\n### 要修设定\n1. `settings/core/`\n2. `settings/world/`\n3. `settings/subsettings/`\n4. `workflow/`\n\n### 要快速回忆摘要\n1. `nav/outline.md`\n2. `nav/characters.md`\n3. `nav/timeline.md`\n4. `nav/foreshadowing.md`\n"""

DOCS_README = """# docs\n\n这里放项目说明、工作入口、发布说明、命名规范等文档。\n\n- `project-notes.md`：当前工作入口\n"""

ANALYSIS_README = """# analysis\n\n这里放读者视角分析、章节复盘、阶段性诊断与发行版综合报告。\n"""

BRAINSTORM_README = """# brainstorm\n\n这里放结构试探、线索讨论、标题试探、暂不进入正文流的发散材料。\n"""

CHAPTERS_README = """# chapters\n\n这里放实际进入正文流的文本。\n\n- `published/`：已发布正式版\n- `candidates/`：待发布候选稿\n- `early-drafts/`：早期草稿\n- `drafts/`：普通写作稿\n- `revisions/`：修订稿 / 重写稿 / 过渡版\n- `clips/`：章节相关的局部片段 / Clip 资产\n- `retired/`：退出创作流的旧稿 / 废稿 / 历史留档，默认不再参与任何创作判断\n"""

NAV_README = """# nav\n\n这是项目的简版导航区，只做快速摘要入口，不代替正式设定。\n\n- `characters.md`：人物摘要入口\n- `outline.md`：大纲摘要入口\n- `timeline.md`：时间线摘要入口\n- `foreshadowing.md`：伏笔摘要入口\n- `state_tracking.md`：状态文件跳转入口\n"""

NAV_CHARACTERS = """# 人物导航\n\n> 正式人物资料请查看 `settings/subsettings/characters/`\n"""

NAV_OUTLINE = """# 大纲导航\n\n> 长线大纲与母设定请优先查看 `settings/core/` 与 `workflow/`\n"""

NAV_TIMELINE = """# 时间线导航\n\n> 正式时间线请查看 `settings/subsettings/timeline/`\n"""

NAV_FORESHADOWING = """# 伏笔导航\n\n> 正式伏笔管理请查看 `settings/subsettings/foreshadowing/`\n"""

NAV_STATE = """# 状态跟踪\n\n> 详细状态请查看：\n> - `.novel-studio/state.json`\n> - `.novel-studio/chapter-meta.json`\n> - `workflow/chapter-progress.md`\n"""

SETTINGS_README = """# 设定区说明\n\n`settings/` 是项目的设定主区。\n\n- `core/`：总设定 / 上位真相 / 长线母文件\n- `world/`：世界规则 / 写法边界\n- `subsettings/`：人物、关系、时间、伏笔、空间、场景、事件、物件等对象层资料\n"""

SUBSETTINGS_README = """# 子设定区说明\n\n`subsettings/` 用于放可扩展的对象层资料。\n\n推荐对象类型：\n- `characters/`\n- `relationships/`\n- `timeline/`\n- `foreshadowing/`\n- `spaces/`\n- `scenes/`\n- `events/`\n- `items/`\n\n一句话原则：当前稳定状态与变化记录尽量分开。\n"""

CHARACTERS_README = """# characters\n\n这里放人物卡、人物变化记录、人物模板。\n"""

RELATIONSHIPS_README = """# relationships\n\n这里放角色关系线、关系变化与张力说明。\n"""

TIMELINE_README = """# timeline\n\n这里放时间锚点、章节前后顺序与关键因果节点。\n"""

FORESHADOWING_README = """# foreshadowing\n\n这里放伏笔卡、回收计划与伏笔状态管理。\n"""

SPACES_README = """# spaces\n\n这里放固定空间卡与空间变化记录。\n"""

SCENES_README = """# scenes\n\n这里放场景卡与场景变化记录。\n"""

EVENTS_README = """# events\n\n事件卡目录。\n\n适合记录：\n- 事件节点\n- 事件影响\n- 事件后续牵连\n"""

ITEMS_README = """# items\n\n这里放关键物件卡与物件变化记录。\n\n适合记录：\n- 会反复出现的重要物件\n- 承载信息或法意的关键物件\n- 需要跨章节追踪状态变化的物件\n"""

ITEMS_CHANGES_README = """# 物品变化管理说明\n\n`changes/` 用于记录关键物件在章节推进中的变化过程。\n"""

PROJECT_STYLE_CARD = """# 项目风格卡\n\n## 风格总纲\n- \n\n## 叙事要求\n- \n\n## 对话要求\n- \n\n## 节奏要求\n- \n\n## 禁止倾向\n- \n"""

WORKFLOW_README = """# workflow\n\n这里放写作推进、章节进度、近章规划与流程说明。\n"""

CHAPTER_PROGRESS = """# 章节进度记录\n\n## 当前章节状态\n- ch_001：\n\n## 当前最优先任务\n- \n\n## 联动维护规则\n1. 更新正文或草稿\n2. 更新伏笔 / 时间 / 对象层资料\n3. 更新本文件\n4. 如涉及长线调整，再回写 `settings/core/` / `settings/world/`\n"""

OUTLINE_NEXT_CHAPTERS = """# 近章规划\n\n## 当前近章目标\n- \n\n## 承接点\n- \n\n## 近期风险\n- \n"""

NOVEL_STUDIO_README = """# .novel-studio

这是项目的结构化工作内核，存放：
- Model 配置已全局化，不再在项目内保存；使用 `ns_model_config.py global set` 管理
- `state.json`：小说项目状态
- `chapter-meta.json`：章节元数据
- chapter summary
- chapter packet
- active indexes
- workflow logs
- clip indexes / Clip 资产索引
"""

# CONFIG_TEMPLATE removed — model config is now global. Projects no longer get config.json with directApi.

ACTIVE_INDEX_PLACEHOLDER = """# {title}

- 暂无
"""

STATE_TEMPLATE = {
    "project": "",
    "volume": "",
    "version": "0.1.0",
    "last_updated": "",
    "status": "active",
    "writing_mode": "packet-first",
    "summary": {
        "total_chapters_planned": 0,
        "chapters_published": 0,
        "chapters_candidate": 0,
        "chapters_draft": 0,
        "chapters_reference_only": 0,
    },
    "current_phase": "",
    "main_strand": {
        "quest": "",
        "fire": "",
        "constellation": "",
    },
    "active_conflicts": [],
    "key_open_threads": [],
    "strand_balance": {
        "quest_last推进": "",
        "fire_last推进": "",
        "constellation_last推进": "",
    },
}

CHAPTER_META_TEMPLATE = {
    "chapters": []
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: init_novel_project.py <project-dir>")
        return 1

    root = Path(sys.argv[1]).expanduser().resolve()
    today = datetime.now().strftime("%Y-%m-%d")

    dirs = [
        root / "analysis",
        root / "brainstorm",
        root / "chapters" / "published",
        root / "chapters" / "candidates",
        root / "chapters" / "early-drafts",
        root / "chapters" / "drafts",
        root / "chapters" / "revisions",
        root / "chapters" / "clips",
        root / "chapters" / "retired",
        root / "chapters" / "retired" / "clips",
        root / "docs",
        root / "nav",
        root / "settings" / "core",
        root / "settings" / "world",
        root / "settings" / "subsettings" / "characters" / "changes",
        root / "settings" / "subsettings" / "characters" / "templates",
        root / "settings" / "subsettings" / "relationships",
        root / "settings" / "subsettings" / "timeline" / "templates",
        root / "settings" / "subsettings" / "foreshadowing" / "cards",
        root / "settings" / "subsettings" / "foreshadowing" / "templates",
        root / "settings" / "subsettings" / "spaces" / "cards",
        root / "settings" / "subsettings" / "spaces" / "changes",
        root / "settings" / "subsettings" / "spaces" / "templates",
        root / "settings" / "subsettings" / "scenes" / "cards",
        root / "settings" / "subsettings" / "scenes" / "changes",
        root / "settings" / "subsettings" / "scenes" / "templates",
        root / "settings" / "subsettings" / "events" / "templates",
        root / "settings" / "subsettings" / "items" / "cards",
        root / "settings" / "subsettings" / "items" / "changes",
        root / "settings" / "subsettings" / "items" / "templates",
        root / "workflow",
        root / ".novel-studio" / "summaries",
        root / ".novel-studio" / "packets",
        root / ".novel-studio" / "indexes",
        root / ".novel-studio" / "logs",
    ]

    for path in dirs:
        ensure_dir(path)

    ensure_file(root / "README.md", ROOT_README.format(project=root.name))
    ensure_file(root / "analysis" / "README.md", ANALYSIS_README)
    ensure_file(root / "brainstorm" / "README.md", BRAINSTORM_README)
    ensure_file(root / "chapters" / "README.md", CHAPTERS_README)
    ensure_file(root / "docs" / "README.md", DOCS_README)
    ensure_file(root / "docs" / "project-notes.md", DOCS_PROJECT_NOTES)
    ensure_file(root / "nav" / "README.md", NAV_README)
    ensure_file(root / "nav" / "characters.md", NAV_CHARACTERS)
    ensure_file(root / "nav" / "outline.md", NAV_OUTLINE)
    ensure_file(root / "nav" / "timeline.md", NAV_TIMELINE)
    ensure_file(root / "nav" / "foreshadowing.md", NAV_FORESHADOWING)
    ensure_file(root / "nav" / "state_tracking.md", NAV_STATE)
    ensure_file(root / "settings" / "README.md", SETTINGS_README)
    ensure_file(root / "settings" / "subsettings" / "README.md", SUBSETTINGS_README)
    ensure_file(root / "settings" / "subsettings" / "project-style-card.md", PROJECT_STYLE_CARD)
    ensure_file(root / "settings" / "subsettings" / "characters" / "README.md", CHARACTERS_README)
    ensure_file(root / "settings" / "subsettings" / "relationships" / "README.md", RELATIONSHIPS_README)
    ensure_file(root / "settings" / "subsettings" / "timeline" / "README.md", TIMELINE_README)
    ensure_file(root / "settings" / "subsettings" / "foreshadowing" / "README.md", FORESHADOWING_README)
    ensure_file(root / "settings" / "subsettings" / "spaces" / "README.md", SPACES_README)
    ensure_file(root / "settings" / "subsettings" / "scenes" / "README.md", SCENES_README)
    ensure_file(root / "settings" / "subsettings" / "events" / "README.md", EVENTS_README)
    ensure_file(root / "settings" / "subsettings" / "items" / "README.md", ITEMS_README)
    ensure_file(root / "settings" / "subsettings" / "items" / "changes" / "README.md", ITEMS_CHANGES_README)
    ensure_file(root / "workflow" / "README.md", WORKFLOW_README)
    ensure_file(root / "workflow" / "chapter-progress.md", CHAPTER_PROGRESS)
    ensure_file(root / "workflow" / "outline-next-chapters.md", OUTLINE_NEXT_CHAPTERS)
    ensure_file(root / ".novel-studio" / "README.md", NOVEL_STUDIO_README)
    ensure_file(root / ".novel-studio" / "indexes" / "active-characters.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前活跃人物"))
    ensure_file(root / ".novel-studio" / "indexes" / "active-events.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前活跃事件"))
    ensure_file(root / ".novel-studio" / "indexes" / "active-spaces.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前活跃空间"))
    ensure_file(root / ".novel-studio" / "indexes" / "active-scenes.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前活跃场景"))
    ensure_file(root / ".novel-studio" / "indexes" / "active-clips.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前活跃片段 / Clips"))
    ensure_file(root / ".novel-studio" / "indexes" / "pending-foreshadowing.md", ACTIVE_INDEX_PLACEHOLDER.format(title="当前待回收伏笔"))

    state = dict(STATE_TEMPLATE)
    state["project"] = root.name
    state["last_updated"] = today
    # config.json no longer created — model config is global (ns_model_config.py global set)
    ensure_json(root / ".novel-studio" / "state.json", state)
    ensure_json(root / ".novel-studio" / "chapter-meta.json", CHAPTER_META_TEMPLATE)

    print(f"initialized layered packet-first novel project skeleton at: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
