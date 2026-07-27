#!/usr/bin/env python3
"""
来财AI客服 - v2.0 核心引擎
优化点：
1. 🔁 多轮对话记忆（Session Context）
2. 📝 意图识别升级（模糊匹配+上下文继承+否定识别）
3. ⏰ 智能留守模式（非工作时间自动切换）
4. 📝 对话日志自动记录（供后续优化分析）
5. 📸 图片识别提示
6. 🔔 库存预警主动推送

用法: python3 agent_v2.py（与 agent_extended.py 二选一）
"""

import re, sqlite3, os, sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ====== 路径 ======
_S = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(_S), "db", "laicai.db")
sys.path.insert(0, os.path.join(os.path.dirname(_S), "tools"))
from query import (search_products, get_product_by_id, check_stock,
    search_orders, format_product, format_product_list,
    format_orders, format_order_detail, get_stock_alerts)
import query_extended as qx

# ====== Session Context（多轮对话记忆）======
class SessionContext:
    """轻量级会话上下文管理器"""
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.order_candidates: list = []
        self.last_intent: str = ""
        self.last_product_keyword: str = ""
        self.confirmed_fields: Dict[str, Any] = {}

    def update(self, **kwargs):
        self.data.update(kwargs)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def remember_product(self, kw: str):
        """记住客户刚才提过的面料关键词"""
        self.last_product_keyword = kw

    def remember_intent(self, intent: str):
        self.last_intent = intent

    def set_field(self, key: str, value: Any):
        self.confirmed_fields[key] = value

    def get_field(self, key: str):
        return self.confirmed_fields.get(key)

    def clear_order(self):
        self.order_candidates = []
        self.confirmed_fields = {}

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "last_intent": self.last_intent,
            "last_product_keyword": self.last_product_keyword,
            "confirmed_fields": self.confirmed_fields,
        }

# 全局 Session（Web服务下建议改用 Redis/DB 存储）
_session_store: Dict[str, SessionContext] = {}

def get_session(session_id: str) -> SessionContext:
    if session_id not in _session_store:
        _session_store[session_id] = SessionContext()
    return _session_store[session_id]

def clear_session(session_id: str):
    if session_id in _session_store:
        _session_store[session_id] = SessionContext()

