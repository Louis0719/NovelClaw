"""
step1_extract_scenes.py
Step 1: 把小说 TXT 按章节/段落拆分为场景列表
"""
import json
import re
from pathlib import Path
from config import OUTPUT_DIR, SCENE_MAX_CHARS


def split_novel(text: str) -> list[dict]:
    """按章节标记 + 段落拆分小说"""
    scenes = []
    
    # 章节标记正则
    marker_pattern = re.compile(
        r'^[\s\t]*(?:第\s*[0-9０-９]+\s*[章集节幕][^\n]*|'
        r'(?:chapter|episode|ep|part)\s+\d+[^\n]*|'
        r'#{1,3}\s+[^\n]+|'
        r'\[[^\]]+\])[\s\t]*$',
        re.IGNORECASE | re.MULTILINE
    )
    
    # 找所有章节标记
    markers = list(marker_pattern.finditer(text))
    
    if len(markers) >= 2:
        # 路径A: 有章节标记
        # 开篇内容
        pre = text[:markers[0].start()].strip()
        if len(pre) >= 100:
            scenes.append({
                "index": 0,
                "title": "序章",
                "text": pre,
                "char_count": len(pre),
            })
        
        for i, m in enumerate(markers):
            start = m.start()
            end = markers[i+1].start() if i+1 < len(markers) else len(text)
            seg = text[start:end].strip()
            if not seg:
                continue
            first_line = seg.split('\n')[0][:40].strip()
            scenes.append({
                "index": i + 1,
                "title": first_line or f"第{i+1}章",
                "text": seg,
                "char_count": len(seg),
            })
    else:
        # 路径B: 无章节标记，按段落拆分
        paras = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]
        buf = ""
        idx = 0
        for para in paras:
            if buf and (len(buf) + len(para) > SCENE_MAX_CHARS):
                scenes.append({
                    "index": idx,
                    "title": f"场景 {idx+1}",
                    "text": buf,
                    "char_count": len(buf),
                })
                buf = para
                idx += 1
            else:
                buf += ("\n\n" + para if buf else para)
        
        if buf:
            scenes.append({
                "index": idx,
                "title": f"场景 {idx+1}",
                "text": buf,
                "char_count": len(buf),
            })
    
    # 每个场景再拆成更小的镜头（按自然段落）
    refined = []
    for scene in scenes:
        sub_scenes = _split_scene(scene)
        refined.extend(sub_scenes)
    
    # 重新编号
    for i, s in enumerate(refined):
        s["index"] = i + 1
    
    return refined


def _split_scene(scene: dict) -> list[dict]:
    """把一个场景拆成多个镜头"""
    paras = [p.strip() for p in scene["text"].split('\n\n') if p.strip() and len(p.strip()) > 30]
    
    if len(paras) <= 2:
        return [scene]
    
    # 按每 500 字一个镜头
    chunks = []
    buf = ""
    for para in paras:
        if buf and (len(buf) + len(para) > 500):
            chunks.append(buf)
            buf = para
        else:
            buf += ("\n\n" + buf if buf else "") + para if not buf else "\n\n" + para
    
    if buf:
        chunks.append(buf)
    
    if not chunks:
        return [scene]
    
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "index": f"{scene['index']}-{i+1}",
            "title": f"{scene['title']} ({i+1})",
            "text": chunk,
            "char_count": len(chunk),
        })
    return result


def run(novel_path: str) -> Path:
    """执行 Step 1"""
    print(f"📖 读取小说: {novel_path}")
    text = Path(novel_path).read_text(encoding="utf-8")
    print(f"  总字数: {len(text)} 字")
    
    print("✂️ 开始分镜...")
    scenes = split_novel(text)
    print(f"  共拆分 {len(scenes)} 个镜头")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "scenes.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(scenes),
            "scenes": scenes,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分镜数据已保存: {out_file}")
    for s in scenes[:5]:
        print(f"  [{s['index']}] {s['title']} ({s['char_count']}字)")
    if len(scenes) > 5:
        print(f"  ... 共 {len(scenes)} 个")
    
    return out_file
