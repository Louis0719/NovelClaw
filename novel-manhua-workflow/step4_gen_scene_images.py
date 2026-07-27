"""
step4_gen_scene_images.py
Step 4: 基于场景描述 + 角色图生成场景图
"""
import json
import time
from pathlib import Path
from config import OUTPUT_DIR, MINIMAX_API_KEY, VIDEO_ASPECT_RATIO


def build_scene_prompt(scene: dict, characters: list[dict]) -> str:
    """构建场景图的 prompt"""
    scene_chars = []
    scene_text = scene.get("text", "")
    for char in characters:
        name = char.get("name", "")
        if name and name in scene_text:
            scene_chars.append(char)

    char_desc = ""
    if scene_chars:
        char_desc = "\nCharacters present: " + ", ".join([
            f"{c['name']}: {c['visual_description'][:100]}"
            for c in scene_chars[:3]
        ])

    prompt = f"""Scene: {scene.get('title', 'Scene')}

Setting description (from story):
{scene.get('text', '')[:400]}
{char_desc}

Visual requirements:
- Cinematic illustration style, high quality
- Aspect ratio: {VIDEO_ASPECT_RATIO}
- Dynamic composition, rich background details
- Anime/cartoon style for Chinese web novel
- No text, no watermark, no logo"""

    return prompt.strip()


def generate_scene_image(scene: dict, characters: list[dict]) -> tuple:
    """生成单张场景图"""
    import urllib.request

    prompt = build_scene_prompt(scene, characters)

    size_map = {
        "1:1": "1:1",
        "16:9": "16:9",
        "9:16": "9:16",
    }
    image_size = size_map.get(VIDEO_ASPECT_RATIO, "1:1")

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
        return None, prompt


def download_image(url: str, path: Path) -> bool:
    """下载图片"""
    import urllib.request
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"  ⚠️ 下载失败: {e}")
        return False


def run(limit: int = 5) -> Path:
    """执行 Step 4"""
    scenes_file = OUTPUT_DIR / "scenes.json"
    chars_file = OUTPUT_DIR / "characters.json"

    if not scenes_file.exists():
        raise FileNotFoundError("请先运行 step1 提取分镜！")
    if not chars_file.exists():
        raise FileNotFoundError("请先运行 step2 提取角色！")

    with open(scenes_file, encoding="utf-8") as f:
        scenes_data = json.load(f)
    with open(chars_file, encoding="utf-8") as f:
        chars_data = json.load(f)

    scenes = scenes_data.get("scenes", [])[:limit]
    characters = chars_data.get("characters", [])

    out_dir = OUTPUT_DIR / "images" / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    print(f"🎬 开始生成 {len(scenes)} 张场景图...")

    for i, scene in enumerate(scenes):
        idx = scene.get("index", i+1)
        title = scene.get("title", f"场景{i+1}")
        img_path = out_dir / f"scene_{idx:03d}.png"

        print(f"  [{i+1}/{len(scenes)}] 生成场景图: {title}")

        image_url, prompt_used = generate_scene_image(scene, characters)

        if image_url:
            success = download_image(image_url, img_path)
            if success:
                results.append({
                    "index": idx,
                    "title": title,
                    "image_url": image_url,
                    "image_path": str(img_path),
                    "prompt": prompt_used,
                    "status": "success",
                })
                print(f"    ✅ 已保存: {img_path}")
            else:
                results.append({
                    "index": idx,
                    "title": title,
                    "status": "failed",
                    "error": "download failed"
                })
        else:
            results.append({
                "index": idx,
                "title": title,
                "status": "failed",
                "error": "generation failed"
            })

        if i < len(scenes) - 1:
            time.sleep(2)

    result_file = OUTPUT_DIR / "scene_images_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ 场景图完成: {success_count}/{len(scenes)} 成功")
    print(f"📁 保存位置: {out_dir}")

    return result_file
