#!/usr/bin/env python3
"""来财AI客服 v7 - 含VIP功能"""
import re, sqlite3
from datetime import datetime, timedelta

import os; _s = os.path.dirname(os.path.abspath(__file__)); DB = os.path.join(os.path.dirname(_s), "db", "laicai.db")
TOOLS = os.path.dirname(os.path.abspath(__file__))
import sys; _s = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(_s), "tools"))
from query import (search_products, get_product_by_id, check_stock, get_order_detail,
    search_orders, format_product, format_product_list, format_orders,
    format_order_detail, get_stock_alerts)

# ========== 常量 ==========
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

# ========== 工具函数 ==========
def get_pid(t):
    m = re.search(r"FC-\d+", t)
    return m.group() if m else None

def get_oid(t):
    m = re.search(r"DD-\d{8}-\d{3}", t)
    return m.group() if m else None

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

# ========== VIP功能 ==========
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
                    return {"name": row[0], "level": row[1], "discount": row[2]}
    conn.close()
    return None

def is_vip_query(t):
    return any(k in t for k in ["坯布", "加工费", "印花费", "染色费", "工艺费", "涂层费", "整理费"])

def h_vip_greycloth(t):
    vip = check_vip(t)
    if not vip:
        return LOCKED
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # 提取坯布关键词：去掉坯布相关词+VIP名字
    stop = ["坯布", "库存", "价格", "多少钱", "有吗", "帮我", "客户", "我是"]
    k = t
    for sw in stop:
        k = k.replace(sw, " ").strip()
    # 也去掉VIP名字
    k = k.replace(vip["name"], " ")
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
        return f"未找到相关坯布，{vip['name']} {vip['level']}"
    d = vip["discount"]
    lines = [
        f"🏭 坯布库存（{vip['name']} · {vip['level']} · {int(d*100)}折）\n",
        "━━━━━━━━━━━━━━"
    ]
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

def h_vip_processing(t):
    vip = check_vip(t)
    if not vip:
        return LOCKED
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # 从消息中去掉VIP名字再判断工艺类型
    stop = [vip["name"], "客户", "我是"]
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
        return f"未找到相关工艺，{vip['name']}"
    cats = {}
    for r in rows:
        cat = r[2]
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(r)
    lines = [
        f"🏭 加工费报价（{vip['name']} · {vip['level']}）\n",
        "━━━━━━━━━━━━━━"
    ]
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
    lines = ["👑 VIP会员名单\n━━━━━━━━━━━━━━"]
    for r in rows:
        lines.append(f"• {r[0]} · {r[1]}")
        lines.append(f"  {r[2]} | 额度：{r[3]}万")
    return "\n".join(lines)

# ========== 普通查询 ==========
def h_price(t):
    pid = get_pid(t)
    if pid:
        p = get_product_by_id(pid)
        if p:
            return "💰 %s\n单价：¥%s/米\n起订量：%s米\n报价有效期：3天" % (p[1], p[9], p[10])
    k = re.sub(r"[价格多少钱的单]", "", t).strip()
    if k:
        ps = search_products(k)
        if ps:
            return "💰 价格查询结果：\n" + "\n".join(
                "- %s：¥%s/米 | 起订%s米" % (p[1], p[6], p[7]) for p in ps[:5])
    return "请告诉我要查哪个产品的价格，如：'60s天丝印花多少钱'"

def h_stock(t):
    pid = get_pid(t)
    if pid:
        p = get_product_by_id(pid)
        if p:
            se = "🟢充足" if p[11] > 5000 else "🟡偏少" if p[11] > 1000 else "🔴紧张" if p[11] > 0 else "⚫缺货"
            return "📦 %s\n库存：%s %s米\n交期：%s天" % (p[1], se, p[11], p[12])
    stop = ["库存", "有", "货", "吗", "请", "告诉", "我", "要", "查", "哪", "个", "的", "帮", "看", "看看", "查查"]
    k = t
    for sw in stop:
        k = k.replace(sw, " ")
    k = " ".join(k.split()).strip()
    if len(k) >= 2:
        rs = check_stock(k)
        if rs:
            return "📦 库存查询结果：\n" + "\n".join(
                "- %s：%s %s米 | 交期%s天" % (r["name"], r["status"], r["stock"], r["lead_days"]) for r in rs[:5])
        return "未找到与'%s'相关的产品" % k
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*),SUM(stock) FROM products")
    cnt, tot = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM products WHERE stock<1000")
    low = cur.fetchone()[0]
    conn.close()
    return "📦 库存总览\n━━━━━━━━━━━━━━\n产品总数：%d款\n总库存：约%s米\n⚠️ 库存紧张：%d款\n\n请告诉我要查哪个产品，如：'60s天丝有货吗'" % (cnt, tot or 0, low)

def h_order(t):
    oid = get_oid(t)
    if oid:
        return format_order_detail(get_order_detail(oid))
    orders = search_orders()
    return format_orders(orders[:5] if orders else [])

