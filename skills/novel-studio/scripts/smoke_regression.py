#!/usr/bin/env python3
"""
smoke_regression.py

Create a temporary layered project, run the main scaffold/governance/chapter-full
workflow chain, and assert that the expected files are produced.

This is a lightweight regression guard for novel-studio's current standard:
- init scaffold
- governance audit / workflow doctor
- startup packet generation
- chapter-full minimal output set
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(*args: str, cwd: Path | None = None) -> None:
    cmd = [sys.executable, *args]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def assert_exists(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"expected path missing: {path}")


def seed_minimal_content(project: Path) -> None:
    # Make style extraction slightly more realistic by seeding one published chapter.
    published = project / "chapters" / "published" / "ch_001-published.md"
    published.write_text(
        "# ch_001\n\n"
        "雨夜里，旧店的灯忽然亮了。\n\n"
        "她站在门外，没有立刻进来。\n\n"
        "“你这里，还开门吗？”\n",
        encoding="utf-8",
    )

    clip = project / "chapters" / "clips" / "old-lamp-memory.md"
    clip.write_text(
        "---\n"
        "type: clip\n"
        "title: 旧灯记忆片段\n"
        "chapter: ch_002\n"
        "status: active\n"
        "created_at: 2026-04-23 00:00:00 +0800\n"
        "updated_at: 2026-04-23 00:00:00 +0800\n"
        "tags: [\"memory\", \"flashback\"]\n"
        "merged_into:\n"
        "---\n\n"
        "她想起旧灯第一次亮起的那个晚上。\n",
        encoding="utf-8",
    )

    state = project / ".novel-studio" / "state.json"
    state.write_text(
        json.dumps(
            {
                "project": project.name,
                "volume": "",
                "version": "0.1.0",
                "last_updated": "2026-04-23",
                "status": "active",
                "writing_mode": "packet-first",
                "summary": {
                    "total_chapters_planned": 0,
                    "chapters_published": 1,
                    "chapters_candidate": 0,
                    "chapters_draft": 0,
                    "chapters_reference_only": 0,
                },
                "current_phase": "ch_001 已有发布章，等待后续章节启动",
                "main_strand": {"quest": "", "fire": "", "constellation": ""},
                "active_conflicts": [],
                "key_open_threads": [],
                "strand_balance": {"quest_last推进": "ch_001", "fire_last推进": "", "constellation_last推进": ""},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    meta = project / ".novel-studio" / "chapter-meta.json"
    meta.write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "id": "ch_001",
                        "title": "旧店亮灯",
                        "status": "published",
                        "phase": "定稿",
                        "word_count": None,
                        "published_date": None,
                        "summary": "雨夜里旧店亮灯，有人来敲门。",
                        "key_events": ["旧店亮灯", "门外来人"],
                        "hasPacket": False,
                        "hasSummary": False,
                        "cardsUpdated": False,
                        "timeAnchor": "雨夜",
                        "clipStats": {
                            "total": 0,
                            "active": 0,
                            "merged": 0,
                            "archived": 0,
                            "discarded": 0
                        },
                        "strand": {"quest": 1, "fire": 0, "constellation": 0},
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Seed one object card so object summary / index refresh have something to see.
    character = project / "settings" / "subsettings" / "characters" / "shenji-character.md"
    character.write_text(
        "# 沈寂\n\n"
        "- 当前状态：旧店守着人，嘴硬，警惕高。\n",
        encoding="utf-8",
    )

    event = project / "settings" / "subsettings" / "events" / "old-shop-lights-on.md"
    event.write_text(
        "# 旧店灯自亮\n\n"
        "- 当前状态：已发生，原因未明。\n",
        encoding="utf-8",
    )

    foreshadow = project / "settings" / "subsettings" / "foreshadowing" / "foreshadowing-management.md"
    foreshadow.write_text(
        "# 伏笔管理\n\n"
        "- 旧店为什么会自己亮灯\n"
        "- 她为什么认识这间店\n",
        encoding="utf-8",
    )


def customize_packet(project: Path, chapter_id: str) -> None:
    packet = project / ".novel-studio" / "packets" / f"{chapter_id}-packet.md"
    text = packet.read_text(encoding="utf-8")
    text = text.replace("### 人物\n- ", "### 人物\n- shenji")
    text = text.replace("### 事件\n- ", "### 事件\n- old-shop-lights-on")
    text = text.replace("### 空间\n- ", "### 空间\n- old-shop")
    text = text.replace("### 场景\n- ", "### 场景\n- rain-night-entry")
    packet.write_text(text, encoding="utf-8")

    summary = project / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md"
    if not summary.exists():
        summary.write_text(
            f"# {chapter_id} 摘要\n\n"
            "## 一、本章发生了什么\n- 雨夜里，旧店重新亮灯。\n\n"
            "## 二、人物停在哪\n- shenji 仍守在旧店。\n\n"
            "## 三、事件推进到哪\n- old-shop-lights-on 已被确认发生。\n\n"
            "## 四、空间 / 场景状态变化\n- 旧店重新进入可用状态。\n\n"
            "## 五、时间锚点\n- 雨夜。\n\n"
            "## 六、下一章承接点\n- 门外来人。\n",
            encoding="utf-8",
        )


def main() -> int:
    chapter_id = "ch_002"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        project = tmp_path / "fixture-novel"

        run(str(SCRIPTS / "init_novel_project.py"), str(project))
        seed_minimal_content(project)

        run(str(SCRIPTS / "governance_audit.py"), str(project))
        run(str(SCRIPTS / "workflow_runner.py"), str(project), chapter_id, "doctor")
        run(str(SCRIPTS / "chapter_startup.py"), str(project), chapter_id)
        customize_packet(project, chapter_id)
        run(str(SCRIPTS / "workflow_runner.py"), str(project), chapter_id, "chapter-full", project.name)
        run(str(SCRIPTS / "workflow_runner.py"), str(project), chapter_id, "overview")
        run(str(SCRIPTS / "workflow_runner.py"), str(project), chapter_id, "clip-stats-sync")

        expected = [
            project / "README.md",
            project / "docs" / "project-notes.md",
            project / ".novel-studio" / "state.json",
            project / ".novel-studio" / "chapter-meta.json",
            project / ".novel-studio" / "packets" / f"{chapter_id}-packet.md",
            project / ".novel-studio" / "packets" / f"{chapter_id}-style-overlay.md",
            project / ".novel-studio" / "summaries" / f"{chapter_id}-summary.md",
            project / ".novel-studio" / "summaries" / f"{chapter_id}-objects.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-startup-checklist.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-input-pack.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-model-min.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-model-std.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-input-pack-review.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-chapter-full-report-v1.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-chapter-full-report-v1.json",
            project / ".novel-studio" / "logs" / f"{chapter_id}-chapter-overview.md",
            project / ".novel-studio" / "logs" / f"{chapter_id}-chapter-overview.json",
            project / ".novel-studio" / "indexes" / "active-characters.md",
            project / ".novel-studio" / "indexes" / "active-scenes.md",
            project / ".novel-studio" / "indexes" / "active-clips.md",
            project / "settings" / "subsettings" / "project-style-card.md",
            project / "chapters" / "retired",
        ]

        for path in expected:
            assert_exists(path)

        meta = json.loads((project / ".novel-studio" / "chapter-meta.json").read_text(encoding="utf-8"))
        if not meta.get("chapters"):
            raise AssertionError("chapter-meta should have at least one chapter entry after clip stats sync")
        first = next((x for x in meta["chapters"] if x.get("id") == chapter_id), None)
        if not first:
            raise AssertionError(f"chapter-meta missing entry for {chapter_id}")
        if "clipStats" not in first:
            raise AssertionError(f"chapter-meta entry for {chapter_id} missing clipStats")

        print("\nSmoke regression passed.")
        print(f"Fixture project path (temporary): {project}")
        print("Validated chain: init -> governance_audit -> doctor -> chapter_startup -> chapter-full")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
