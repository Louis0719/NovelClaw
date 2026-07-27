#!/usr/bin/env python3
"""
meeting-assistant v3.0 - 企业微信会议助手
==========================================
功能：
  1. 接收会议录音 → Whisper转写 → AI提取待办
  2. 客户沟通记录 → 自动归档 → 提取待办
  3. 每天早上推送当天待办任务（含逾期预警）
  4. 任务完成状态管理
  5. 历史会议语义搜索（类AskFred）
  6. 早会统计（本周完成/新增/逾期）

用法:
  python3 meeting_assistant.py              # 交互模式（显示今日待办）
  python3 meeting_assistant.py --add "文本内容"  # 直接添加内容
  python3 meeting_assistant.py --audio audio.m4a  # 音频转写+分析
  python3 meeting_assistant.py --daily            # 推送早会待办（含逾期）
  python3 meeting_assistant.py --query "张总说了什么"  # 搜索历史会议
  python3 meeting_assistant.py --list             # 列出所有待办
  python3 meeting_assistant.py --done <id>         # 标记完成
  python3 meeting_assistant.py --today             # 查看今日待办
  python3 meeting_assistant.py --stats             # 查看本周统计
"""

import re, os, sys, json, sqlite3, logging
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

# ====== 路径配置 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "meeting.db")
LOG_PATH = os.path.join(LOG_DIR, "meeting.log")

# ====== 日志配置 ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("meeting-assistant")

# ====== LLM 配置（MiniMax）======
LLM_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
LLM_BASE_URL = "https://api.minimax.chat/v1"
LLM_MODEL = "MiniMax-Text-01"

# ====== 企业微信机器人 Webhook ======
WECOM_WEBHOOK = os.environ.get("WECOM_WEBHOOK", "")