# ====== 对话日志记录 ======
def log_chat(session_id: str, user_msg: str, intent: str, reply: str):
    """记录每轮对话到数据库，用于后续优化分析"""
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_logs (user_msg, intent, reply, session_id, created_at)
            VALUES (?, ?, ?, ?, datetime('now', '+8 hours'))
        """, (user_msg, intent, reply, session_id))
        conn.commit()
        conn.close()
    except Exception:
        pass  # 日志失败不影响主流程

# ====== ⏰ 智能留守模式 ======
def is_off_hours() -> bool:
    """判断是否非工作时间（22:00-8:00）"""
    hour = datetime.now().hour
    return hour >= 22 or hour < 8

OFF_HOURS_MSG = (
    "🌙 您好，现在是非工作时间。\n"
    "━━━━━━━━━━━━━━\n"
    "有事请留言，明早 {hour} 点后第一时间回复您～\n\n"
    "紧急业务可拨打：138-XXXX-XXXX\n"
    "━━━━━━━━━━━━━━\n"
    "📋 常用功能（24小时自助）：\n"
    "• 回复【库存】+ 产品名 查库存\n"
    "• 回复【价格】+ 产品名 查价格\n"
    "• 回复【帮助】查看全部功能"
).format(hour=8)

# ====== 图片识别提示 ======
def handle_image(session_id: str) -> str:
    return (
        "📸 收到图片！\n\n"
        "目前支持：\n"
        "• 如需找相似面料，请描述图片中面料的【成分】【工艺】【花型】\n"
        "• 如需鉴定面料，可发图片给客服人工确认\n\n"
        "💡 示例：「找跟这张图类似的60s天丝印花」"
    )

# ====== 📝 意图识别 v2（升级版）======
class IntentEngine:
    """
    升级版意图识别：
    - 模糊匹配（口语化）
    - 上下文继承（连续问）
    - 否定识别（"不是/没有/换了"）
    - 多意图组合
    """

    # 意图关键词库（按优先级排列）
    INTENTS = {
        # === 核心业务 ===
        "price": {
            "keywords": ["价格", "多少钱", "单价", "报价", "怎么卖", "多少米", "一米", "一匹"],
            "context_triggers": [],  # 继承上轮的上下文
            "priority": 3
        },
        "stock": {
            "keywords": ["库存", "有货", "有吗", "现货", "还有多少", "能发", "有没有", "货呢"],
            "context_triggers": [],
            "priority": 3
        },
        "order_create": {
            "keywords": ["下单", "订", "要一批", "帮我订", "帮我下", "订一批", "拿货"],
            "context_triggers": [],
            "priority": 5
        },
        "order_query": {
            "keywords": ["订单", "货做好", "进度", "物流", "交期", "发货", "运到", "单号"],
            "context_triggers": [],
            "priority": 4
        },
        "recommend": {
            "keywords": ["推荐", "适合", "爆款", "热卖", "新款", "有什么好的"],
            "context_triggers": [],
            "priority": 2
        },
        "help": {
            "keywords": ["帮助", "怎么用", "功能", "你能做什么", "菜单", "有哪些"],
            "context_triggers": [],
            "priority": 1
        },
        # === 部门专用 ===
        "boss_dashboard": {
            "keywords": ["日报", "今日情况", "今日经营", "今天情况", "经营情况", "驾驶舱", "概况"],
            "context_triggers": [],
            "priority": 5
        },
        "sales_report": {
            "keywords": ["报表", "销售报告", "月度", "季度", "销售统计", "营业额"],
            "context_triggers": [],
            "priority": 5
        },
        "qc_report": {
            "keywords": ["质检", "质量报告", "合格", "次品", "验货"],
            "context_triggers": [],
            "priority": 5
        },
        "logistics": {
            "keywords": ["物流", "快递", "运到", "单号"],
            "context_triggers": [],
            "priority": 5
        },
        "production": {
            "keywords": ["生产进度", "排期", "进度", "到哪", "进行到哪"],
            "context_triggers": [],
            "priority": 5
        },
        "production_delay": {
            "keywords": ["延期", "逾期", "超时", "赶不上"],
            "context_triggers": [],
            "priority": 5
        },
        "inventory_alert": {
            "keywords": ["库存预警", "库存提醒", "库存不足", "缺货", "补货"],
            "context_triggers": [],
            "priority": 5
        },
        "pending_shipment": {
            "keywords": ["发货安排", "今天发什么", "哪些要发货", "待发货"],
            "context_triggers": [],
            "priority": 5
        },
        "complaints": {
            "keywords": ["客诉", "投诉", "质量投诉", "有问题"],
            "context_triggers": [],
            "priority": 5
        },
        "customer_profile": {
            "keywords": ["客户档案", "客户资料", "老客户", "客户历史"],
            "context_triggers": [],
            "priority": 5
        },
        "customer_followup": {
            "keywords": ["客户跟进", "跟进记录", "联系客户", "回访"],
            "context_triggers": [],
            "priority": 5
        },
        "vip_query": {
            "keywords": ["坯布", "加工费", "印花费", "染色费", "工艺费", "涂层费", "整理费", "VIP", "会员"],
            "context_triggers": [],
            "priority": 6
        },
        "stock_alert": {
            "keywords": ["库存预警", "库存告警", "缺货提醒"],
            "context_triggers": [],
            "priority": 4
        },
        "negation": {
            "keywords": ["不是", "没有", "换了", "另外", "其他", "别的", "不对", "不对"],
            "context_triggers": [],
            "priority": 10
        },
    }

    # 意图 → 处理函数映射
    INTENT_HANDLERS = {
        "price": "h_price",
        "stock": "h_stock",
        "order_create": "h_new_order",
        "order_query": "h_order",
        "recommend": "h_recommend",
        "help": "h_help",
        "boss_dashboard": "h_boss_dashboard",
        "sales_report": "h_sales_report",
        "qc_report": "h_qc_report",
        "logistics": "h_logistics",
        "production": "h_production",
        "production_delay": "h_production_delay",
        "inventory_alert": "h_inventory_alert",
        "pending_shipment": "h_pending_shipment",
        "complaints": "h_complaints",
        "customer_profile": "h_customer_profile",
        "customer_followup": "h_customer_followup",
        "vip_query": "h_vip",
        "stock_alert": "h_alert",
    }

    @classmethod
    def recognize(cls, text: str, session: SessionContext) -> str:
        """识别用户意图，支持上下文继承和否定"""
        text = text.strip()
        t_lower = text.lower()

        # === 否定识别 ===
        if any(k in text for k in ["不是", "没有", "换了", "另外", "其他", "别的", "不对"]):
            # 如果客户说"不是/没有"，清空面料记忆，切换为搜索模式
            if session.last_product_keyword:
                session.last_product_keyword = ""
            # 否则按普通搜索处理
            return "query"

        # === 上下文继承：连续问价格/库存 ===
        if session.last_intent in ("price", "stock") and session.last_product_keyword:
            # 客户没有明确新产品，继续用上次的
            if any(k in text for k in ["呢", "吗", "多少", "价格", "库存", "有"]):
                return session.last_intent  # 继承上轮意图

        # === 精确匹配 ===
        for intent_name, intent_def in cls.INTENTS.items():
            for kw in intent_def["keywords"]:
                if kw in t_lower or kw in text:
                    # 上下文继承
                    if intent_name in ("price", "stock") and not session.last_product_keyword:
                        # 提取面料关键词
                        kw_list = ["天丝", "全棉", "竹纤维", "棉麻", "提花", "交织", "天丝绢丝"]
                        for fabric in kw_list:
                            if fabric in text:
                                session.remember_product(fabric)
                                break
                    return intent_name

        # === 自由搜索兜底 ===
        return "query"

# ====== 简化版常量（从 agent_extended.py 引入核心模板）======
LOCKED = ("🔒 此功能仅对VIP会员开放\n\n"
    "━━━━━━━━━━━━━━\n"
    "请先告诉我您的【客户名称】验证VIP身份\n"
    "如：我是张总\n\n"
    "━━━━━━━━━━━━━━\n"
    "📋 VIP权益：\n"
    "• 坯布库存实时查询\n"
    "• 工厂加工费透明\n"
    "• 专属折扣\n\n"
    "咨询开通VIP请回复【VIP申请】")

TEMPLATE = ("━━━━━━━━━━━━━━\n"
    "📋 下单格式（请按以下填写）\n\n"
    "【面料】60s天丝 / 40s全棉 等\n"
    "【花型】如：蓝底白花 / 碎花\n"
    "【工艺】印花 / 染色\n"
    "【质量】A类 / B类 / 婴童级\n"
    "【客户】客户名称\n"
    "【地址】送货地址\n"
    "【米数】300米\n"
    "【备注】特别注意（如有）\n"
    "━━━━━━━━━━━━━━\n"
    "示例：\n"
    "面料：60s天丝\n"
    "花型：蓝底白花\n"
    "工艺：数码印花\n"
    "质量：A类\n"
    "客户：张总\n"
    "地址：南通叠石桥\n"
    "米数：500米\n"
    "直接发送即可自动创建订单～")

VIP_REGISTER = ("📋 VIP会员申请\n\n"
    "━━━━━━━━━━━━━━\n"
    "请联系客服开通VIP会员，享受：\n\n"
    "🔓 坯布库存实时查询\n"
    "🔓 工厂加工费透明\n"
    "💰 专属折扣优惠\n\n"
    "回复【姓名+公司+联系方式】即可申请开通")

# ====== 辅助函数（来自 agent_extended.py）======
def get_pid(t):
    m = re.search(r"FC-\d+", t)
    return m.group() if m else None

def get_oid(t):
    m = re.search(r"DD-\d{8}-\d{3}", t)
    return m.group() if m else None

def check_vip(t):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for kw in ["客户", "我是"]:
        idx = t.find(kw)
        if idx >= 0:
            name_part = t[idx+len(kw):].strip()
            name = name_part.lstrip(":： ").split()[0] if name_part else ""
            if name and len(name) >= 2:
                cur.execute("SELECT name,level,discount FROM vip_members WHERE name LIKE ?",
                    (f"%{name}%",))
                row = cur.fetchone()
                if row:
                    conn.close()
                    return {"Name": row[0], "level": row[1], "discount": row[2]}
    conn.close()
    return None

def parse_order(t):
    result = {}
    lines = [l.strip() for l in t.replace("\r\n", "\n").split("\n") if l.strip()]
    for line in lines:
        sep = None
        for s in ["\uff1a", ":"]:
            if s in line:
                sep = s
                break
        if not sep:
            continue
        idx = line.index(sep)
        key = line[:idx].strip()
        val = line[idx+1:].strip()
        if key in ["面料", "布", "产品"]:
            ps = search_products(val)
            if ps:
                result["product"] = ps[0]
        elif key in ["米数", "数量"]:
            m = re.search(r"\d+", val)
            if m:
                result["quantity"] = int(m.group())
        elif key in ["客户"]:
            result["customer"] = val
        elif key in ["地址"]:
            result["address"] = val
        elif key in ["花型", "色号"]:
            result["color"] = val
        elif key in ["质量"]:
            result["quality"] = val
        elif key in ["备注"]:
            result["note"] = val
    return result

def make_order(customer, pid, qty, address="", color="", quality="", note=""):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    cur.execute("SELECT COUNT(*) FROM orders WHERE id LIKE ?", (f"DD-{today}%",))
    seq = cur.fetchone()[0] + 1
    oid = "DD-%s-%03d" % (today, seq)
    cur.execute("SELECT name,price,lead_days FROM products WHERE id=?", (pid,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    pname, price, days = row
    amt = price * qty
    dl = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    parts = []
    if color: parts.append("花型:" + color)
    if quality: parts.append("质量:" + quality)
    if address: parts.append("地址:" + address)
    if note: parts.append("备注:" + note)
    remark = "; ".join(parts)
    cur.execute(
        "INSERT INTO orders (id,customer,product_id,quantity,price,amount,status,delivery,remark) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (oid, customer, pid, qty, price, amt, "待确认", dl, remark))
    conn.commit()
    conn.close()
    return oid, pname, price, qty, amt, dl

# ====== v2 处理器（优化版）======

def h_price_v2(t, session: SessionContext):
    """查价格 - 支持上下文继承"""
    pid = get_pid(t)
    if pid:
        p = get_product_by_id(pid)
        if p:
            return "💰 %s\n单价：¥%s/米\n起订量：%s米\n报价有效期：3天" % (p[1], p[9], p[10])

    # 提取面料关键词
    kw = None
    kw_list = ["天丝", "全棉", "竹纤维", "棉麻", "提花", "交织", "天丝绢丝", "棉天丝", "竹棉"]
    for fabric in kw_list:
        if fabric in t:
            kw = fabric
            session.remember_product(fabric)
            break

    # 如果没提取到，用上次的
    if not kw:
        kw = session.last_product_keyword

    if kw:
        ps = search_products(kw)
        if ps:
            return "💰 价格查询结果（%s）：\n" % kw + "\n".join(
                "- %s：¥%s/米 | 起订%s米" % (p[1], p[6], p[7]) for p in ps[:5])
        return "未找到与「%s」相关的产品" % kw

    return "请告诉我要查哪个产品的价格，如：'60s天丝印花多少钱'"

def h_stock_v2(t, session: SessionContext):
    """查库存 - 支持上下文继承"""
    pid = get_pid(t)
    if pid:
        p = get_product_by_id(pid)
        if p:
            se = "🟢充足" if p[11] > 5000 else "🟡偏少" if p[11] > 1000 else "🔴紧张" if p[11] > 0 else "⚫缺货"
            return "📦 %s\n库存：%s %s米\n交期：%s天" % (p[1], se, p[11], p[12])

    # 提取面料关键词
    kw = None
    kw_list = ["天丝", "全棉", "竹纤维", "棉麻", "提花", "交织", "天丝绢丝", "棉天丝", "竹棉"]
    for fabric in kw_list:
        if fabric in t:
            kw = fabric
            session.remember_product(fabric)
            break

    if not kw:
        kw = session.last_product_keyword

    if kw:
        rs = check_stock(kw)
        if rs:
            return "📦 库存查询结果（%s）：\n" % kw + "\n".join(
                "- %s：%s %s米 | 交期%s天" % (r["name"], r["status"], r["stock"], r["lead_days"]) for r in rs[:5])
        return "未找到与「%s」相关的产品" % kw

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*),SUM(stock) FROM products")
    cnt, tot = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM products WHERE stock<1000")
    low = cur.fetchone()[0]
    conn.close()
    return "📦 库存总览\n━━━━━━━━━━━━━━\n产品总数：%d款\n总库存：约%s米\n⚠️ 库存紧张：%d款\n\n请告诉我要查哪个产品，如：'60s天丝有货吗'" % (cnt, tot or 0, low)

def h_new_order_v2(t, session: SessionContext):
    """下单 - 支持多轮补全"""
    info = parse_order(t)
    p = info.get("product")
    qty = info.get("quantity")
    customer = info.get("customer")
    address = info.get("address")
    color = info.get("color")
    quality = info.get("quality")
    note = info.get("note")

    # 上下文补全
    if not p and session.last_product_keyword:
        ps = search_products(session.last_product_keyword)
        if ps:
            p = ps[0]

    missing = []
    if not p: missing.append("【面料】")
    if not qty: missing.append("【米数】")
    if not customer: missing.append("【客户】")
    if not address: missing.append("【地址】")

    if missing:
        lines = ["📝 订单信息（请补全以下内容）\n━━━━━━━━━━━━━━"]
        if p: lines.append("✅ 面料：%s" % p[1])
        else: lines.append("⬜ 面料：未填写（请告诉我您要什么面料）")
        if qty: lines.append("✅ 米数：%s米" % qty)
        else: lines.append("⬜ 米数：未填写")
        if customer: lines.append("✅ 客户：%s" % customer)
        else: lines.append("⬜ 客户：未填写")
        if address: lines.append("✅ 地址：%s" % address)
        else: lines.append("⬜ 地址：未填写")
        if color: lines.append("✅ 花型：%s" % color)
        if quality: lines.append("✅ 质量：%s" % quality)
        if note: lines.append("✅ 备注：%s" % note)
        lines.append("━━━━━━━━━━━━━━")
        lines.append("缺少：%s\n" % " / ".join(missing))
        lines.append(TEMPLATE)
        return "\n".join(lines)

    pid = p[0]
    pname = p[1]
    price = p[6] if len(p) == 11 else p[9]
    stock = p[8] if len(p) == 11 else p[11]
    if stock < qty:
        return "⚠️ %s 当前库存仅 %s米，不足 %s米" % (pname, stock, qty)
    r = make_order(customer, pid, qty, address or "", color or "", quality or "", note or "")
    if not r:
        return "创建订单失败，请重试"
    oid, pn, pr, q, amt, dl = r
    details = []
    if color: details.append("花型：" + color)
    if quality: details.append("质量：" + quality)
    dstr = "\n".join(details)
    # 清空会话中的订单信息
    session.clear_order()
    return ("✅ 订单创建成功！\n\n━━━━━━━━━━━━━━\n"
            "📋 订单号：%s\n👤 客户：%s\n📦 产品：%s\n🔢 数量：%s米\n"
            "💰 总价：¥%.2f\n📅 交期：%s\n%s\n━━━━━━━━━━━━━━\n"
            "请尽快确认定金以锁定订单～") % (
            oid, customer, pn, q, amt, dl, (dstr + "\n" if dstr else ""))

def h_help_v2():
    return ("🤖 来财AI客服 v2.0 - 功能一览\n\n"
        "━━━ 常用功能 ━━━\n\n"
        "🔍 查价格（支持连续追问）\n"
        "   「60s天丝多少钱」\n"
        "   「那40s全棉呢」← 自动继承上文\n\n"
        "📦 查库存\n"
        "   「FC-001有货吗」\n\n"
        "📋 查订单\n"
        "   「我的订单」\n\n"
        "🛒 下订单（支持分次补全）\n"
        "   「我要订60s天丝，500米」\n"
        "   「客户是张总」\n\n"
        "━━━ 部门专用 ━━━\n\n"
        "📊 老板驾驶舱    →「今日经营情况」\n"
        "🔍 质检报告      →「最近质检情况」\n"
        "🚚 物流查询      →「DD-20250601-001物流」\n"
        "🏭 生产进度      →「DD-20250601-001进度」\n"
        "📦 库存预警      →「库存需要补货吗」\n"
        "🚢 发货安排      →「有哪些订单要发货」\n"
        "👤 客户档案      →「张总的客户档案」\n\n"
        "━━━ VIP专属 ━━━\n"
        "回复【我是张总】验证VIP身份\n"
        "坯布库存 · 加工费报价 · 专属折扣\n\n"
        "💡 提示：发送【帮助】随时查看本菜单")

# ====== 路由分发（兼容 agent_extended.py 的其他 handler）======
def process_v2(text: str, session_id: str = "default") -> str:
    """v2 主入口"""
    session = get_session(session_id)
    text = text.strip()

    if not text:
        return "您好！请告诉我您需要什么帮助~\n\n回复【帮助】查看全部功能"

    # === 留守模式 ===
    if is_off_hours():
        return OFF_HOURS_MSG

    # === 图片识别 ===
    if any(text.startswith(k) for k in ["[图片]", "[image]", "📷", "image:"]):
        return handle_image(session_id)

    # === VIP 相关 ===
    vip = check_vip(text)
    if vip and any(k in text for k in ["坯布", "坯布价格", "坯布库存"]):
        return h_vip_greycloth(text, vip)
    if vip and any(k in text for k in ["印花", "染色", "涂层", "整理", "工艺", "加工"]):
        return h_vip_processing(text, vip)
    if vip and any(k in text for k in ["VIP名单", "vip名单", "会员名单"]):
        return h_vip_list()
    if any(k in text for k in ["VIP申请", "申请VIP", "开通VIP"]):
        return VIP_REGISTER
    if any(k in text for k in ["VIP", "vip"]) and not vip:
        return "请先告诉我您的【客户名称】验证VIP身份，如：「我是张总」"

    # === VIP 锁定功能 ===
    if any(k in text for k in ["坯布", "加工费", "印花费", "染色费"]):
        if not vip:
            return LOCKED

    # === 意图识别 v2 ===
    intent = IntentEngine.recognize(text, session)
    session.remember_intent(intent)

    # === 上下文继承 ===
    if intent in ("price", "stock") and session.last_product_keyword:
        if not any(k in text for k in ["天丝", "全棉", "竹", "棉麻", "提花", "交织"]):
            # 客户在连续追问，沿用上次的关键词
            if intent == "price":
                return h_price_v2(session.last_product_keyword, session)
            elif intent == "stock":
                return h_stock_v2(session.last_product_keyword, session)

    # === 分发处理 ===
    handler_map = {
        "price": lambda: h_price_v2(text, session),
        "stock": lambda: h_stock_v2(text, session),
        "order_create": lambda: h_new_order_v2(text, session),
        "order_query": lambda: h_order(text),
        "recommend": lambda: h_recommend(text),
        "help": h_help_v2,
        "boss_dashboard": lambda: h_boss_dashboard(text),
        "sales_report": lambda: h_sales_report(text),
        "qc_report": lambda: h_qc_report(text),
        "logistics": lambda: h_logistics(text),
        "production": lambda: h_production(text),
        "production_delay": lambda: h_production_delay(text),
        "inventory_alert": lambda: h_inventory_alert(text),
        "pending_shipment": lambda: h_pending_shipment(text),
        "complaints": lambda: h_complaints(text),
        "customer_profile": lambda: h_customer_profile(text),
        "customer_followup": lambda: h_customer_followup(text),
        "stock_alert": lambda: h_alert(),
        "vip_query": lambda: LOCKED if not check_vip(text) else h_vip_processing(text, check_vip(text)),
        "negation": lambda: h_query_v2(text, session),
        "query": lambda: h_query_v2(text, session),
    }

    if intent in handler_map:
        reply = handler_map[intent]()
        log_chat(session_id, text, intent, reply)
        return reply

    # 兜底查询
    reply = h_query_v2(text, session)
    log_chat(session_id, text, "query", reply)
    return reply

# ====== 兼容 agent_extended.py 的原有函数签名 ======
# 保留原 agent_extended.py 的处理函数签名（用于兼容其他模块）
def h_price(t): return h_price_v2(t, get_session("default"))
def h_stock(t): return h_stock_v2(t, get_session("default"))
def h_new_order(t): return h_new_order_v2(t, get_session("default"))
def h_help(): return h_help_v2()

def h_order(t):
    oid = get_oid(t)
    if oid:
        return format_order_detail(get_order_detail_by_oid(oid))
    orders = search_orders()
    return format_orders(orders[:5] if orders else [])

def get_order_detail_by_oid(oid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, p.name as product_name, p.spec
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE o.id = ?
    """, (oid,))
    result = cur.fetchone()
    conn.close()
    return result

