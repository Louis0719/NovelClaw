"""Smoke tests — 验证 .gitignore 白名单生效"""
import pytest


def test_pytest_works():
    """基本测试，确保 CI 框架跑得通"""
    assert 1 + 1 == 2


def test_apps_exist():
    """三个 apps 都应在"""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    for app in ["auth-portal", "multiagent", "novelclaw"]:
        assert (root / "apps" / app).is_dir(), f"missing apps/{app}/"


def test_novelclaw_has_all_agents():
    """novelclaw 应该有 9 个 agents"""
    from pathlib import Path
    agents_dir = Path(__file__).resolve().parent.parent / "apps" / "novelclaw" / "agents"
    expected = {
        "base_agent.py", "character_agent.py", "evaluator_agent.py",
        "idea_copilot_agent.py", "judge_agent.py", "plot_agent.py",
        "retrieval_agent.py", "world_agent.py", "writer_agent.py",
    }
    found = {p.name for p in agents_dir.glob("*.py")}
    missing = expected - found
    assert not missing, f"missing agents: {sorted(missing)}"
