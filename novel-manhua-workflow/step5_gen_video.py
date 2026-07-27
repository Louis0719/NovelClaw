"""
step5_gen_video.py
Step 5: 用 MiniMax Hailo 2.3 把场景图转成视频

API 说明 (Hailo 2.3):
- 提交: POST https://api.minimax.chat/v1/video_generation
- 模型: Hailo 2.3 (MiniMax-Hailuo-2.3)
- 返回 SSE 流，每行 data: {"status": "processing|success|failed", "video_url": "..."}
- 旧版轮询已废弃，使用 SSE 流式获取结果
"""
import json
import time
from pathlib import Path
from config import OUTPUT_DIR, MINIMAX_API_KEY


VIDEO_API = "https://api.minimax.chat/v1/video_generation"
VIDEO_QUERY_API = "https://api.minimax.chat/v1/query/video_generation"
VIDEO_METADATA_API = "https://api.minimax.chat/v1/files/retrieve"
VIDEO_MODEL = "MiniMax-Hailuo-2.3"


def generate_video_from_image(image_path: str, prompt: str = "", aspect_ratio: str = "16:9") -> dict:
    """用 MiniMax Hailo 2.3 生成视频（ SSE 流式获取结果）"""
    import base64, urllib.request

    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    if not prompt:
        prompt = "Cinematic anime scene, high quality animation, dynamic camera movement"

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    # 提交任务（使用 Hailo 2.3）
    payload = json.dumps({
        "model": VIDEO_MODEL,
        "prompt": prompt[:500],
        "input": {
            "type": "image_url",
            "url": f"data:image/png;base64,{img_b64}"
        },
        "parameters": {
            "aspect_ratio": aspect_ratio,
        }
    }).encode()

    req = urllib.request.Request(VIDEO_API, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            task_id = result.get("task_id", "")
            if not task_id:
                return {"status": "failed", "error": "no task_id returned"}
    except Exception as e:
        return {"status": "failed", "error": f"submission error: {e}"}

    print(f"  ⏳ task_id={task_id[:15]}... 等待生成（预计1-2分钟）")

    # 轮询获取结果（最多等待 5 分钟，每 10 秒轮询一次）
    import urllib.error, time as time_module
    poll_url = f"{VIDEO_QUERY_API}?task_id={task_id}"
    max_attempts = 30
    poll_interval = 10

    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(poll_url, headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                status = data.get("status", "")
                # status 可能是 "Success", "success", "Processing", "Preparing" 等
                status_lower = status.lower() if isinstance(status, str) else ""
                print(f"  [{attempt+1}/{max_attempts}] 状态: {status}")
                
                if status_lower == "success":
                    file_id = data.get("file_id", "")
                    if not file_id:
                        # 有时候成功但 file_id 为空，再等一下
                        print("  file_id 为空，继续等待...")
                        if attempt < max_attempts - 1:
                            time_module.sleep(poll_interval)
                        continue
                    
                    # 通过 file_id 获取下载链接
                    print(f"  获取下载链接 (file_id={file_id[:15]}...)")
                    metadata_url = f"{VIDEO_METADATA_API}?file_id={file_id}"
                    meta_req = urllib.request.Request(metadata_url, headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"})
                    with urllib.request.urlopen(meta_req, timeout=30) as meta_resp:
                        meta_data = json.loads(meta_resp.read())
                    
                    video_url = meta_data.get("file", {}).get("download_url", "")
                    if video_url:
                        print(f"  ✅ 获取到视频地址")
                        return {"status": "success", "video_url": video_url, "task_id": task_id}
                    else:
                        print("  download_url 为空，继续等待...")
                        if attempt < max_attempts - 1:
                            time_module.sleep(poll_interval)
                        continue
                        
                elif status_lower == "fail" or status_lower == "failed":
                    return {"status": "failed", "error": "video generation failed", "task_id": task_id}
                
                elif status_lower in ("processing", "preparing", "queueing", ""):
                    if attempt < max_attempts - 1:
                        time_module.sleep(poll_interval)
                    continue
                    
                else:
                    # 未知状态，继续轮询
                    if attempt < max_attempts - 1:
                        time_module.sleep(poll_interval)
                    
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            return {"status": "error", "error": f"HTTP {e.code}: {body[:200]}", "task_id": task_id}
        except Exception as e:
            return {"status": "error", "error": f"poll error: {e}", "task_id": task_id}

    return {"status": "timeout", "task_id": task_id}


def download_video(url: str, path: Path) -> bool:
    """下载视频"""
    import urllib.request, urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(path, "wb") as out:
                out.write(resp.read())
        return True
    except urllib.error.HTTPError as e:
        print(f"  ⚠️ 下载失败 HTTP {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"  ⚠️ 下载失败: {e}")
        return False


def run(limit: int = 10) -> Path:
    """执行 Step 5"""
    scene_images_file = OUTPUT_DIR / "scene_images_result.json"

    if not scene_images_file.exists():
        raise FileNotFoundError("请先运行 step4 生成场景图！")

    with open(scene_images_file, encoding="utf-8") as f:
        scene_images = json.load(f)

    # 只处理还没生成视频的场景
    existing_results_file = OUTPUT_DIR / "videos" / "video_result.json"
    already_done = set()
    if existing_results_file.exists():
        with open(existing_results_file, encoding="utf-8") as f:
            existing = json.load(f)
            for r in existing:
                if r.get("status") == "success":
                    already_done.add(r.get("index"))
        print(f"📋 已完成的视频: {already_done}")

    pending = [s for s in scene_images if s.get("status") == "success" and s.get("index") not in already_done][:limit]

    if not pending:
        print("✅ 所有场景视频都已生成完毕")
        return existing_results_file

    out_dir = OUTPUT_DIR / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 加载已有结果
    results = []
    if existing_results_file.exists():
        with open(existing_results_file, encoding="utf-8") as f:
            results = json.load(f)

    print(f"🎥 开始生成 {len(pending)} 个视频片段（预计每段1-2分钟）...")

    for i, scene in enumerate(pending):
        scene_idx = scene.get("index", i+1)
        title = scene.get("title", f"场景{scene_idx}")
        image_path = scene.get("image_path", "")
        prompt = scene.get("prompt", "")

        video_path = out_dir / f"scene_{scene_idx:03d}.mp4"

        print(f"  [{i+1}/{len(pending)}] 生成视频: {title}")

        if not Path(image_path).exists():
            print(f"    ⚠️ 图片不存在: {image_path}")
            continue

        result = generate_video_from_image(image_path, prompt)

        if result.get("status") == "success" and result.get("video_url"):
            video_url = result["video_url"]
            if download_video(video_url, video_path):
                # 去除旧记录
                results = [r for r in results if r.get("index") != scene_idx]
                results.append({
                    "index": scene_idx,
                    "title": title,
                    "video_url": video_url,
                    "video_path": str(video_path),
                    "status": "success",
                })
                print(f"    ✅ 已保存: {video_path}")
            else:
                results = [r for r in results if r.get("index") != scene_idx]
                results.append({
                    "index": scene_idx,
                    "title": title,
                    "video_url": video_url,
                    "status": "failed",
                    "error": "download failed"
                })
        else:
            results = [r for r in results if r.get("index") != scene_idx]
            results.append({
                "index": scene_idx,
                "title": title,
                "status": result.get("status", "unknown"),
                "error": result.get("error", ""),
                "task_id": result.get("task_id", ""),
            })
            print(f"    ❌ 失败: {result.get('error', 'unknown')}")

        # 每完成一个就保存，防止中途中断
        with open(existing_results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in results if r["status"] == "success")
    total = len(scene_images)
    print(f"\n✅ 视频生成完成: {success_count}/{total} 成功（本次新增 {len(pending)} 个）")
    print(f"📁 保存位置: {out_dir}")
    print(f"📋 查看结果: cat {existing_results_file}")

    return existing_results_file
