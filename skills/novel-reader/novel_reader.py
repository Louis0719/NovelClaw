#!/usr/bin/env python3
"""
小说阅读器 v2 - 跨平台小说内容抓取
主力平台: 17K小说网
备用平台: 起点中文网、晋江、飞卢（部分可用）

用法:
  python3 novel_reader.py toc <书籍ID或URL>      # 获取目录
  python3 novel_reader.py read <书籍ID> <章节ID> # 读章节
  python3 novel_reader.py url <完整章节URL>     # 直接读任意章节URL
  python3 novel_reader.py sites                 # 测试所有平台

示例:
  python3 novel_reader.py toc 3631088
  python3 novel_reader.py read 3631088 49406153
  python3 novel_reader.py url https://www.17k.com/chapter/3631088/49406154.html
"""

import asyncio
import re
import sys
import argparse
from playwright.async_api import async_playwright

# ============================================================
# 核心读取函数
# ============================================================

async def read_url(url: str) -> dict:
    """用Playwright读取任意URL的小说章节内容"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 900})
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(3)
            
            # 尝试多个selector找正文
            for sel in ['.content', '.chapter-content', '.read-content', '#content', '.article']:
                try:
                    els = await page.query_selector_all(sel)
                    texts = [await e.inner_text() for e in els]
                    combined = '\n'.join(texts).strip()
                    if len(combined) > 200:
                        paras = _clean_paragraphs(combined, url)
                        return {
                            'url': url,
                            'selector': sel,
                            'paragraphs': paras,
                            'raw_len': len(combined),
                            'para_count': len(paras),
                        }
                except:
                    pass
            
            # 最后手段：取body
            body = await page.inner_text('body')
            paras = _clean_paragraphs(body, url)
            return {
                'url': url,
                'selector': 'body',
                'paragraphs': paras,
                'raw_len': len(body),
                'para_count': len(paras),
            }
        finally:
            await browser.close()


def _clean_paragraphs(text: str, url: str) -> list:
    """清洗段落：去除页头页脚广告"""
    lines = text.split('\n')
    skip_keywords = [
        '17K', '17k', '小说网', '17k.com', 'www.17k.com',
        '更新时间', '本章共', '字数', '更新于', '上一章', '下一章',
        '返回目录', '加入书架', '推荐票', '送礼物',
        '起点中文网', 'qq阅读', '起点读书', '起点',
        '晋江文学', 'jjwxc', 'jjwxc.net',
        '纵横中文', 'zongheng', 'zongheng.com',
        '飞卢小说', 'faloo',
        '番茄小说', 'fanqie',
        '最新章节', '上一章', '下一章', '目录', '章节目录',
        '加入书架', '免费阅读', 'VIP章节', '订阅', '打赏',
        '第1页', '第2页', '页', '上一章', '返回', '下一章',
    ]
    
    paras = []
    for line in lines:
        line = line.strip()
        # 过滤：太短不要，太长可能是标题合并
        if len(line) < 10:
            continue
        # 过滤：包含跳过关键词
        skip = False
        for kw in skip_keywords:
            if kw in line:
                skip = True
                break
        # 过滤：纯数字或纯符号
        if re.match(r'^[第\d]+章', line) and len(line) < 50:
            continue  # 章节标题单独处理
        if re.match(r'^[\d\s\-\.]+$', line):
            continue
        if skip:
            continue
        
        paras.append(line)
    
    return paras

# ============================================================
# 平台特定函数
# ============================================================

async def get_toc_17k(bid: str) -> list:
    """获取17K书籍目录"""
    url = f'https://www.17k.com/list/{bid}.html'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 900})
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(3)
            
            # 用JS提取所有章节链接
            links = await page.evaluate('''() => {
                const result = [];
                const as = document.querySelectorAll('a');
                for (const a of as) {
                    if (a.href && a.href.includes('/chapter/')) {
                        let title = (a.title || a.innerText || '').trim();
                        // 清理干扰信息
                        title = title.replace(/字数：\\d+[\\r\\n]*/g, '');
                        title = title.replace(/更新日期[^\\s]*/g, '');
                        title = title.replace(/\\s{2,}/g, ' ').trim();
                        result.push({ title, href: a.href });
                    }
                }
                return result;
            }''')
            
            chapters = []
            for l in links[:600]:
                m = re.search(r'/chapter/(\d+)/(\d+)\.html', l['href'])
                if m:
                    chapters.append({
                        'num': len(chapters) + 1,
                        'title': l['title'].strip(),
                        'bid': m.group(1),
                        'cid': m.group(2),
                        'url': l['href'],
                    })
            return chapters
        finally:
            await browser.close()


def make_chapter_url(site: str, bid: str, cid: str) -> str:
    """构建章节URL"""
    if site == '17k':
        return f'https://www.17k.com/chapter/{bid}/{cid}.html'
    return f'https://www.17k.com/chapter/{bid}/{cid}.html'

# ============================================================
# CLI 命令
# ============================================================

def extract_ids_from_input(text: str) -> tuple:
    """从输入中提取bid和cid"""
    text = text.strip()
    
    # 直接是纯数字
    if text.isdigit():
        return text, None
    
    # URL格式
    m = re.search(r'/chapter/(\d+)/(\d+)\.html', text)
    if m:
        return m.group(1), m.group(2)
    
    # 书籍URL
    m = re.search(r'/book/(\d+)\.html', text)
    if m:
        return m.group(1), None
    
    m = re.search(r'17k\.com/(\w+)/(\d+)\.html', text)
    if m:
        return m.group(2), None
    
    return text, None


async def cmd_toc(args):
    bid, _ = extract_ids_from_input(args.book_or_url)
    if not bid:
        print('无法解析书籍ID')
        return
    
    print(f'正在获取《{bid}》的目录...')
    chapters = await get_toc_17k(bid)
    
    if not chapters:
        print('未找到目录，可能书籍不存在或需要登录')
        return
    
    print(f'\n找到 {len(chapters)} 章:\n')
    print(f'{"序号":>4}  {"章节":<30}  {"章节ID"}')
    print('-' * 55)
    for ch in chapters[:100]:
        print(f'{ch["num"]:>4}  {ch["title"][:28]:<30}  {ch["cid"]}')
    if len(chapters) > 100:
        print(f'  ... 还有 {len(chapters)-100} 章')


async def cmd_read(args):
    if args.url:
        result = await read_url(args.url)
        _print_content(result)
    else:
        bid, cid = extract_ids_from_input(args.book_id)
        if not bid:
            print('无法解析书籍ID')
            return
        if not args.chapter_id:
            print('请提供章节ID或使用 --url 直接指定URL')
            return
        
        cid2, _ = extract_ids_from_input(args.chapter_id)
        url = make_chapter_url('17k', bid, cid2)
        result = await read_url(url)
        _print_content(result)


async def cmd_url(args):
    result = await read_url(args.url)
    _print_content(result)


def _print_content(result: dict):
    print(f'\n字数: {result["raw_len"]} | 有效段落: {result["para_count"]} | 选择器: {result["selector"]}\n')
    print('=' * 62)
    for p in result['paragraphs'][:50]:
        print(p)
        print()


async def cmd_sites(args):
    """测试所有平台"""
    sites = [
        ('17K小说网', 'https://www.17k.com/chapter/3631088/49406153.html'),
        ('起点中文网', 'https://www.qidian.com/'),
        ('晋江文学城', 'https://www.jjwxc.net/'),
        ('飞卢小说网', 'https://www.faloo.com/'),
        ('纵横中文网', 'https://www.zongheng.com/'),
        ('七猫小说网', 'https://www.qimao.com/'),
    ]
    
    print('测试各平台可达性:\n')
    for name, url in sites:
        try:
            result = await read_url(url)
            status = f'✅ {result["raw_len"]}字' if result["raw_len"] > 100 else f'⚠️ {result["raw_len"]}字'
            print(f'  {name}: {status}')
        except Exception as e:
            print(f'  {name}: ❌ {e}')


def main():
    parser = argparse.ArgumentParser(
        description='小说阅读器 - 跨平台小说内容抓取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python3 novel_reader.py toc 3631088
  python3 novel_reader.py read 3631088 49406153
  python3 novel_reader.py url https://www.17k.com/chapter/3631088/49406154.html
  python3 novel_reader.py sites
        '''
    )
    sub = parser.add_subparsers()
    
    t = sub.add_parser('toc', help='获取书籍目录')
    t.add_argument('book_or_url', help='书籍ID或书籍URL')
    
    r = sub.add_parser('read', help='读章节')
    r.add_argument('book_id', nargs='?', help='书籍ID')
    r.add_argument('chapter_id', nargs='?', help='章节ID')
    r.add_argument('--url', help='直接章节URL（优先级最高）')
    
    u = sub.add_parser('url', help='直接读任意章节URL')
    u.add_argument('url', help='完整章节URL')
    
    s = sub.add_parser('sites', help='测试所有平台')
    
    args = parser.parse_args()
    
    if hasattr(args, 'book_or_url'):
        asyncio.run(cmd_toc(args))
    elif hasattr(args, 'url') and args.url:
        asyncio.run(cmd_read(args))
    elif hasattr(args, 'book_id'):
        asyncio.run(cmd_read(args))
    elif hasattr(args, 'url'):
        asyncio.run(cmd_url(args))
    elif hasattr(args, 'book_id'):
        asyncio.run(cmd_sites(args))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
