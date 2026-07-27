#!/usr/bin/env python3
"""直接测试MiniMax后端在SkillOpt中的调用"""
import os, sys

# 设置正确的MiniMax配置
os.environ["MINIMAX_BASE_URL"] = "https://api.minimax.chat/v1"
os.environ["MINIMAX_API_KEY"] = os.environ.get("MINIMAX_API_KEY", "")

from skillopt.model import minimax_backend

# 测试1: 简单对话
print("=== Test 1: Simple chat ===")
try:
    result, usage = minimax_backend.chat_target(
        system="You are a helpful assistant.",
        user="What is 2+2? Answer with just the number.",
        max_completion_tokens=20,
        stage="test"
    )
    print(f"Result: {result!r}")
    print(f"Usage: {usage}")
    print("✅ chat_target works!")
except Exception as e:
    print(f"❌ chat_target failed: {e}")

# 测试2: 用SkillOpt训练流程跑searchqa
print("\n=== Test 2: Full skillopt-train (searchqa) ===")
print("需要先下载SearchQA数据集...")

# 先检查是否有数据集
import subprocess
result = subprocess.run(
    ["python3", "-c", 
     "from skillopt.datasets import searchqa; print(searchqa.__file__)"],
    capture_output=True, text=True
)
print(f"searchqa module: {result.stdout.strip()}")
