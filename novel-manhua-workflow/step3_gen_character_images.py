"""
step3_gen_character_images.py
Step 3: 生成角色立绘
"""
import json
import time
from pathlib import Path
from config import OUTPUT_DIR, MINIMAX_API_KEY, VIDEO_ASPECT_RATIO


def generate_character_image(character: dict, index: int) -> tuple:
    """用 MiniMax image-01 生成角色立绘"""
    import urllib.request
    
    # 映射视频比例为图片尺寸
    size_map = {
        "1:1": "1:1",
        "16:9": "16:9",
        "9:16": "9:16",
    }
    image_size = size_map.get(VIDEO_ASPECT_RATIO, "1:1")
    
    prompt = f"""{character.get('visual_description', '')}

Style requirements:
- Portrait style, centered character
- Clear face features, expressive eyes
- High quality illustration style suitable for AI video generation
- Aspect ratio: {VIDEO_ASPECT_RATIO}
- No text, no watermark, no logo
- Anime/cartoon style for Chinese web novel adaptation"""

    try:
        url = "https://api.minimax.chat/v1/image_generation"
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = json.dumps({
            "model": "image-01",
            "prompt": prompt,
            "image_size": image_size,
            "number": 1,
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            image_url = result["data"]["image_urls"][0]
            return image_url, prompt
    except Exception as e:
        print(f"  ⚠️ 生成失败: {e}")
        return None, None


def download_and_save(url: str, path: Path):
    """下载图片并保存"""
    import urllib.request
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"  ⚠️ 下载失败: {e}")
        return False


def run() -> Path:
    """执行 Step 3"""
    chars_file = OUTPUT_DIR / "characters.json"
    if not chars_file.exists():
        raise FileNotFoundError("请先运行 step2 提取角色！")
    
    with open(chars_file, encoding="utf-8") as f:
        data = json.load(f)
    characters = data.get("characters", [])
    
    out_dir = OUTPUT_DIR / "images" / "characters"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    print(f"🎨 开始生成 {len(characters)} 个角色立绘...")
    
    for i, char in enumerate(characters):
        name = char.get("name", f"character_{i+1}")
        safe_name = name.replace("/", "_").replace("\\", "_")
        img_path = out_dir / f"{safe_name}.png"
        
        print(f"  [{i+1}/{len(characters)}] 生成角色: {name}")
        
        image_url, prompt_used = generate_character_image(char, i)
        
        if image_url:
            success = download_and_save(image_url, img_path)
            if success:
                results.append({
                    "name": name,
                    "image_url": image_url,
                    "image_path": str(img_path),
                    "prompt": prompt_used,
                    "status": "success",
                })
                print(f"    ✅ 已保存: {img_path}")
            else:
                results.append({
                    "name": name,
                    "status": "failed",
                    "error": "download failed"
                })
        else:
            results.append({
                "name": name,
                "status": "failed",
                "error": "generation failed"
            })
        
        # 避免限流
        if i < len(characters) - 1:
            time.sleep(2)
    
    # 保存结果
    result_file = OUTPUT_DIR / "character_images_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ 角色立绘完成: {success_count}/{len(characters)} 成功")
    print(f"📁 保存位置: {out_dir}")
    
    return result_file
