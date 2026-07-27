#!/usr/bin/env python3
"""
AI 漫剧 Agent - 角色四视图生成脚本
用法: python generate_character_four_views.py "角色名" "角色描述" "输出路径"
"""
import sys
import os
import json
import base64
import time
import requests
from pathlib import Path

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
BASE_URL = "https://api.minimax.chat/v1"

def generate_character_four_views(name: str, description: str, output_path: str):
    """生成角色四视图"""
    
    prompt = f"""Chinese style anime, cel-shaded, neo-chic oriental aesthetic,
    {name}, female character design sheet, character turnaround,
    {description},
    【L1·妆容】基础妆：妆容清雅、淡扫蛾眉、素妆清颜,
    【L2·发型】半扎发、云鬓自然垂落,
    【L3+L4·服饰】古装长裙、丝绸质感、衣服质感清晰,
    【L5·配饰】简约发簪,
    同一画面左至右并排：人像特写+正视图+侧视图+后视图,
    自然站立, 月白纯色背景 #E8EAF5, 均匀柔光,
    四视图一致性, 8K, 超精细"""
    
    print(f"🎬 正在生成角色「{name}」的四视图...")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    # 调用 MiniMax image-01
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "image-01",
        "prompt": prompt,
        "size": "1K",
        "n": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/images/generations",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        print(f"❌ API 错误: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    
    # 获取图片 URL
    image_url = data.get("data", [{}])[0].get("url", "")
    
    if not image_url:
        print("❌ 未获取到图片 URL")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return False
    
    # 下载图片
    img_response = requests.get(image_url)
    if img_response.status_code == 200:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_response.content)
        print(f"✅ 四视图已保存: {output_path}")
        return True
    
    print(f"❌ 下载失败: {img_response.status_code}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python generate_character_four_views.py <角色名> <描述> <输出路径>")
        sys.exit(1)
    
    name = sys.argv[1]
    description = sys.argv[2]
    output_path = sys.argv[3]
    
    success = generate_character_four_views(name, description, output_path)
    sys.exit(0 if success else 1)
