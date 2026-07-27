#!/usr/bin/env python3
"""
SkillOpt训练API - 多路径预缓存版本
"""
import os, sys

sys.path.insert(0, '/Users/wushixiaoshenxian/Library/Python/3.12/lib/python/site-packages')

os.environ["MINIMAX_BASE_URL"] = "https://api.minimax.chat/v1"
os.environ["MINIMAX_API_KEY"] = os.environ.get("MINIMAX_API_KEY", "")

from skillopt.prompts import clear_cache, load_prompt, _PROMPTS_DIR, _REFLACT_DIR, _cache
clear_cache()

# 预缓存真实路径
import os
real_prompts_dir = _PROMPTS_DIR
print(f"Real prompts dir: {real_prompts_dir}")

for fname in os.listdir(real_prompts_dir):
    if not fname.endswith('.md'):
        continue
    real_path = os.path.join(real_prompts_dir, fname)
    with open(real_path) as f:
        content = f.read()
    _cache[real_path] = content
    rel_key = f"skillopt/prompts/{fname}"
    _cache[rel_key] = content
    print(f"  ✅ Cached '{fname}' ({len(content)} chars)")

print(f"✅ Pre-cache done, {len(_cache)} entries")

# 训练
from skillopt.config import load_config, flatten_config
from skillopt.engine.trainer import ReflACTTrainer
from scripts.train import get_adapter

cfg_path = '/Users/wushixiaoshenxian/openclaw-workspace/skillopt-test/miniqa_config.yaml'
structured_cfg = load_config(cfg_path)
cfg = flatten_config(structured_cfg)
cfg['out_root'] = os.path.abspath(cfg.get('out_root', '/Users/wushixiaoshenxian/openclaw-workspace/skillopt-test/outputs'))
print(f"✅ Config OK, env={cfg.get('env')}")

adapter = get_adapter(cfg)
print(f"✅ Adapter: {type(adapter).__name__}")

trainer = ReflACTTrainer(cfg, adapter)
print("✅ Training...")
summary = trainer.train()
print(f"\n✅ Done! sel_hard={summary.get('sel_hard')}, test_hard={summary.get('test_hard')}")
