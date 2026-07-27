#!/usr/bin/env python3
"""
来财AI客服 - 启动脚本
用法: python3 start.py
"""
import subprocess, sys, os

def main():
    agent = os.path.join(os.path.dirname(__file__), "system/agent/agent.py")
    print(f"🚀 启动来财AI客服...")
    print(f"📦 加载系统: {agent}")
    print("-" * 40)
    subprocess.run([sys.executable, agent])

if __name__ == "__main__":
    main()
