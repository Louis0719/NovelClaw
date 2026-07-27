#!/usr/bin/env python3
"""
skill-router validate.py
验证路由系统是否正常工作

用法: python3 validate.py
"""

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path.home() / "openclaw-workspace"
INDEX_FILE = WORKSPACE / "skills/skill-router/scripts/trigger_index.json"
SKILL_ROUTER = WORKSPACE / "skills/skill-router/scripts/route.py"

PASS = "\033[92m✅\033[0m"
FAIL = "\033[91m❌\033[0m"


def check_file(path: Path, label: str) -> bool:
    if path.exists():
        print(f"{PASS} {label} 存在")
        return True
    else:
        print(f"{FAIL} {label} 不存在: {path}")
        return False


def check_index() -> bool:
    if not INDEX_FILE.exists():
        print(f"{FAIL} trigger_index.json 不存在，先运行 reindex.py")
        return False
    try:
        with open(INDEX_FILE) as f:
            idx = json.load(f)
        skills_count = len(idx)
        print(f"{PASS} trigger_index.json 正常 ({skills_count} 个 Skills)")
        # 检查几个关键技能
        required = ["tianming-novel-system", "github", "shuorenhua", "gpt-image2-ppt"]
        for skill in required:
            if skill in idx:
                print(f"  {PASS} {skill} 已索引")
            else:
                print(f"  {FAIL} {skill} 未索引")
        return True
    except Exception as e:
        print(f"{FAIL} trigger_index.json 读取失败: {e}")
        return False


def test_route(message: str, expected: list) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, str(SKILL_ROUTER), message],
            capture_output=True, text=True, timeout=5,
            cwd=str(WORKSPACE)
        )
        data = json.loads(result.stdout)
        matched = data.get("matched", [])
        
        # 检查是否包含所有期望的技能
        ok = all(s in matched for s in expected)
        status = PASS if ok else FAIL
        print(f"{status} \"{message[:30]}...\"")
        print(f"    期望: {expected}")
        print(f"    实际: {matched}")
        return ok
    except Exception as e:
        print(f"{FAIL} \"{message[:30]}...\" -> 错误: {e}")
        return False


def main():
    print("=" * 50)
    print("Skill Router 系统验证")
    print("=" * 50)
    
    all_ok = True
    
    # 文件检查
    print("\n📁 文件检查:")
    all_ok &= check_file(WORKSPACE / "skills/skill-router/SKILL.md", "SKILL.md")
    all_ok &= check_file(SKILL_ROUTER, "route.py")
    all_ok &= check_file(WORKSPACE / "skills/skill-router/scripts/reindex.py", "reindex.py")
    
    # 索引检查
    print("\n📋 索引检查:")
    all_ok &= check_index()
    
    # 路由测试
    print("\n🧪 路由测试:")
    tests = [
        ("写一本玄幻小说", ["tianming-novel-system", "novel-studio"]),
        ("帮我改掉AI味", ["shuorenhua", "avoid-ai-writing"]),
        ("看看GitHub的issues", ["github", "gh-issues"]),
        ("做一份演示PPT", ["gpt-image2-ppt"]),
        ("用天命写章节", ["tianming-novel-system"]),
        ("分析小说文风", ["writing-style", "novel-reader"]),
        ("查一下邮件", ["gog", "himalaya"]),
        ("画一个架构图", ["diagram-maker", "drawio"]),
    ]
    
    for msg, expected in tests:
        all_ok &= test_route(msg, expected)
    
    print("\n" + "=" * 50)
    if all_ok:
        print(f"{PASS} 所有检查通过！Skill Router 系统就绪")
    else:
        print(f"{FAIL} 部分检查失败，请修复后重试")
    print("=" * 50)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
