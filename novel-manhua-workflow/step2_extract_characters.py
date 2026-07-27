"""
step2_extract_characters.py
Step 2: 用 AI 从场景中提取角色，并生成角色描述
"""
import json
import re
from pathlib import Path
from openai import OpenAI
from config import OUTPUT_DIR, MINIMAX_API_KEY, MINIMAX_BASE_URL, MAX_CHARACTERS


def extract_characters_from_scenes(scenes: list[dict]) -> list[dict]:
    """用 MiniMax LLM 提取角色"""
    client = OpenAI(
        api_key=MINIMAX_API_KEY,
        base_url=MINIMAX_BASE_URL,
    )
    
    # 合并前3个场景作为样本
    sample = "\n\n".join([
        f"【场景{s.get('index',i+1)}】{s.get('text','')[:500]}"
        for i, s in enumerate(scenes[:3])
    ])
    
    prompt = f"""从以下小说场景提取角色，要求返回简短JSON（最多4个角色，每个描述不超过80字）：
{{"characters":[{{"name":"名字","role":"角色类型","visual_description":"外貌描述50字"}}]}}
场景：
{sample}
只返回JSON，不要解释。
"""

    print("🤖 AI 正在分析角色...")
    response = client.chat.completions.create(
        model="MiniMax-M2.5-highspeed",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.7,
    )
    
    content = response.choices[0].message.content.strip()
    
    # 尝试解析 JSON
    try:
        # 去掉 markdown 代码块
        if content.startswith("```"):
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{") or part.startswith("["):
                    content = part
                    break
        # 去掉 LLM 思考过程
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        data = json.loads(content)
        return data.get("characters", [])
    except json.JSONDecodeError:
        print(f"⚠️ JSON 解析失败，原始返回：{content[:200]}")
        return []


def run() -> Path:
    """执行 Step 2"""
    scenes_file = OUTPUT_DIR / "scenes.json"
    if not scenes_file.exists():
        raise FileNotFoundError("请先运行 step1 提取分镜！")
    
    with open(scenes_file, encoding="utf-8") as f:
        data = json.load(f)
    scenes = data["scenes"]
    
    print(f"📋 从 {len(scenes)} 个场景中提取角色...")
    characters = extract_characters_from_scenes(scenes)
    
    print(f"✅ 提取了 {len(characters)} 个角色:")
    for c in characters:
        print(f"  👤 {c.get('name', '?')} ({c.get('role', '')})")
    
    out_file = OUTPUT_DIR / "characters.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(characters),
            "characters": characters,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 角色数据已保存: {out_file}")
    return out_file
