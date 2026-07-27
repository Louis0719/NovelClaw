#!/usr/bin/env python3
"""来财AI客服 - 扩展查询模块（各部门数据查询）"""
import sqlite3
from datetime import datetime

import os; _s = os.path.dirname(os.path.abspath(__file__)); DB = os.path.join(os.path.dirname(_s), "db", "laicai.db")

def _conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ======== 老板驾驶舱 ========
def get_boss_dashboard():
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = today[:7] + '-01'
    conn = _conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM orders WHERE created_at LIKE ?", (today+'%',))
    today_data = cur.fetchone()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM orders WHERE created_at >= ?", (month_start,))
    month_data = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM orders WHERE status IN ('待确认','已确认','生产中','排产中','染整中')")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products WHERE stock < 1000")
    alerts = cur.fetchone()[0]

    cur.execute("""
        SELECT p.name, p.id, COALESCE(SUM(o.quantity),0) as total_qty, COUNT(o.id) as cnt
        FROM products p
        LEFT JOIN orders o ON o.product_id = p.id AND o.created_at >= ? AND o.status NOT IN ('已取消')
        GROUP BY p.id ORDER BY total_qty DESC LIMIT 5
    """, (month_start,))
    hot = cur.fetchall()

    cur.execute("SELECT COUNT(*), SUM(CASE WHEN result='合格' THEN 1 ELSE 0 END) FROM quality_checks WHERE created_at >= ?", (month_start,))
    qc_data = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM quality_checks WHERE result='待处理'")
    qc_pending = cur.fetchone()[0]

    conn.close()

    qc_rate = f"{qc_data[1]*100/qc_data[0]:.1f}%" if qc_data[0] and qc_data[0] > 0 else "暂无数据"

    return {
        'today_orders': today_data[0],
        'today_amount': today_data[1],
        'month_orders': month_data[0],
        'month_amount': month_data[1],
        'pending': pending,
        'stock_alerts': alerts,
        'hot': hot,
        'qc_rate': qc_rate,
        'qc_pending': qc_pending,
    }

def format_boss_dashboard(d):
    today_str = datetime.now().strftime('%Y-%m-%d')
    hot_lines = '\n'.join([
        f"  • {r['name']}({r['id']}) {int(r['total_qty'])}米/{r['cnt']}单"
        for r in d['hot'] if r['total_qty'] and r['total_qty'] > 0
    ]) or "  暂无成交数据"
    return f"""📊 来财经营驾驶舱 - {today_str}

━━━━━━━━━━━━━━━
📈 今日
  成交订单: {d['today_orders']}单
  成交金额: ¥{d['today_amount']:,.0f}

📈 本月累计
  成交订单: {d['month_orders']}单
  成交金额: ¥{d['month_amount']:,.0f}

━━━━━━━━━━━━━━━
🚚 进行中订单: {d['pending']}单
⚠️ 库存预警: {d['stock_alerts']}款
🔍 待处理质检: {d['qc_pending']}条
🔬 本月质检合格率: {d['qc_rate']}

━━━━━━━━━━━━━━━
🔥 本月热销产品
{hot_lines}
"""

# ======== 质检 ========
def get_quality_checks(product_id=None, result=None, limit=20):
    conn = _conn()
    cur = conn.cursor()
    sql = "SELECT * FROM quality_checks WHERE 1=1"
    params = []
    if product_id:
        sql += " AND product_id=?"
        params.append(product_id)
    if result:
        sql += " AND result=?"
        params.append(result)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def format_qc_report(checks):
    if not checks:
        return "暂无质检记录"
    lines = []
    for c in checks:
        icon = {"合格": "✅", "不合格": "❌", "待处理": "⏳"}.get(c['result'], "❓")
        defect = f"\n    ⚠️ {c['defect_type']}: {c['defect_meters']}米" if c['defect_meters'] else ""
        lines.append(f"{icon} {c['check_date']} | {c['product_id']} | {c['check_type']} | {c['result']} | {c['inspector']}{defect}")
    return '\n'.join(lines)

# ======== 物流 ========
def get_logistics(order_id=None, status=None):
    conn = _conn()
    cur = conn.cursor()
    sql = "SELECT * FROM logistics WHERE 1=1"
    params = []
    if order_id:
        sql += " AND order_id=?"
        params.append(order_id)
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def format_logistics(records):
    if not records:
        return "暂无物流记录"
    icons = {"待发货": "⏳", "已发出": "📦", "运输中": "🚚", "已签收": "✅"}
    lines = []
    for r in records:
        icon = icons.get(r['status'], "❓")
        lines.append(f"{icon} {r['order_id']} | {r['express_company']} | {r['status']} | 收件:{r['receiver']}")
        if r['tracking_no']:
            lines.append(f"   单号: {r['tracking_no']}")
    return '\n'.join(lines)