def h_new_order(t):
    info = parse_order(t)
    p = info.get("product")
    qty = info.get("quantity")
    customer = info.get("customer")
    address = info.get("address")
    color = info.get("color")
    quality = info.get("quality")
    note = info.get("note")
    missing = []
    if not p: missing.append("【面料】")
    if not qty: missing.append("【米数】")
    if not customer: missing.append("【客户】")
    if not address: missing.append("【地址】")
    if missing:
        lines = ["📝 订单信息（请补全以下内容）\n━━━━━━━━━━━━━━"]
        if p: lines.append("✅ 面料：%s" % p[1])
        if qty: lines.append("✅ 米数：%s米" % qty)
        if customer: lines.append("✅ 客户：%s" % customer)
        if address: lines.append("✅ 地址：%s" % address)
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
    return ("✅ 订单创建成功！\n\n━━━━━━━━━━━━━━\n"
            "📋 订单号：%s\n👤 客户：%s\n📦 产品：%s\n🔢 数量：%s米\n"
            "💰 总价：¥%.2f\n📅 交期：%s\n%s\n━━━━━━━━━━━━━━\n"
            "请尽快确认定金以锁定订单～") % (
            oid, customer, pn, q, amt, dl, (dstr + "\n" if dstr else ""))

def h_recommend(t):
    kw = next((w for w in ["天丝","全棉","竹","提花","交织"] if w in t), "印花")
    ps = search_products(kw)
    if not ps:
        return "暂无相关推荐"
    return "🌟 为您推荐 %s 系列：\n" % kw + "\n".join(
        "- %s | ¥%s/米 | 🟢%s米" % (p[1], p[6], p[8]) for p in ps[:3]
    ) + "\n\n回复产品编号查看详情，如：FC-001"

def h_help():
    return ("🤖 来财AI客服 - 功能一览\n\n"
        "━━━ 常用功能 ━━━\n\n"
        "🔍 查价格\n"
        "   \"60s天丝多少钱\"\n\n"
        "📦 查库存\n"
        "   \"FC-001有货吗\"\n\n"
        "📋 查订单\n"
        "   \"我的订单\"\n\n"
        "🛒 下订单\n"
        "   发送面料+花型+工艺+质量+客户+地址+米数\n\n"
        "🔒 VIP专属\n"
        "   坯布库存 · 加工费报价\n"
        "   回复【我是张总】验证VIP身份\n\n"
        "⚠️ 库存预警")

def h_alert():
    alerts = get_stock_alerts()
    if not alerts:
        return "✅ 目前所有产品库存充足，无告警"
    return "⚠️ 库存告警 (%d款)\n" % len(alerts) + "\n".join(
        "- %s：%s" % (a[1], a[3]) for a in alerts[:10])

def h_query(t):
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
        return format_product_list(ps)
    return "请告诉我您要查询的产品名称或编号"

# ========== 路由 ==========
def process(t):
    t = t.strip()
    if not t:
        return "您好！请告诉我您需要什么帮助~"
    t2 = t.lower()
    # VIP专属路由（优先）
    if is_vip_query(t) or any(k in t.lower() for k in ["印花", "染色", "涂层", "整理", "工艺"]):
        vip = check_vip(t)
        if vip:
            if any(k in t for k in ["坯布", "坯布价格", "坯布库存"]):
                return h_vip_greycloth(t)
            return h_vip_processing(t)
        return LOCKED
    if any(k in t for k in ["VIP名单", "vip名单", "会员名单"]):
        return h_vip_list()
    if any(k in t for k in ["VIP申请", "申请VIP", "开通VIP"]):
        return h_vip_register()
    # 普通路由
    if any(p in t2 for p in ["面料","花型","色号","工艺","质量","客户","地址","米数","备注"]):
        return h_new_order(t)
    if any(p in t2 for p in ["库存预警","库存告警","缺货"]):
        return h_alert()
    if any(p in t2 for p in ["有货","有没有","现货","多少米","还有多少","能发"]):
        return h_stock(t)
    if any(p in t2 for p in ["价格","多少钱","单价","报价"]):
        return h_price(t)
    if any(p in t2 for p in ["订单","货做好","进度","发货","物流","交期"]):
        return h_order(t)
    if any(p in t2 for p in ["推荐","适合","爆款"]):
        return h_recommend(t)
    if any(p in t2 for p in ["帮助","怎么用","功能"]):
        return h_help()
    if any(p in t2 for p in ["订","下单","下一单","帮我订","要一批"]):
        return h_new_order(t)
    return h_query(t)

if __name__ == "__main__":
    tests = [
        "面料：60s天丝\n花型：蓝底白花\n工艺：数码印花\n质量：A类\n客户：张总\n地址：南通\n米数：500米",
        "60s天丝多少钱",
        "FC-001有货吗",
        "帮我查一下订单",
        "坯布",
        "我是张总 坯布",
        "印花加工费",
        "有什么推荐",
        "怎么用",
        "库存预警",
    ]
    for msg in tests:
        print("\nQ:", msg.replace("\n", " | "))
        print("A:", process(msg))
