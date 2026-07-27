#!/usr/bin/env python3
"""
skill-router reindex.py
扫描所有 Skills，自动生成 trigger_index.json

用法: python3 reindex.py
"""

import json
import re
from pathlib import Path

WORKSPACE = Path.home() / "openclaw-workspace"
SKILLS_DIR = WORKSPACE / "skills"
OUT_FILE = WORKSPACE / "skills/skill-router/scripts/trigger_index.json"


def extract_description(skill_path: Path) -> str:
    """从 SKILL.md frontmatter 提取 description"""
    sk = skill_path / "SKILL.md"
    if not sk.exists():
        return ""
    text = sk.read_text(encoding="utf-8")
    # 提取 description 字段
    m = re.search(r'description:\s*["""]([^"""]{1,500})["""]', text)
    if m:
        return m.group(1).strip()
    return ""


def extract_keywords_from_description(desc: str) -> list:
    """从 description 自动提取关键词"""
    keywords = []
    # 英文词提取（>=3字母）
    en_words = re.findall(r'\b[a-z][a-z0-9-]{2,}\b', desc.lower())
    keywords.extend([w for w in set(en_words) if w not in {
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'these',
        'those', 'when', 'then', 'than', 'mode', 'list', 'edit',
        'send', 'read', 'load', 'save', 'type', 'tool', 'file',
        'path', 'name', 'task', 'work', 'mode', 'step', 'flow',
        'note', 'call', 'text', 'data', 'find', 'open', 'link',
        'user', 'your', 'also', 'only', 'each', 'both', 'same',
    }])
    
    # 中文关键概念
    zh_concepts = re.findall(r'[\u4e00-\u9fff]{2,4}', desc)
    for c in set(zh_concepts):
        if len(c) >= 2:
            keywords.append(c)
    
    # 常见触发词（基于描述内容）
    triggers = []
    if 'pdf' in desc.lower(): triggers.append('pdf')
    if 'github' in desc.lower(): triggers.append('github')
    if 'mail' in desc.lower() or 'email' in desc.lower(): triggers.append('email')
    if 'calendar' in desc.lower(): triggers.append('calendar')
    if 'write' in desc.lower() or '写作' in desc: triggers.append('写作')
    if 'novel' in desc.lower() or '小说' in desc: triggers.extend(['小说', '网文', '章节', '写作'])
    if 'image' in desc.lower() or '图片' in desc: triggers.append('图片')
    if 'video' in desc.lower() or '视频' in desc: triggers.append('视频')
    if 'music' in desc.lower() or '音频' in desc or '音乐' in desc: triggers.append('音乐')
    if 'web' in desc.lower() or 'search' in desc.lower(): triggers.append('搜索')
    if '天气' in desc or 'weather' in desc.lower(): triggers.append('天气')
    if '微信' in desc or 'wechat' in desc.lower(): triggers.extend(['微信', 'wechat'])
    if 'telegram' in desc.lower(): triggers.append('telegram')
    if 'discord' in desc.lower(): triggers.append('discord')
    if 'video' in desc.lower() or 'youtube' in desc.lower(): triggers.append('视频')
    if 'ppt' in desc.lower() or 'presentation' in desc.lower(): triggers.extend(['ppt', '幻灯片', '演示'])
    if 'skill' in desc.lower(): triggers.append('技能')
    
    keywords.extend(triggers)
    # 去重，保持顺序
    seen = set()
    unique = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique.append(kw)
    
    return unique[:30]  # 最多30个关键词


def scan_skills():
    """扫描 skills 目录，构建索引"""
    index = {}
    
    if not SKILLS_DIR.exists():
        print(f"❌ Skills 目录不存在: {SKILLS_DIR}")
        return
    
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name == "skill-router":
            continue  # 不索引自己
        
        skill_name = skill_dir.name
        desc = extract_description(skill_dir)
        keywords = extract_keywords_from_description(desc)
        
        # 手动补充一些高权重关键词
        extra_kw = get_manual_keywords(skill_name)
        keywords.extend(extra_kw)
        seen = set()
        kw_unique = []
        for kw in keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                kw_unique.append(kw)
        keywords = kw_unique[:30]
        
        index[skill_name] = {
            "keywords": keywords,
            "weight": get_weight(skill_name),
            "description": desc,
        }
    
    return index