# ======== 生产进度 ========
def get_production_progress(order_id=None):
    conn = _conn()
    cur = conn.cursor()
    if order_id:
        cur.execute("SELECT * FROM production_progress WHERE order_id=? ORDER BY id", (order_id,))
    else:
        cur.execute("SELECT * FROM production_progress ORDER BY order_id, id")
    rows = cur.fetchall()
    conn.close()
    return rows

def format_production(order_id, stages):
    if not stages:
        return f"暂无订单 {order_id} 的生产进度"
    status_map = {"已完成": "✅", "进行中": "🔄", "待开始": "⏳", "异常": "❌"}
    lines = [f"🏭 订单 {order_id} 生产进度"]
    for s in stages:
        icon = status_map.get(s['status'], "❓")
        info = f"  {icon} {s['stage']} | {s['status']}"
        if s['operator']:
            info += f" | {s['operator']}"
        if s['start_date']:
            info += f" | {s['start_date']}"
        if s['notes']:
            info += f" | {s['notes']}"
        lines.append(info)
    return '\n'.join(lines)

# ======== 库存预警 ========
def get_inventory_alerts():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE stock < 1000 ORDER BY stock LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    return rows

def format_inventory_alerts(products):
    if not products:
        return "✅ 暂无库存预警，所有产品库存充足"
    lines = ["⚠️ 库存预警"]
    for p in products:
        lines.append(f"  🔴 {p['name']}({p['id']}) 库存: {p['stock']}米 | {p['category'] or '其他'}")
    return '\n'.join(lines)

# ======== 待发货 ========
def get_pending_shipments():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.customer, o.status,
               p.name as product_name, p.id as pid,
               o.quantity, o.price as unit_price
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.status IN ('待确认', '已确认', '生产中', '排产中', '染整中')
        ORDER BY o.created_at
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def format_pending_shipments(records):
    if not records:
        return "✅ 暂无待发货订单"
    lines = ["🚚 待发货订单"]
    current = None
    for r in records:
        if r['id'] != current:
            lines.append(f"\n📋 {r['id']} | {r['customer']}")
            current = r['id']
        subtotal = float(r['quantity'] or 0) * float(r['unit_price'] or 0)
        lines.append(f"  • {r['product_name']}({r['pid']}) ×{r['quantity']}米 ¥{subtotal:.0f}")
    return '\n'.join(lines)

