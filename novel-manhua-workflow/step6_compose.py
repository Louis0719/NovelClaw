"""
step6_compose.py
Step 6: 用 ffmpeg 把视频片段合成为最终成品
"""
import json
from pathlib import Path
from config import OUTPUT_DIR, VIDEO_ASPECT_RATIO


def compose_videos(video_results_file: Path, output_name: str = "final.mp4") -> Path:
    """用 ffmpeg 合成视频"""
    import subprocess
    
    with open(video_results_file, encoding="utf-8") as f:
        results = json.load(f)
    
    # 只取成功的
    videos = [r for r in results if r.get("status") == "success"]
    
    if not videos:
        raise ValueError("没有可用的视频片段！")
    
    print(f"🎬 合成 {len(videos)} 个视频片段...")
    
    # 创建临时文件列表
    list_file = OUTPUT_DIR / "videos" / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for v in videos:
            path = v.get("video_path", "")
            if path and Path(path).exists():
                # ffmpeg concat 需要绝对路径
                abs_path = str(Path(path).resolve())
                f.write(f"file '{abs_path}'\n")
    
    # 确定输出路径
    out_path = OUTPUT_DIR / output_name
    
    # 确定 scale filter（根据比例）
    if VIDEO_ASPECT_RATIO == "9:16":
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    elif VIDEO_ASPECT_RATIO == "1:1":
        scale_filter = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
    else:
        scale_filter = "scale=1920:1080:force_original_aspect_ratio=decrease"
    
    # 执行 ffmpeg concat
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        str(out_path),
    ]
    
    print(f"🔧 执行: ffmpeg {' '.join(cmd[:8])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"⚠️ ffmpeg 警告: {result.stderr[:200]}")
        # 尝试不用 scale filter
        cmd_simple = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c", "copy", str(out_path),
        ]
        result2 = subprocess.run(cmd_simple, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"❌ 合成失败: {result2.stderr[:300]}")
            raise RuntimeError(f"ffmpeg 合成失败: {result2.stderr}")
    
    size = out_path.stat().st_size / 1024 / 1024
    print(f"✅ 合成完成！输出: {out_path} ({size:.1f} MB)")
    
    # 清理临时文件
    try:
        list_file.unlink()
    except:
        pass
    
    return out_path


def run(output_name: str = "final.mp4") -> Path:
    """执行 Step 6"""
    video_results_file = OUTPUT_DIR / "video_result.json"
    
    if not video_results_file.exists():
        raise FileNotFoundError("请先运行 step5 生成视频！")
    
    out_path = compose_videos(video_results_file, output_name)
    
    # 打印总结
    print("\n" + "="*50)
    print("🎉 AI 漫剧制作完成！")
    print("="*50)
    print(f"📁 成品: {out_path}")
    print(f"📂 中间文件: {OUTPUT_DIR}")
    print(f"📐 比例: {VIDEO_ASPECT_RATIO}")
    print("="*50)
    
    return out_path
