#!/bin/bash
# MoneyPrinterTurbo API 调用示例
# API 服务地址：http://127.0.0.1:8080
# 完整 API 文档：http://127.0.0.1:8080/docs

BASE_URL="http://127.0.0.1:8080"

# === 示例1：生成竖屏短视频 ===
echo ">>> 生成竖屏短视频..."
curl -X POST "$BASE_URL/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "金钱的作用",
    "video_aspect": "9:16",
    "voice_name": "zh-CN-XiaoxiaoNeural",
    "voice_rate": 1.0,
    "subtitle_enabled": true,
    "subtitle_position": "bottom",
    "bgm_type": "random",
    "bgm_volume": 0.3
  }'

# === 示例2：生成横屏视频 ===
echo ">>> 生成横屏视频..."
curl -X POST "$BASE_URL/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "为什么要运动",
    "video_aspect": "16:9",
    "voice_name": "zh-CN-YunxiNeural"
  }'

# === 示例3：自定义文案（跳过 LLM 生成）===
echo ">>> 使用自定义文案..."
curl -X POST "$BASE_URL/videos/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "video_subject": "科技改变生活",
    "video_script": "第一段：科技让生活更便捷。\n第二段：人工智能深入各行各业。\n第三段：未来已来。",
    "video_aspect": "9:16",
    "voice_name": "zh-CN-XiaoxiaoNeural"
  }'

# === 示例4：查询任务状态 ===
# 把 TASK_ID 换成实际返回的 task_id
# curl "$BASE_URL/videos/status/TASK_ID"

# === 示例5：下载已完成视频 ===
# curl -O "$BASE_URL/tasks/{task_id}/final-1.mp4"
