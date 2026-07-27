#!/usr/bin/env python3
"""
来财AI客服 - query_extended v2
新增：
1. 经营驾驶舱 v2（含昨日同比、库存周转）
2. 热销/滞销红黑榜
3. 临近交期预警
4. 销售漏斗分析
"""

import sqlite3
from datetime import datetime, timedelta
import os

_S = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(os.path.dirname(_S), "db", "laicai.db")

def _conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ======== 经营驾驶舱 v2 ========
def get_boss_dashboard_v2():
    """增强版老板驾驶舱：含昨日同比、库存周转、热销/滞销"""
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    month_start = today[:7] + '-01'
    conn = _conn()
    cur = conn.cursor()

    # 今日数据
    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM orders WHERE created_at LIKE ?", (today+'%',))
    today_data = cur.fetchone()

    # 昨日数据（同比）
    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM orders WHERE created_at LIKE ?", (yesterday+'%',))
    yesterday_data = cur.fetchone()

    # 本月累计
    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM orders WHERE created_at >= ?", (month_start,))
    month_data = cur.fetchone()

    # 进行中订单
    cur.execute("SELECT COUNT(*) FROM orders WHERE status IN ('待确认','已确认','生产中','排产中','染整中')")
    pending = cur.fetchone()[0]

    # 库存预警
    cur.execute("SELECT COUNT(*) FROM products WHERE stock < 1000")
    alerts = cur.fetchone()[0]

    # 热销TOP5
    cur.execute("""
        SELECT p.name, p.id, COALESCE(SUM(o.quantity),0) as total_qty, COUNT(o.id) as cnt
        FROM products p
        LEFT JOIN orders o ON o.product_id = p.id AND o.created_at >= ? AND o.status NOT IN ('已取消')
        GROUP BY p.id ORDER BY total_qty DESC LIMIT 5
    """, (month_start,))
    hot = cur.fetchall()

    # 滞销（30天无订单）
    cur.execute("""
        SELECT p.id, p.name, p.stock
        FROM products p
        WHERE p.stock > 0
        AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.product_id = p.id AND o.created_at >= ?)
        ORDER BY p.stock DESC LIMIT 5
    """, ((datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),))
    cold = cur.fetchall()

    # 质检
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN result='合格' THEN 1 ELSE 0 END) FROM quality_checks WHERE created_at >= ?", (month_start,))
    qc_data = cur.fetchone()
    qc_rate = f"{qc_data[1]*100/qc_data[0]:.1f}%" if qc_data[0] and qc_data[0] > 0 else "暂无数据"

    # 临近交期（3天内）
    cur.execute("""
        SELECT COUNT(*) FROM orders
        WHERE status IN ('已确认','生产中','排产中','染整中')
        AND delivery BETWEEN ? AND ?
    """, (today, (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')))
    near_delivery = cur.fetchone()[0]

    # 总库存和平均库存
    cur.execute("SELECT COALESCE(SUM(stock),0), COUNT(*) FROM products")
    total_stock, product_count = cur.fetchone()

    conn.close()

    # 同比计算
    order_diff = today_data[0] - yesterday_data[0]
    amount_diff = today_data[1] - yesterday_data[1]
    order_trend = "📈" if order_diff > 0 else ("📉" if order_diff < 0 else "➡️")
    amount_trend = "📈" if amount_diff > 0 else ("📉" if amount_diff < 0 else "➡️")

    return {
        'today': {'orders': today_data[0], 'amount': today_data[1]},
        'yesterday': {'orders': yesterday_data[0], 'amount': yesterday_data[1]},
        'order_diff': order_diff,
        'amount_diff': amount_diff,
        'order_trend': order_trend,
        'amount_trend': amount_trend,
        'month_orders': month_data[0],
        'month_amount': month_data[1],
        'pending': pending,
        'stock_alerts': alerts,
        'hot': hot,
        'cold': cold,
        'qc_rate': qc_rate,
        'near_delivery': near_delivery,
        'total_stock': total_stock,
        'product_count': product_count,
    }

def format_boss_dashboard_v2(d):
    today_str = datetime.now().strftime('%Y-%m-%d')
    hot_lines = '\n'.join([
        f"  • {r['name']}({r['id']}) {int(r['total_qty'] or 0)}米/{r['cnt'] or 0}单"
        for r in d['hot'] if r['total_qty'] and r['total_qty'] > 0
    ]) or "  暂无成交数据"

    cold_lines = '\n'.join([
        f"  ⚫ {r['name']}({r['id']}) 库存:{r['stock']}米 | 30天无订单"
        for r in d['cold']
    ]) or "  暂无滞销数据"

    return f"""📊 来财经营驾驶舱 v2 - {today_str}

━━━━━━━━━━━━━━
📈 今日 vs 昨日
  {d['order_trend']} 今日订单: {d['today']['orders']}单 (昨日{d['yesterday']['orders']}单 {'+'+str(d['order_diff']) if d['order_diff'] > 0 else d['order_diff']})
  {d['amount_trend']} 今日金额: ¥{d['today']['amount']:,.0f} (昨日¥{d['yesterday']['amount']:,.0f})

━━━━━━━━━━━━━━
📈 本月累计
  成交订单: {d['month_orders']}单
  成交金额: ¥{d['month_amount']:,.0f}

━━━━━━━━━━━━━━
🚚 进行中订单: {d['pending']}单
⏰ 3天内交期: {d['near_delivery']}单
⚠️ 库存预警: {d['stock_alerts']}款
🔬 本月质检合格率: {d['qc_rate']}

━━━━━━━━━━━━━━
🔥 本月热销TOP5
{hot_lines}

━━━━━━━━━━━━━━
⚫ 滞销预警（30天无订单）
{cold_lines}

━━━━━━━━━━━━━━
📦 库存总览
  产品数: {d['product_count']}款
  总库存: {d['total_stock']:,}米
"""