def h_recommend(t):
    kw = next((w for w in ["天丝","全棉","竹","提花","交织"] if w in t), "印花")
    ps = search_products(kw)
    if not ps:
        return "暂无相关推荐"
    return "🌟 为您推荐 %s 系列：\n" % kw + "\n".join(
        "- %s | ¥%s/米 | 🟢%s米" % (p[1], p[6], p[8]) for p in ps[:3]
    ) + "\n\n回复产品编号查看详情，如：FC-001"

def h_alert():
    alerts = get_stock_alerts()
    if not alerts:
        return "✅ 目前所有产品库存充足，无告警"
    return "⚠️ 库存告警 (%d款)\n" % len(alerts) + "\n".join(
        "- %s：%s" % (a[1], a[3]) for a in alerts[:10])

def h_query_v2(t, session: SessionContext):
    pid = get_pid(t)
    if pid:
        p = get_product_by_id(pid)
        if p:
            return format_product(p)
    k = t
    for sw in ["请问","问一下","帮我","查","一下","看看","的"]:
        k = k.replace(sw, " ")
    k = " ".join(k.split())
    if k:
        ps = search_products(k)
        if ps:
            session.remember_product(k)
            return format_product_list(ps)
    return "未找到相关内容，请换个关键词试试~\n\n回复【帮助】查看全部功能"