# ======== 客户跟进 ========
def get_customer_followups(customer=None, limit=20):
    conn = _conn()
    cur = conn.cursor()
    if customer:
        cur.execute("SELECT * FROM customer_followups WHERE customer_id LIKE ? ORDER BY created_at DESC LIMIT ?",
                    (f"%{customer}%", limit))
    else:
        cur.execute("SELECT * FROM customer_followups ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def format_followups(records, customer_name=None):
    if not records:
        name_str = f"「{customer_name}」" if customer_name else ""
        return f"暂无{name_str}的跟进记录"
    title = f"👤 {'「'+customer_name+'」' if customer_name else ''}跟进记录"
    lines = [title]
    for f in records:
        icon = {"电话": "📞", "微信": "💬", "上门": "🏢", "邮件": "📧"}.get(f['followup_type'], "📝")
        lines.append(f"{icon} {f['created_at']} [{f['followup_type']}] {f['followup_by']}")
        lines.append(f"   {f['content']}")
        if f['next_followup_date']:
            lines.append(f"   📅 下次跟进: {f['next_followup_date']}")
    return '\n'.join(lines)

# ======== 销售报表 ========
def get_sales_report(start_date=None, end_date=None):
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.customer, o.amount, o.status, o.created_at,
               p.name as product_name, o.quantity, o.price as unit_price
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.created_at >= ? AND o.created_at <= ?
        AND o.status NOT IN ('已取消')
        ORDER BY o.created_at DESC
    """, (start_date, end_date + ' 23:59:59'))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return {'start_date': start_date, 'end_date': end_date, 'total': 0, 'count': 0, 'by_status': {}, 'orders': []}

    total = sum(float(r['amount']) for r in rows)
    order_ids = set(r['id'] for r in rows)
    by_status = {}
    for r in rows:
        st = r['status'] or '未知'
        by_status[st] = by_status.get(st, 0) + float(r['amount'])

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total': total,
        'count': len(order_ids),
        'by_status': by_status,
        'orders': rows,
    }

def format_sales_report(r):
    status_lines = '\n'.join([f"  • {k}: ¥{v:,.0f}" for k, v in r['by_status'].items()]) or "  暂无数据"
    avg = r['total'] / r['count'] if r['count'] > 0 else 0
    return f"""📊 销售报表
{r['start_date']} 至 {r['end_date']}

━━━━━━━━━━━━━━━
💰 总销售额: ¥{r['total']:,.0f}
📋 总订单数: {r['count']}单
📈 均单价: ¥{avg:,.0f}/单

━━━━━━━━━━━━━━━
📍 订单状态分布
{status_lines}
"""

# ======== 员工绩效 ========
def get_staff_performance(start_date=None):
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    conn = _conn()
    cur = conn.cursor()
    # 按跟进人统计
    cur.execute("""
        SELECT cf.followup_by as name, e.department,
               COUNT(DISTINCT cf.order_id) as order_count,
               COALESCE(SUM(o.amount), 0) as total_amount
        FROM customer_followups cf
        LEFT JOIN employees e ON e.name = cf.followup_by
        LEFT JOIN orders o ON o.id = cf.order_id AND o.created_at >= ?
        WHERE cf.followup_by IS NOT NULL
        GROUP BY cf.followup_by
        ORDER BY total_amount DESC
    """, (start_date,))
    rows = cur.fetchall()
    conn.close()
    return rows

def format_staff_performance(staff):
    if not staff:
        return "暂无员工跟进数据"
    lines = ["🏆 员工跟进排行(本月)"]
    for i, s in enumerate(staff, 1):
        icon = "🥇" if i == 1 else ("🥈" if i == 2 else "🥉") if i == 3 else "  "
        dept = s['department'] or '未分配'
        lines.append(f"{icon} {s['name']}({dept}) {s['order_count']}次跟进 ¥{s['total_amount']:,.0f}")
    return '\n'.join(lines)

# ========== 员工绩效 ==========
def get_staff_performance():
    """基于跟进记录统计员工绩效"""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT followup_by,
               COUNT(*) as followup_count,
               COUNT(CASE WHEN next_followup_date IS NOT NULL THEN 1 END) as next_plan_count
        FROM customer_followups
        GROUP BY followup_by
        ORDER BY followup_count DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def format_staff_performance(staff):
    if not staff:
        return "暂无员工绩效数据"
    lines = ["📊 员工跟进绩效\n━━━━━━━━━━━━━━━"]
    total = sum(r['followup_count'] for r in staff)
    for r in staff:
        pct = r['followup_count'] * 100 // total if total > 0 else 0
        lines.append(f"👤 {r['followup_by']}")
        lines.append(f"  跟进次数: {r['followup_count']}次 | 计划次数: {r['next_plan_count']}次")
        lines.append(f"  占比: {pct}%")
    return '\n'.join(lines)

# ========== 客户档案 ==========
def get_customer_profile(customer_name):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.id, o.created_at, o.amount, o.status,
               p.name as product_name, o.quantity
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.customer LIKE ?
        ORDER BY o.created_at DESC LIMIT 20
    """, (f"%{customer_name}%",))
    orders = cur.fetchall()
    followups = get_customer_followups(customer=customer_name)
    conn.close()
    return orders, followups

def format_customer_profile(orders, followups, customer_name):
    if not orders and not followups:
        return f"未找到客户「{customer_name}」的档案"
    total_amount = sum(float(r['amount']) for r in orders)
    total_qty = sum(int(r['quantity']) for r in orders)
    order_list = '\n'.join([
        f"  • {r['id']} | {r['product_name']}×{r['quantity']}米 | ¥{r['amount']} | {r['status']}"
        for r in orders[:5]
    ]) if orders else "暂无订单记录"
    lines = [f"👤 客户档案「{customer_name}」",
             "━━━━━━━━━━━━━━━",
             f"💰 累计消费: ¥{total_amount:,.0f}",
             f"📦 累计订单: {len(set(r['id'] for r in orders))}单",
             f"🧵 累计米数: {total_qty}米",
             "",
             "📋 最近订单"]
    lines.append(order_list)
    if followups:
        lines.append("\n📝 跟进记录")
        for f in followups[:3]:
            icon = {"电话": "📞", "微信": "💬", "上门": "🏢"}.get(f['followup_type'], "📝")
            lines.append(f"  {icon} {f['created_at']} [{f['followup_type']}] {f['content'][:40]}")
    return '\n'.join(lines)
