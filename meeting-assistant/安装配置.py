#!/usr/bin/env python3
"""
会议助手 - 一键安装配置脚本
自动检查依赖、配置环境变量、提供使用指南
"""

import os, sys, subprocess, urllib.request, urllib.error, json

def step(msg):
    print(f"\n👉 {msg}")

def ok(msg):
    print(f"  ✅ {msg}")

def warn(msg):
    print(f"  ⚠️ {msg}")

def error(msg):
    print(f"  ❌ {msg}")

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "超时"
    except Exception as e:
        return False, "", str(e)

def check_whisper():
    step("检查 Whisper（本地语音转写）")
    found, out, _ = run("which whisper")
    if found:
        ok("Whisper 已安装")
        _, ver, _ = run("whisper --help 2>&1 | head -1")
        ok(f"版本: {ver}")
        return True
    else:
        warn("Whisper 未安装")
        print("  安装命令: brew install openai-whisper")
        print("  Mac M系列芯片推荐安装 large 模型:")
        print("  whisper --help  # 首次会自动下载模型")
        return False

def check_ffmpeg():
    step("检查 ffmpeg（音频格式转换）")
    ok_flag, out, _ = run("which ffmpeg")
    if ok_flag:
        ok("ffmpeg 已安装")
        return True
    else:
        warn("ffmpeg 未安装（会影响部分音频格式转写）")
        print("  安装命令: brew install ffmpeg")
        return False

def check_minimax_key():
    step("检查 MiniMax API Key")
    key = os.environ.get("MINIMAX_API_KEY", "")
    if key:
        ok(f"已配置 (前8位: {key[:8]}...)")
        # 验证key有效性
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://api.minimax.chat/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                ok("Key 验证通过，可以正常调用")
                return True
        except urllib.error.HTTPError:
            warn("Key 存在但验证失败，请检查是否过期")
            return False
        except Exception as e:
            warn(f"Key 存在但无法验证: {e}")
            return False
    else:
        warn("未配置 MINIMAX_API_KEY")
        print("  请到 MiniMax 控制台获取: https://platform.minimax.chat/")
        print("  获取后运行:")
        print("  echo 'export MINIMAX_API_KEY=\"your_key_here\"' >> ~/.zshrc")
        print("  source ~/.zshrc")
        return False

def check_wecom_webhook():
    step("检查企业微信 Webhook")
    webhook = os.environ.get("WECOM_WEBHOOK", "")
    if webhook:
        ok(f"已配置 (前20位: {webhook[:20]}...)")
        return True
    else:
        warn("未配置 WECOM_WEBHOOK")
        print("  配置方式:")
        print("  1. 打开企业微信 App")
        print("  2. 进入需要接收提醒的群 → 群设置 → 智能群助手 → 添加机器人")
        print("  3. 复制 Webhook 地址，格式如:")
        print("     https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx")
        print("  4. 运行: echo 'export WECOM_WEBHOOK=\"your_webhook_url\"' >> ~/.zshrc")
        print("  5. source ~/.zshrc")
        return False

def init_database():
    step("初始化数据库")
    try:
        from meeting_assistant import init_db
        init_db()
        ok("数据库初始化完成 (data/meeting.db)")
        return True
    except Exception as e:
        error(f"数据库初始化失败: {e}")
        return False

def main():
    print("=" * 50)
    print("  📋 企业微信会议助手 - 安装配置")
    print("=" * 50)

    checks = {
        "Whisper": check_whisper(),
        "ffmpeg": check_ffmpeg(),
        "MiniMax API": check_minimax_key(),
        "企业微信Webhook": check_wecom_webhook(),
    }

    print("\n" + "=" * 50)
    print("  📊 检查结果汇总")
    print("=" * 50)

    all_pass = True
    for name, passed in checks.items():
        status = "✅" if passed else "⚠️"
        print(f"  {status} {name}")

    if not checks["MiniMax API"]:
        all_pass = False
        print("\n  ⚠️ MiniMax API Key 未配置，AI分析功能无法使用")
        print("  其他功能（转写、记录）仍可正常使用")

    if not checks["Whisper"]:
        all_pass = False
        print("\n  ⚠️ Whisper 未安装，音频转写需要先安装")
        print("  brew install openai-whisper")

    if all_pass:
        ok("\n所有依赖检查通过！")
    else:
        warn("\n部分依赖未就绪，但核心功能可以开始使用")

    # 初始化数据库
    init_database()

    print("\n" + "=" * 50)
    print("  🚀 快速开始")
    print("=" * 50)
    print("""
  方式1 - 文字输入（无需录音设备）:
    python3 meeting_assistant.py --add "今天开会讨论了...张三负责..."

  方式2 - 音频转写（需要录音文件）:
    python3 meeting_assistant.py --audio recording.m4a

  方式3 - 推送早会待办:
    python3 meeting_assistant.py --daily

  方式4 - 查看今日待办:
    python3 meeting_assistant.py --today

  ============================================
  企业微信使用方式:
  1. 把机器人拉到企业微信群
  2. 每次 --daily 会自动推送到群里
  3. 设置定时任务（每天8:30自动推送）:
     openclaw cron add "0 8 * * *" --daily
  ============================================
  """)

if __name__ == "__main__":
    main()