def h_boss_dashboard(t):
    try:
        d = qx.get_boss_dashboard_v2()  # v2 带同比数据
        return qx.format_boss_dashboard_v2(d)
    except AttributeError:
        d = qx.get_boss_dashboard()
        return qx.format_boss_dashboard(d)

def h_sales_report(t): return qx.get_sales_report() and qx.format_sales_report(qx.get_sales_report())
def h_qc_report(t): return "🔍 质检报告\n\n" + qx.format_qc_report(qx.get_quality_checks(limit=20))
def h_logistics(t):
    oid_m = re.search(r'(DD-\d+-\d+)', t)
    if oid_m:
        records = qx.get_logistics(order_id=oid_m.group(1))
    else:
        records = qx.get_logistics()
    return f"🚚 物流查询\n\n{qx.format_logistics(records)}"
def h_production(t):
    oid_m = re.search(r'(DD-\d+-\d+)', t)
    if not oid_m:
        return "请告诉我订单号，如：DD-20260525-001的生产进度"
    stages = qx.get_production_progress(order_id=oid_m.group(1))
    return qx.format_production(oid_m.group(1), stages)
def h_production_delay(t):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, customer, status, delivery FROM orders
        WHERE status IN ('生产中','已确认')
        AND delivery < date('now', '+3 days')
        AND delivery < date('now')
        ORDER BY delivery
    """)
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "✅ 暂无即将延期或已延期的订单"
    return "⚠️ 即将延期/已延期订单\n" + "\n".join(
        f"  🔴 {r['id']} | {r['customer']} | 交期:{r['delivery']}" for r in rows)

def h_pending_shipment(t):
    recs = qx.get_pending_shipments()
    return qx.format_pending_shipments(recs)

def h_inventory_alert(t):
    prods = qx.get_inventory_alerts()
    return qx.format_inventory_alerts(prods)

def h_complaints(t):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM quality_checks
        WHERE result = '不合格' OR notes LIKE '%投诉%' OR notes LIKE '%客诉%'
        ORDER BY created_at DESC LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "✅ 暂无质量投诉记录"
    return "🔴 质量投诉记录\n" + "\n".join(
        f"  ❌ {r['check_date']} | {r['product_id']} | {r['defect_type']}" for r in rows)

def h_customer_followup(t):
    m = re.search(r'([^\s]{2,6}?)(?:的)?(?:客户)?(档案|资料)?$', t)
    name = m.group(1) if m else None
    recs = qx.get_customer_followups(customer=name)
    return qx.format_followups(recs, customer_name=name)

def h_customer_profile(t):
    name_part = t.replace('客户档案','').replace('客户资料','').replace('档案','').replace('资料','').replace('的','').strip()
    name = name_part if name_part and len(name_part) >= 2 else None
    if not name:
        return "请告诉我要查哪个客户，如：'张总的客户档案'"
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.created_at, o.amount as total_price, o.status,
               p.name as product_name, o.quantity
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.customer LIKE ?
        ORDER BY o.created_at DESC LIMIT 10
    """, (f"%{name}%",))
    orders = cur.fetchall()
    recs = qx.get_customer_followups(customer=name)
    conn.close()
    if not orders:
        return f"未找到客户「{name}」的订单记录"
    total_amount = sum(float(o['total_price']) for o in orders)
    total_qty = sum(int(o['quantity']) for o in orders)
    order_list = '\n'.join([
        f"  • {o['id']} | {o['product_name']}×{o['quantity']}米 | ¥{o['total_price']} | {o['status']}"
        for o in orders
    ])
    followup_text = qx.format_followups(recs, customer_name=name)
    return (f"👤 客户档案 - {name}\n\n━━━━━━━━━━━━━━\n"
            f"📊 累计采购\n  总订单: {len(set(o['id'] for o in orders))}单\n"
            f"  总金额: ¥{total_amount:,.0f}\n  总米数: {total_qty}米\n\n━━━━━━━━━━━━━━\n"
            f"📋 订单记录\n{order_list}\n\n━━━━━━━━━━━━━━\n"
            f"{followup_text}")

