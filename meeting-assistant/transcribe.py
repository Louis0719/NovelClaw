#!/usr/bin/env python3
"""
meeting-assistant - 企业微信会议助手
==============================
核心转录引擎：从音频文件转写为文字

用法:
  python3 transcribe.py audio.m4a
  python3 transcribe.py audio.m4a --model medium
"""

import sys
import os
import subprocess
import tempfile
import hashlib

# ====== Whisper 配置 ======
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "turbo")  # turbo/base/medium/large
WHISPER_LANG = "zh"  # 中文

def get_audio_duration(path: str) -> float:
    """获取音频时长（秒）"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def convert_to_wav(input_path: str, output_path: str = None) -> str:
    """将各种音频格式转为16kHz单声道WAV（Whisper最佳格式）"""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".wav")

    # 检测格式
    ext = os.path.splitext(input_path)[1].lower()

    # 如果已经是wav且时长<2小时，直接复制
    if ext == ".wav":
        # 转换采样率
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
            output_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"ffmpeg警告: {result.stderr[:200]}", file=sys.stderr)
            # 尝试直接复制
            import shutil
            shutil.copy(input_path, output_path)
    except FileNotFoundError:
        # 没有ffmpeg，直接复制原文件
        import shutil
        shutil.copy(input_path, output_path)
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        import shutil
        shutil.copy(input_path, output_path)

    return output_path

def transcribe(audio_path: str, model: str = None, language: str = None) -> dict:
    """
    使用Whisper转录音频

    Returns:
        dict: {
            "text": "转写文字",
            "chunks": [{"text": "...", "start": 0.0, "end": 5.0}, ...],
            "language": "zh",
            "duration": 120.5
        }
    """
    model = model or WHISPER_MODEL
    language = language or WHISPER_LANG

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    duration = get_audio_duration(audio_path)
    print(f"[转录] 文件: {audio_path}")
    print(f"[转录] 时长: {duration:.1f}秒 | 模型: {model} | 语言: {language}")

    # 转换为Whisper最佳格式
    wav_path = convert_to_wav(audio_path)
    print(f"[转录] 格式转换完成: {wav_path}")

    # 构建Whisper命令
    # whisper 支持: --model, --language, --output_format, --output_dir
    output_dir = tempfile.mkdtemp()
    cmd = [
        "whisper",
        wav_path,
        "--model", model,
        "--language", language,
        "--output_format", "json",
        "--output_dir", output_dir,
    ]

    print(f"[转录] 执行: whisper {' '.join(cmd[1:])}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        raise RuntimeError("未找到whisper命令，请先安装: brew install openai-whisper")
    except subprocess.TimeoutExpired:
        raise RuntimeError("转录超时，请尝试更小的音频文件或更轻量的模型")

    if result.returncode != 0:
        stderr = result.stderr
        # 常见错误处理
        if "No such file" in stderr and "whisper" in stderr:
            raise RuntimeError("whisper命令未找到，请安装: brew install openai-whisper")
        raise RuntimeError(f"Whisper转录失败: {stderr[:500]}")

    # 读取结果文件
    base = os.path.splitext(os.path.basename(wav_path))[0]
    json_path = os.path.join(output_dir, base + ".json")

    if not os.path.exists(json_path):
        # 尝试其他输出格式
        for f in os.listdir(output_dir):
            if f.endswith(".json"):
                json_path = os.path.join(output_dir, f)
                break

    if not os.path.exists(json_path):
        raise RuntimeError(f"Whisper未生成结果文件，stderr: {result.stderr[:300]}")

    import json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 清理临时文件
    try:
        os.unlink(wav_path)
        os.unlink(json_path)
        os.rmdir(output_dir)
    except Exception:
        pass

    # 解析结果
    text = data.get("text", "").strip()
    segments = []
    for seg in data.get("segments", []):
        segments.append({
            "text": seg.get("text", "").strip(),
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0),
        })

    result_text = text if text else "[无法识别音频内容]"
    print(f"[转录] 完成，转写文字长度: {len(result_text)}字")

    return {
        "text": result_text,
        "chunks": segments,
        "language": data.get("language", language),
        "duration": duration,
        "model": model,
    }

def transcribe_text_only(audio_path: str) -> str:
    """仅返回纯文本，简化用法"""
    result = transcribe(audio_path)
    return result["text"]

# ====== CLI 入口 ======
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 transcribe.py <音频文件> [--model turbo|medium]")
        print("示例: python3 transcribe.py meeting.m4a")
        print("       python3 transcribe.py audio.mp3 --model medium")
        sys.exit(1)

    audio_file = sys.argv[1]
    model = "turbo"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    if not os.path.exists(audio_file):
        print(f"错误: 文件不存在: {audio_file}")
        sys.exit(1)

    print("=" * 50)
    print("  🎤 Whisper 会议转录")
    print("=" * 50)

    try:
        result = transcribe(audio_file, model=model)
        print(f"\n📝 转写结果:\n{result['text']}")
        print(f"\n⏱️ 时长: {result['duration']:.1f}秒")
        print(f"🗣️ 语言: {result['language']}")
    except Exception as e:
        print(f"\n❌ 转录失败: {e}")
        sys.exit(1)
