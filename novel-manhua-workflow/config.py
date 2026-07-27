"""
novel-manhua-workflow config.py
配置管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WORKSPACE = Path.home() / "openclaw-workspace" / "novel-manhua-workflow"
OUTPUT_DIR = WORKSPACE / "output"

# MiniMax API
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID", "")

# MiniMax API endpoints
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
MINIMAX_T2A_URL = "https://api.minimax.chat/v1/t2a_v2"
MINIMAX_IMAGE_URL = "https://api.minimax.chat/v1/image_generation"
MINIMAX_VIDEO_URL = "https://api.minimax.chat/v1/hailo_v2"

# 视频参数
VIDEO_ASPECT_RATIO = "16:9"  # 可选: 16:9 / 9:16 / 1:1
VIDEO_DURATION = 6  # 秒，6-10之间
VIDEO_NUM_FRAMES = 81  # MiniMax 标准

# 分镜参数
SCENE_MAX_CHARS = 2000  # 单场景最大字数

# 角色数量上限
MAX_CHARACTERS = 6

def ensure_dirs():
    """确保目录存在"""
    for d in [
        OUTPUT_DIR,
        OUTPUT_DIR / "images" / "characters",
        OUTPUT_DIR / "images" / "scenes",
        OUTPUT_DIR / "videos",
    ]:
        d.mkdir(parents=True, exist_ok=True)