# =============================================
# 数据库初始化
# =============================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'text',
            speaker TEXT,
            meeting_date TEXT,
            meeting_title TEXT,
            raw_text TEXT,
            summary TEXT,
            todos TEXT,
            created_at TEXT DEFAULT (datetime('now', '+8 hours')),
            updated_at TEXT DEFAULT (datetime('now', '+8 hours'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            source_meeting_id INTEGER,
            owner TEXT,
            deadline TEXT,
            priority TEXT DEFAULT '中',
            status TEXT DEFAULT 'pending',
            notes TEXT,
            tags TEXT,
            created_at TEXT DEFAULT (datetime('now', '+8 hours')),
            done_at TEXT,
            reminder_sent INTEGER DEFAULT 0,
            FOREIGN KEY (source_meeting_id) REFERENCES meetings(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_briefings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brief_date TEXT UNIQUE,
            content TEXT,
            todos TEXT,
            sent_at TEXT,
            created_at TEXT DEFAULT (datetime('now', '+8 hours'))
        )
    """)

    # ====== 索引优化（v3.0新增）======
    cur.execute("CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_todos_deadline ON todos(deadline)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(meeting_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_meetings_title ON meetings(meeting_title)")

    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")

# =============================================
# MiniMax LLM 调用
# =============================================
def call_llm(prompt: str, system: str = "") -> str:
    """调用 MiniMax LLM 返回文字"""
    if not LLM_API_KEY:
        raise RuntimeError(
            "未配置 MINIMAX_API_KEY，请设置环境变量：\n"
            "  export MINIMAX_API_KEY='your_key'"
        )

    import urllib.request, urllib.error

    url = f"{LLM_BASE_URL}/text/chatcompletion_v2"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system or "你是一个专业的会议助手，擅长从会议记录中提取关键信息和待办事项。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"LLM API错误 ({e.code}): {error_body[:300]}")
    except Exception as e:
        raise RuntimeError(f"LLM调用失败: {e}")

# =============================================
# AI 分析：从文本中提取待办
# =============================================
def extract_todos_from_text(text: str, source: str = "text") -> dict:
    """
    使用AI从会议记录/沟通记录中提取待办事项
    """
    system = """你是一个专业的商业助理。从给定的会议记录或沟通内容中：

1. 生成一个简洁的标题（10字内）
2. 生成一段摘要（100字内）
3. 提取所有待办事项，包括：
   - 任务内容（具体可执行）
   - 负责人（如果有提到）
   - 截止日期（如果有提到，格式YYYY-MM-DD）
   - 优先级（高/中/低，根据任务紧急程度判断）

输出格式（严格JSON，不要其他内容）：
{
  "title": "标题",
  "summary": "摘要",
  "todos": [
    {"task": "任务描述", "owner": "负责人", "deadline": "2026-07-15", "priority": "高"}
  ]
}

如果没有待办事项，todos数组留空。
所有日期必须是 YYYY-MM-DD 格式。
负责人如果是客户，用"客户"表示。"""

    today = date.today().strftime("%Y-%m-%d")
    prompt = f"""请分析以下内容，提取信息。

当前日期是：{today}

内容：
{text[:4000]}

【重要】
- 当前日期是 {today}
- 所有日期必须 >= {today}（不能是过去的日期！）
- 如果提到"这周"指本周内，"月底"指本月最后一天，"尽快"指本周内
- 严格按JSON格式输出，不要任何其他内容
- deadline如果没有明确日期，根据上下文合理推断或写null
- owner如果没有明确，写null
- priority根据内容判断：需要当天/尽快完成的=高，有明确截止=中，其他=低"""

    try:
        raw = call_llm(prompt, system)
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if raw.endswith("```") else lines)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        data = json.loads(raw)
        return {
            "title": data.get("title", "未命名"),
            "summary": data.get("summary", ""),
            "todos": data.get("todos", [])
        }
    except json.JSONDecodeError as e:
        logger.warning(f"JSON解析失败，使用备用方案: {e}")
        return {"title": "待处理", "summary": text[:100], "todos": []}
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning(f"AI分析异常: {e}")
        return {"title": "待处理", "summary": text[:100], "todos": []}

# =============================================
# AI 语义搜索（类 AskFred）
# =============================================
def query_meetings(query: str, top_k: int = 3) -> str:
    """
    搜索历史会议，返回与query最相关的会议片段
    策略：先做关键词匹配找候选，再用LLM做语义判断
    """
    conn = get_db()
    cur = conn.cursor()

    # 提取query中的关键词
    keywords = re.findall(r'[\w]{2,}', query)
    keyword_pattern = " OR ".join([f"content LIKE '%{k}%' OR summary LIKE '%{k}%'" for k in keywords[:5]])

    if keyword_pattern:
        cur.execute(f"""
            SELECT id, meeting_title, summary, raw_text, created_at
            FROM meetings
            WHERE {keyword_pattern}
            ORDER BY created_at DESC
            LIMIT 20
        """)
    else:
        cur.execute("""
            SELECT id, meeting_title, summary, raw_text, created_at
            FROM meetings ORDER BY created_at DESC LIMIT 10
        """)

    candidates = cur.fetchall()
    conn.close()

    if not candidates:
        return "📭 没有找到相关的会议记录。\n\n可以尝试：\n  · 换一些关键词（如客户名、产品名）\n  · 用 --add 添加新的会议记录"

    # 如果候选少，直接用LLM总结最相关的几条
    if len(candidates) <= top_k:
        selected = candidates
    else:
        # LLM排序：选最相关的top_k条
        meeting_texts = "\n\n".join([
            f"--- 会议{id} [{dict(r)['created_at'][:10]}] {dict(r)['meeting_title']}\n"
            f"摘要：{dict(r)['summary'] or dict(r)['raw_text'][:200]}"
            for r in candidates
        ])

        rank_system = """你是一个会议记录检索助手。给定用户的搜索query，从候选会议列表中选出最相关的3条。
只返回会议ID列表，每行一个ID，例如：5\n3\n12
不要返回其他内容。"""

        try:
            ids_raw = call_llm(
                f"用户问题：{query}\n\n候选会议：\n{meeting_texts}",
                rank_system
            )
            selected_ids = [int(line.strip()) for line in ids_raw.strip().split("\n") if line.strip().isdigit()]
            selected = [r for r in candidates if r["id"] in selected_ids[:top_k]]
            if not selected:
                selected = list(candidates)[:top_k]
        except Exception:
            selected = list(candidates)[:top_k]

    # 构建回答
    lines = [f"🔍 搜索「{query}」找到 {len(selected)} 条相关记录：\n"]
    for r in selected:
        r = dict(r)
        content = r["raw_text"] or r["summary"] or ""
        snippet = content[:300].replace("\n", " ").strip()
        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📅 {r['created_at'][:10]} | {r['meeting_title'] or '未命名'}")
        lines.append(f"💬 {snippet}...")
        lines.append("")

    # 如果只有1条，让LLM直接回答问题
    if len(selected) == 1:
        r = dict(selected[0])
        content = r["raw_text"] or r["summary"] or ""
        if len(content) > 50:
            answer_system = """你是一个会议记录助手。根据下面的会议记录，用简洁的语言回答用户的问题。
如果会议记录中没有相关信息，直接说"没有找到相关内容"。"""
            try:
                answer = call_llm(f"用户问题：{query}\n\n会议记录：\n{content[:3000]}", answer_system)
                lines.append("━━━━━━━━━━━━━━━━━━━━")
                lines.append(f"💡 AI回答：\n{answer}")
            except Exception:
                pass

    return "\n".join(lines)

# =============================================
# 存储
# =============================================
def save_meeting(text: str, source: str = "text", speaker: str = None,
                  meeting_date: str = None, analysis: dict = None) -> int:
    """保存会议记录和提取结果"""
    conn = get_db()
    cur = conn.cursor()
    meeting_date = meeting_date or date.today().strftime("%Y-%m-%d")
    analysis = analysis or {}

    cur.execute("""
        INSERT INTO meetings (content, source, speaker, meeting_date, meeting_title,
                              raw_text, summary, todos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        text[:5000],
        source,
        speaker,
        meeting_date,
        analysis.get("title", ""),
        text[:8000],
        analysis.get("summary", ""),
        json.dumps(analysis.get("todos", []), ensure_ascii=False)
    ))
    meeting_id = cur.lastrowid

    for todo in analysis.get("todos", []):
        cur.execute("""
            INSERT INTO todos (task, source_meeting_id, owner, deadline, priority, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (
            todo.get("task", ""),
            meeting_id,
            todo.get("owner"),
            todo.get("deadline") if todo.get("deadline") and str(todo.get("deadline")) != "null" else None,
            todo.get("priority", "中")
        ))

    conn.commit()
    conn.close()
    logger.info(f"保存会议 ID={meeting_id}，提取到 {len(analysis.get('todos', []))} 个待办")
    return meeting_id

def get_pending_todos(owner: str = None) -> List[Dict]:
    """获取所有pending待办"""
    conn = get_db()
    cur = conn.cursor()

    sql = """
        SELECT t.*, m.meeting_title
        FROM todos t
        LEFT JOIN meetings m ON t.source_meeting_id = m.id
        WHERE t.status = 'pending'
    """
    params = []

    if owner:
        sql += " AND (t.owner = ? OR t.owner LIKE ?)"
        params.extend([owner, f"%{owner}%"])

    sql += " ORDER BY CASE t.priority WHEN '高' THEN 0 WHEN '中' THEN 1 ELSE 2 END, t.deadline ASC"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_overdue_todos() -> List[Dict]:
    """获取逾期未完成的待办"""
    conn = get_db()
    cur = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT t.*, m.meeting_title
        FROM todos t
        LEFT JOIN meetings m ON t.source_meeting_id = m.id
        WHERE t.status = 'pending' AND t.deadline < ?
        ORDER BY t.deadline ASC
    """, (today,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_upcoming_todos(days: int = 3) -> List[Dict]:
    """获取未来N天内将到期的待办"""
    conn = get_db()
    cur = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    future = (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT t.*, m.meeting_title
        FROM todos t
        LEFT JOIN meetings m ON t.source_meeting_id = m.id
        WHERE t.status = 'pending'
          AND t.deadline IS NOT NULL
          AND t.deadline > ?
          AND t.deadline <= ?
        ORDER BY t.deadline ASC
    """, (today, future))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_todo_done(todo_id: int) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE todos SET status='done', done_at=datetime('now', '+8 hours')
        WHERE id=?
    """, (todo_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_today_todos() -> List[Dict]:
    """
    获取今日/近期待办：已逾期 + 今日截止 + 7天内将截止的任务
    """
    conn = get_db()
    cur = conn.cursor()
    today = date.today().strftime("%Y-%m-%d")
    next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT t.*, m.meeting_title
        FROM todos t
        LEFT JOIN meetings m ON t.source_meeting_id = m.id
        WHERE t.status = 'pending'
          AND (t.deadline IS NULL
               OR t.deadline <= ?)
        ORDER BY
            CASE WHEN t.deadline IS NULL THEN 3
                 WHEN t.deadline < ? THEN 0
                 WHEN t.deadline = ? THEN 1
                 ELSE 2
            END,
            CASE t.priority WHEN '高' THEN 0 WHEN '中' THEN 1 ELSE 2 END,
            t.deadline ASC
    """, (next_week, today, today))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# =============================================
# 统计模块
# =============================================
def get_weekly_stats() -> dict:
    """获取本周统计数据"""
    conn = get_db()
    cur = conn.cursor()
    today = date.today()
    monday = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    # 本周新增
    cur.execute("SELECT COUNT(*) FROM todos WHERE date(created_at) >= ?", (monday,))
    new_count = cur.fetchone()[0]

    # 本周完成
    cur.execute("SELECT COUNT(*) FROM todos WHERE status='done' AND date(done_at) >= ?", (monday,))
    done_count = cur.fetchone()[0]

    # 仍在逾期
    cur.execute("SELECT COUNT(*) FROM todos WHERE status='pending' AND deadline < ?", (today_str,))
    overdue_count = cur.fetchone()[0]

    # 本周逾期已完成的
    cur.execute("""
        SELECT COUNT(*) FROM todos
        WHERE status='done' AND deadline < date(done_at) AND date(done_at) >= ?
    """, (monday,))
    overdue_done_count = cur.fetchone()[0]

    conn.close()
    return {
        "week_start": monday,
        "today": today_str,
        "new": new_count,
        "done": done_count,
        "overdue": overdue_count,
        "overdue_done": overdue_done_count,
    }

# =============================================
# 格式化输出
# =============================================
def format_todos_for_display(todos: List[Dict], title: str = "待办") -> str:
    if not todos:
        return f"✅ {title}，暂无任务"

    lines = []
    for i, t in enumerate(todos, 1):
        icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(t.get("priority","中"), "🟡")
        deadline_str = f"📅 {t['deadline']}" if t.get("deadline") else "📅 无期限"
        owner_str = f"👤 {t['owner']}" if t.get("owner") else "👤 待认领"
        source = f"（来源：{t['meeting_title']}）" if t.get("meeting_title") else ""
        lines.append(f"{i}. {icon} {t['task']}")
        lines.append(f"   {deadline_str} | {owner_str}{source}")
    return "\n".join(lines)

def build_daily_briefing() -> str:
    """
    构建早会待办推送内容 v3.0
    包含：逾期预警 + 今日待办 + 近日到期 + 本周统计
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_display = today.strftime("%m月%d日")
    weekday = ["周一","周二","周三","周四","周五","周六","周日"][today.weekday()]
    week_start = (today - timedelta(days=today.weekday())).strftime("%m月%d日")

    overdue = get_overdue_todos()
    upcoming = get_upcoming_todos(days=3)
    today_todos = get_today_todos()
    stats = get_weekly_stats()

    lines = [
        f"📋 每日待办 · {today_display} {weekday}",
        f"📆 本周（{week_start}起）",
        "━" * 22,
    ]

    # 统计行
    completion_rate = 0
    if stats["new"] > 0:
        completion_rate = int(stats["done"] / stats["new"] * 100)
    stat_line = f"📊 新增{stats['new']} | 完成{stats['done']} | 逾期{stats['overdue']} | 完成率{completion_rate}%"
    lines.append(stat_line)
    lines.append("")

    # 逾期区
    if overdue:
        overdue_ids = ", ".join([str(t["id"]) for t in overdue])
        lines.append(f"⚠️ 逾期未完成（{len(overdue)}项）⚠️")
        for t in overdue[:5]:
            days_overdue = (today - datetime.strptime(t["deadline"], "%Y-%m-%d").date()).days
            lines.append(f"  🔴 [{t['deadline']} 逾期{days_overdue}天] {t['task'][:32]}")
        if len(overdue) > 5:
            lines.append(f"  ... 还有{len(overdue)-5}项（ID: {overdue_ids}）")
        lines.append("")

    # 今日/近期待办
    if today_todos:
        lines.append(f"📌 近期待办（{len(today_todos)}项）")
        for i, t in enumerate(today_todos, 1):
            icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(t.get("priority","中"), "🟡")
            owner = f"👤{t['owner']}" if t.get("owner") else "👤待认领"
            deadline = f"📅{t['deadline']}" if t.get("deadline") else "📅无期限"
            lines.append(f"  {i}. {icon} {t['task'][:28]}")
            lines.append(f"      {owner} | {deadline}")
    else:
        lines.append("✅ 近期暂无待办")

    # 3天内将到期
    if upcoming:
        lines.append("")
        lines.append(f"⏰ 3天内将到期（{len(upcoming)}项）")
        for t in upcoming:
            days_left = (datetime.strptime(t["deadline"], "%Y-%m-%d").date() - today).days
            lines.append(f"  🟡 [{days_left}天后] {t['task'][:30]}")

    lines.append("")
    lines.append(f"📅 {today_display} {weekday} 加油！💪")
    lines.append("（回复完成+ID可标记任务，如：完成5）")

    return "\n".join(lines)

# =============================================
# 企业微信机器人推送
# =============================================
def send_wecom_message(content: str, webhook_url: str = None) -> bool:
    """通过企业微信机器人推送消息"""
    url = webhook_url or WECOM_WEBHOOK
    if not url:
        raise RuntimeError("未配置 WECOM_WEBHOOK 环境变量")

    import urllib.request, urllib.error

    max_len = 2000
    if len(content) > max_len:
        chunks = [content[i:i+max_len] for i in range(0, len(content), max_len)]
        for chunk in chunks:
            if not _send_wecom_text(chunk.strip(), url):
                return False
        return True

    return _send_wecom_text(content, url)

def _send_wecom_text(text: str, url: str) -> bool:
    """发送文本消息"""
    import urllib.request, urllib.error
    payload = {"msgtype": "text", "text": {"content": text}}
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                logger.info("企微推送成功")
                return True
            else:
                logger.error(f"企微推送失败: {result.get('errmsg')}")
                return False
    except Exception as e:
        logger.error(f"企微推送异常: {e}")
        return False

def send_daily_briefing(webhook_url: str = None) -> str:
    """生成并推送早会待办"""
    content = build_daily_briefing()
    url = webhook_url or WECOM_WEBHOOK
    if url:
        send_wecom_message(content, url)
        logger.info("早会推送完成")
    return content

# =============================================
# 主入口
# =============================================
def main():
    init_db()

    if len(sys.argv) < 2:
        print("=" * 44)
        print("  📋 企业微信会议助手 v3.0")
        print("=" * 44)
        print("用法:")
        print("  --add '内容'       添加并分析文本")
        print("  --audio file.m4a  录音转写+分析")
        print("  --daily            推送早会待办")
        print("  --query '关键词'   搜索历史会议")
        print("  --list             列出所有待办")
        print("  --today            查看今日待办")
        print("  --overdue          查看逾期")
        print("  --stats            查看本周统计")
        print("  --done <id>        标记完成")
        print("  --export           导出所有任务")
        print()
        print(build_daily_briefing())
        return

    cmd = sys.argv[1]

    if cmd == "--add":
        if len(sys.argv) < 3:
            print("错误: --add 需要文本内容"); sys.exit(1)
        text = sys.argv[2]
        logger.info(f"分析文本，长度={len(text)}字")
        analysis = extract_todos_from_text(text)
        mid = save_meeting(text, source="text", analysis=analysis)
        print(f"\n📋 分析结果（ID: {mid}）")
        print(f"标题: {analysis['title']}")
        print(f"摘要: {analysis['summary']}")
        print(f"待办（{len(analysis['todos'])}项）:")
        for i, t in enumerate(analysis["todos"], 1):
            dl = f"📅{t['deadline']}" if t.get("deadline") else "📅无期限"
            owner = f"👤{t['owner']}" if t.get("owner") else "👤待认领"
            print(f"  {i}. [{t['priority']}] {t['task']}")
            print(f"     {owner} | {dl}")

    elif cmd == "--audio":
        if len(sys.argv) < 3:
            print("错误: --audio 需要音频文件路径"); sys.exit(1)
        audio_file = sys.argv[2]
        if not os.path.exists(audio_file):
            print(f"错误: 文件不存在: {audio_file}"); sys.exit(1)
        sys.path.insert(0, BASE_DIR)
        from transcribe import transcribe_text_only
        logger.info(f"开始转写: {audio_file}")
        text = transcribe_text_only(audio_file)
        logger.info(f"转写完成: {len(text)}字")
        print(f"\n📝 转写内容（{len(text)}字）:\n{text[:300]}...")
        analysis = extract_todos_from_text(text, source="audio")
        mid = save_meeting(text, source="audio", analysis=analysis)
        print(f"\n📋 AI分析（ID: {mid}）")
        print(f"标题: {analysis['title']}")
        print(f"摘要: {analysis['summary']}")
        print(f"待办（{len(analysis['todos'])}项）:")
        for i, t in enumerate(analysis["todos"], 1):
            dl = f"📅{t['deadline']}" if t.get("deadline") else "📅无期限"
            owner = f"👤{t['owner']}" if t.get("owner") else "👤待认领"
            print(f"  {i}. [{t['priority']}] {t['task']}")
            print(f"     {owner} | {dl}")

    elif cmd == "--daily":
        logger.info("生成早会内容")
        content = send_daily_briefing()
        print(content)

    elif cmd == "--query":
        if len(sys.argv) < 3:
            print("错误: --query 需要搜索关键词"); sys.exit(1)
        query_text = " ".join(sys.argv[2:])
        logger.info(f"搜索会议: {query_text}")
        result = query_meetings(query_text)
        print(result)

    elif cmd == "--list":
        todos = get_pending_todos()
        print(f"📋 所有待办（{len(todos)}项）")
        print(format_todos_for_display(todos, "所有待办"))

    elif cmd == "--today":
        todos = get_today_todos()
        print(f"📅 近期待办（{len(todos)}项）")
        print(format_todos_for_display(todos, "近期待办"))

    elif cmd == "--overdue":
        todos = get_overdue_todos()
        print(f"⚠️ 逾期未完成（{len(todos)}项）")
        print(format_todos_for_display(todos, "逾期"))

    elif cmd == "--stats":
        stats = get_weekly_stats()
        print(f"📊 本周统计（{stats['week_start']} ~ {stats['today']}）")
        print(f"  📥 新增待办：{stats['new']} 项")
        print(f"  ✅ 已完成：{stats['done']} 项")
        print(f"  ⚠️ 当前逾期：{stats['overdue']} 项")
        print(f"  🔄 逾期已完成：{stats['overdue_done']} 项")
        if stats["new"] > 0:
            rate = int(stats["done"] / stats["new"] * 100)
            print(f"  📈 完成率：{rate}%")

    elif cmd == "--done":
        if len(sys.argv) < 3:
            print("错误: --done 需要任务ID"); sys.exit(1)
        tid = int(sys.argv[2])
        if mark_todo_done(tid):
            logger.info(f"任务 {tid} 已标记完成")
            print(f"✅ 任务 {tid} 已标记完成")
        else:
            print(f"❌ 任务 {tid} 不存在")

    elif cmd == "--export":
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.task, t.owner, t.deadline, t.priority, t.status,
                   m.meeting_title, t.created_at
            FROM todos t
            LEFT JOIN meetings m ON t.source_meeting_id = m.id
            ORDER BY t.status, t.deadline
        """)
        rows = cur.fetchall()
        conn.close()
        print(f"导出所有任务（{date.today()}）")
        print("ID | 状态 | 优先级 | 截止 | 负责人 | 任务")
        print("-" * 60)
        for r in rows:
            print(f"{r[0]} | {r[5]} | {r[4]} | {r[3] or '-'} | {r[2] or '-'} | {r[1][:40]}")

    else:
        print(f"未知命令: {cmd}"); sys.exit(1)

if __name__ == "__main__":
    main()
