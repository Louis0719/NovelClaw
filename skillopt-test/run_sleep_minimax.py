#!/usr/bin/env python3
"""用MiniMax后端运行真实的SkillOpt-Sleep cycle"""
import os, sys, json

# 设置正确的MiniMax配置
os.environ["MINIMAX_BASE_URL"] = "https://api.minimax.chat/v1"
os.environ["MINIMAX_API_KEY"] = os.environ.get("MINIMAX_API_KEY", "")

from skillopt_sleep.backend import build_backend
from skillopt_sleep.types import TaskRecord, EditRecord
from skillopt_sleep.replay import replay_batch, aggregate_scores
from skillopt_sleep.consolidate import consolidate, select_gate_score

# 创建一个简单的skill
initial_skill = """# OpenClaw Researcher Skill

You are an OpenClaw agent helping with research tasks.

## Rules
- Answer questions accurately and concisely
- Always cite your sources
"""

# 创建测试任务（类似researcher persona）
tasks = [
    TaskRecord(
        id=f"test_{i}",
        project="/test",
        intent=q,
        context_excerpt="",
        attempted_solution="",
        outcome="fail",
        reference_kind="exact",
        reference=a,
        tags=["rule:wrap-answer"],
        source_sessions=[f"sess_{i}"],
    )
    for i, (q, a) in enumerate([
        ("What is the arXiv id for the Attention paper? Answer with just the ID.", "arXiv:1706.03762"),
        ("Give me the arXiv id for BERT.", "arXiv:1810.04805"),
        ("What is the arXiv id for the GAN paper?", "arXiv:1406.2661"),
    ])
]

print("=== Building MiniMax backend ===")
backend = build_backend(
    backend="azure_openai",  # will be overridden
    optimizer_backend="minimax_chat",
    target_backend="minimax_chat",
    optimizer_model="MiniMax-M2.7-highspeed",
    target_model="MiniMax-M2.7-highspeed",
)
print(f"Backend: {backend}")
print(f"Optimizer: {getattr(backend, 'optimizer', backend)}")

print("\n=== Baseline evaluation (no skill) ===")
pairs = replay_batch(backend, tasks, initial_skill, "")
hard, soft = aggregate_scores(pairs)
baseline = select_gate_score(hard, soft, "mixed", 0.5)
print(f"Baseline score: {baseline:.4f} (hard={hard:.2f}, soft={soft:.2f})")

print("\n=== Attempt with skill ===")
for task in tasks[:2]:
    response = backend.attempt(task, initial_skill, "")
    print(f"Task: {task.intent[:50]}...")
    print(f"Response: {response[:100]!r}...")
    h, s, rationale = backend.judge(task, response)
    print(f"  Score: hard={h:.2f}, soft={s:.2f} — {rationale}")
    print()