def get_weight(skill_name: str) -> int:
    """根据技能类型分配权重"""
    high_weight = {
        'tianming-novel-system', 'tianming-enhanced',
        'novel-studio', 'novel-reader',
        'writing-style', 'shuorenhua', 'avoid-ai-writing',
        'skill-router', 'skill-creator',
        'taskflow', 'summarize',
    }
    if skill_name in high_weight:
        return 5
    medium_weight = {
        'github', 'gh-issues', 'gog', 'himalaya', 'bear-notes',
        'trello', 'obsidian', 'xurl', 'blogwatcher',
        'meme-maker', 'diagram-maker', 'drawio', 'songsee',
        'video-frames', 'nano-pdf', 'gpt-image2-ppt',
        'telegram', 'discord', 'slack', 'imsg', 'wacli',
    }
    if skill_name in medium_weight:
        return 3
    return 1


def get_manual_keywords(skill_name: str) -> list:
    """手动补充高价值触发词"""
    manual = {
        'novel-reader': ['小说网站', '阅读', '追书', '17K', '起点', '番茄', '小说'],
        'novel-studio': ['小说', '网文', '写作', '写小说'],
        'tianming-novel-system': ['天命', '写小说', '网文', '章节', '大纲', '角色', '小说', '修仙', '玄幻', '都市'],
        'tianming-enhanced': ['审稿', '合规', '投稿', '格式检查', '体检'],
        'writing-style': ['文风', '写作风格', '模仿', '文笔'],
        'shuorenhua': ['去AI味', '说人话', 'AI味', '自然', '不像AI'],
        'avoid-ai-writing': ['AI味', '去AI味', '润色', '不像AI'],
        'skill-creator': ['创建技能', '新建技能', '写SKILL', '技能'],
        'skill-router': ['路由', '自动触发', 'skills自动', 'skill自动'],
        'taskflow': ['多步骤', '流程', '子任务', '等待', '编排'],
        'summarize': ['总结', '摘要', '概括', '提炼', '汇总'],
        'github': ['github', 'pr', 'issue', '仓库', 'repo'],
        'gog': ['gmail', '谷歌', 'google workspace', '日历', 'drive', '谷歌日历', '邮件', 'email'],
        'himalaya': ['邮件', 'email', 'mail', 'himalaya', 'smtp', 'imap'],
        'gh-issues': ['issue', 'bug', 'github issues', 'bug报告'],
        'xurl': ['twitter', 'x.com', '推文', 'tweet', '发帖'],
        'diagram-maker': ['图表', '架构图', '流程图', '脑图', 'diagram'],
        'drawio': ['图表', '架构', '流程图', 'draw.io'],
        'nano-pdf': ['pdf编辑', 'pdf修改', 'pdf合并', 'pdf转'],
        'gpt-image2-ppt': ['ppt', '幻灯片', '演示文稿', '做PPT', 'presentation'],
        'blogwatcher': ['rss', '订阅', '博客更新', 'feed', '博客'],
        'trello': ['trello', '看板', '项目管理'],
        'bear-notes': ['bear', '笔记', '苹果笔记'],
        'obsidian': ['obsidian', '双链', '笔记'],
        'memu': ['记忆', '存储', 'memu', '长期记忆'],
        'songsee': ['音频', '音乐', '频谱', 'spectrogram', '波形'],
        'video-frames': ['视频帧', '截图', 'ffmpeg', '视频截图'],
        'meme-maker': ['表情包', 'meme', '梗图', '表情'],
        'companion-simple': ['陪伴', '聊天', '小跃', '伴侣'],
        'imsg': ['imessage', '短信', '苹果消息'],
        'wacli': ['whatsapp', 'wa', 'WhatsApp'],
        'telegram': ['telegram', 'tg', '电报'],
        'discord': ['discord', '频道'],
        'healthcheck': ['安全', '审计', '防火墙', 'ssh', '漏洞'],
        'soul-guardian': ['守护', '完整性', 'drift', '守护'],
        'clawsec-suite': ['安全', '签名', '验证', '恶意'],
        'spike': ['原型', '验证', '可行性', 'demo'],
        'gh-issues': ['issue', 'bug', 'github issues', 'bug报告'],
    }
    return manual.get(skill_name, [])


def main():
    print("🔍 扫描 Skills 目录...")
    index = scan_skills()
    
    if not index:
        print("❌ 扫描失败")
        return
    
    # 写入索引文件
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引生成完成！共 {len(index)} 个 Skills")
    print(f"📁 输出文件: {OUT_FILE}")
    
    # 打印摘要
    print("\n📋 索引摘要（前10个）:")
    for i, (name, entry) in enumerate(sorted(index.items(), key=lambda x: -x[1]['weight'])[:10]):
        kw_count = len(entry['keywords'])
        print(f"  [{entry['weight']}] {name:<30} ({kw_count} 关键词)")


if __name__ == "__main__":
    main()
