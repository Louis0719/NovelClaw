"""
novel-manhua-workflow main.py
一键运行所有步骤

用法:
  python main.py --step 1 --novel "path/to/novel.txt"
  python main.py --step all --novel "path/to/novel.txt"
"""
import argparse
import sys
from pathlib import Path

# 确保当前目录在 path 中
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_dirs, OUTPUT_DIR

def run_step(step: int, novel_path: str = None, **kwargs):
    """根据步骤号运行"""
    if step == 1:
        if not novel_path:
            raise ValueError("step 1 需要指定 --novel 参数")
        from step1_extract_scenes import run as run_step1
        return run_step1(novel_path)
    
    elif step == 2:
        from step2_extract_characters import run as run_step2
        return run_step2()
    
    elif step == 3:
        from step3_gen_character_images import run as run_step3
        return run_step3()
    
    elif step == 4:
        from step4_gen_scene_images import run as run_step4
        return run_step4(kwargs.get("limit", 5))
    
    elif step == 5:
        from step5_gen_video import run as run_step5
        return run_step5(kwargs.get("limit", 3))
    
    elif step == 6:
        from step6_compose import run as run_step6
        return run_step6(kwargs.get("output", "final.mp4"))
    
    else:
        raise ValueError(f"未知步骤: {step}")


def run_all(novel_path: str, scene_limit: int = 5, video_limit: int = 3):
    """一键运行全流程"""
    print("=" * 60)
    print("🚀 AI 漫剧工作流 - 全流程启动")
    print("=" * 60)
    
    ensure_dirs()
    
    steps = [
        (1, {"novel_path": novel_path}),
        (2, {}),
        (3, {}),
        (4, {"limit": scene_limit}),
        (5, {"limit": video_limit}),
        (6, {}),
    ]
    
    for step_num, kwargs in steps:
        print(f"\n{'='*60}")
        print(f"🔄 Step {step_num}/6")
        print("=" * 60)
        try:
            run_step(step_num, **kwargs)
        except FileNotFoundError as e:
            print(f"⚠️ 跳过（未找到前置文件）: {e}")
        except Exception as e:
            print(f"❌ Step {step_num} 失败: {e}")
            print("💡 可以单独重跑失败的步骤: python main.py --step N")
    
    print(f"\n{'='*60}")
    print("🎉 全流程完成！")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"📄 最终成品: {OUTPUT_DIR / 'final.mp4'}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="AI 漫剧工作流")
    parser.add_argument("--step", type=str, required=True,
                        help="步骤编号 (1-6) 或 'all'")
    parser.add_argument("--novel", type=str, default=None,
                        help="小说 TXT 文件路径 (step 1 需要)")
    parser.add_argument("--limit", type=int, default=None,
                        help="场景图/视频生成数量上限")
    parser.add_argument("--output", type=str, default="final.mp4",
                        help="输出文件名")
    
    args = parser.parse_args()
    
    if args.step == "all":
        if not args.novel:
            print("❌ 全流程需要指定 --novel")
            sys.exit(1)
        run_all(args.novel, scene_limit=args.limit or 5, video_limit=args.limit or 3)
    else:
        try:
            step_num = int(args.step)
            kwargs = {"novel_path": args.novel}
            if args.limit is not None:
                kwargs["limit"] = args.limit
            if args.output:
                kwargs["output"] = args.output
            result = run_step(step_num, **kwargs)
            print(f"\n✅ Step {step_num} 完成！")
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"❌ {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