def h_vip_greycloth(t, vip):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    stop = ["坯布", "库存", "价格", "多少钱", "有吗", "帮我", "客户", "我是"]
    k = t
    for sw in stop:
        k = k.replace(sw, " ").strip()
    k = k.replace(vip["Name"], " ")
    k = " ".join(k.split())
    if k and len(k) >= 2:
        cur.execute(
            "SELECT id,name,spec,composition,price,stock FROM greycloth "
            "WHERE name LIKE ? OR spec LIKE ? OR composition LIKE ? LIMIT 10",
            (f"%{k}%", f"%{k}%", f"%{k}%"))
    else:
        cur.execute("SELECT id,name,spec,composition,price,stock FROM greycloth LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return f"未找到相关坯布，{vip['Name']} {vip['level']}"
    d = vip["discount"]
    lines = [f"🏭 坯布库存（{vip['Name']} · {vip['level']} · {int(d*100)}折）\n━━━━━━━━━━━━━━"]
    for r in rows:
        ori = r[4]
        vip_price = ori * d
        se = "🟢" if r[5] > 5000 else "🟡" if r[5] > 1000 else "🔴" if r[5] > 0 else "⚫"
        lines.append(f"{r[0]} {r[1]} {r[2]}")
        lines.append(f"  成分：{r[3]} | 库存：{se}{r[5]}米")
        if d < 1.0:
            lines.append(f"  原价：¥{ori}/米 → VIP价：¥{vip_price:.2f}/米")
        else:
            lines.append(f"  单价：¥{ori}/米")
    lines.append("\n回复坯布编号查看详情，如：GC-001")
    return "\n".join(lines)

def h_vip_processing(t, vip):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if "印花" in t:
        cur.execute("SELECT id,name,category,price,unit,min_order,lead_days FROM processing WHERE category LIKE '%印花%'")
    elif "染色" in t:
        cur.execute("SELECT id,name,category,price,unit,min_order,lead_days FROM processing WHERE category LIKE '%染色%'")
    elif "整理" in t or "涂层" in t:
        cur.execute("SELECT id,name,category,price,unit,min_order,lead_days FROM processing WHERE category LIKE '%整理%'")
    elif "功能" in t:
        cur.execute("SELECT id,name,category,price,unit,min_order,lead_days FROM processing WHERE category LIKE '%功能%'")
    else:
        cur.execute("SELECT id,name,category,price,unit,min_order,lead_days FROM processing")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return f"未找到相关工艺，{vip['Name']}"
    cats = {}
    for r in rows:
        cat = r[2]
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(r)
    lines = [f"🏭 加工费报价（{vip['Name']} · {vip['level']}）\n━━━━━━━━━━━━━━"]
    for cat, items in cats.items():
        lines.append(f"\n【{cat}】")
        for r in items:
            lines.append(f"  {r[0]} {r[1]}")
            lines.append(f"  费用：¥{r[3]}/{r[4]} | 起订：{r[5]}米 | 周期：{r[6]}天")
    return "\n".join(lines)

def h_vip_list():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name,level,company,credit_limit FROM vip_members WHERE status='正常'")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "暂无VIP名单"
    return "👑 VIP会员名单\n━━━━━━━━━━━━━━\n" + "\n".join(
        f"• {r[0]} · {r[1]}\n  {r[2]} | 额度：{r[3]}万" for r in rows
    )

# ====== process 入口（兼容原 API）======
def process(text: str, session_id: str = "default") -> str:
    """主入口：支持 session_id 实现多用户隔离"""
    return process_v2(text, session_id)

if __name__ == "__main__":
    print("=" * 50)
    print("来财AI客服 v2.0 - 核心引擎测试")
    print("=" * 50)

    tests = [
        ("60s天丝多少钱", "s1"),
        ("那40s全棉呢", "s1"),  # 上下文继承
        ("帮我查库存", "s2"),
        ("我要订500米天丝", "s3"),
        ("客户是张总", "s3"),   # 多轮补全
        ("今日经营情况", "s4"),
        ("帮助", "s5"),
    ]

    for msg, sid in tests:
        print(f"\nQ [{sid}]: {msg}")
        print(f"A: {process(msg, sid)}")
