#!/usr/bin/env python3
"""
skill-router route.py
根据用户消息，匹配最相关的 Skills

用法: python3 route.py "用户的完整消息"
"""

import json
import sys
import re
from pathlib import Path

WORKSPACE = Path.home() / "openclaw-workspace"
INDEX_FILE = WORKSPACE / "skills/skill-router/scripts/trigger_index.json"
SKILLS_DIR = WORKSPACE / "skills"


def load_index():
    if not INDEX_FILE.exists():
        return {}
    with open(INDEX_FILE) as f:
        return json.load(f)


def tokenize(text):
    """中英文分词 + 归一化"""
    text_lower = text.lower()
    
    # 中文bigram（相邻字符对）
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text_lower)
    chinese_tokens = [chinese_chars[i]+chinese_chars[i+1] 
                     for i in range(len(chinese_chars)-1)]
    
    # 英文词
    english = re.findall(r'[a-z0-9]{3,}', text_lower)
    
    return set(chinese_tokens + english), text_lower  # 返回原始小写文本供子串匹配


def score_skill(skill_name: str, index_entry: dict, user_tokens: set, text_lower: str) -> float:
    """计算技能匹配得分"""
    keywords = index_entry.get("keywords", [])
    weight = index_entry.get("weight", 1)
    matched = 0
    
    for kw in keywords:
        kw_lower = kw.lower()
        if re.match(r'^[a-z0-9]{3,}$', kw_lower):
            # 英文词：先尝试 token 匹配，失败则做子串匹配（处理中文消息含英文字母的情况）
            if kw_lower in user_tokens:
                matched += 1
            elif kw_lower in text_lower:
                matched += 0.8  # 子串匹配权重稍低
        else:
            # 中文关键词：子串匹配优先
            if kw_lower in text_lower or kw_lower in user_tokens:
                matched += 1
    
    if not keywords:
        return 0
    return (matched / len(keywords)) * weight


def route(message: str) -> dict:
    """主路由函数"""
    index = load_index()
    user_tokens, text_lower = tokenize(message)
    
    scores = {}
    for skill_name, entry in index.items():
        score = score_skill(skill_name, entry, user_tokens, text_lower)
        if score > 0:
            scores[skill_name] = score
    
    if not scores:
        return {"matched": [], "reason": "no match", "scores": {}}
    
    # 按权重降序排列
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    
    # 取权重 >= 最高权重 30% 的技能
    top_score = ranked[0][1]
    threshold = top_score * 0.3
    matched = [name for name, score in ranked if score >= threshold]
    
    return {
        "matched": matched,
        "reason": f"matched {len(matched)} skill(s)",
        "scores": dict(ranked[:5]),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"matched": [], "reason": "no input"}))
        sys.exit(0)
    
    message = " ".join(sys.argv[1:])
    result = route(message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
