#!/usr/bin/env python3
"""
来财AI客服 - 核心查询工具
提供：查价格/查库存/查订单/推荐产品等功能
"""

import sqlite3
import os
import re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "laicai.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def search_products(keyword):
    """
    搜索产品
    支持：品名/规格/成分/分类 模糊搜索
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # 模糊匹配
    pattern = f"%{keyword}%"
    cur.execute("""
        SELECT id, name, category, spec, composition, craft, price, moq, stock, lead_days, status
        FROM products
        WHERE name LIKE ? OR spec LIKE ? OR composition LIKE ? OR category LIKE ? OR craft LIKE ?
        ORDER BY 
            CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
            stock DESC
        LIMIT 10
    """, (pattern, pattern, pattern, pattern, pattern, pattern))
    
    results = cur.fetchall()
    conn.close()
    return results

def get_product_by_id(product_id):
    """根据编号查产品"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, category, subcategory, spec, composition, width_cm, weight_gm2,
               craft, price, moq, stock, lead_days, status, features, scenes, colors
        FROM products WHERE id = ?
    """, (product_id,))
    result = cur.fetchone()
    conn.close()
    return result

def check_stock(keyword):
    """查库存"""
    products = search_products(keyword)
    if not products:
        return None
    
    results = []
    for p in products:
        stock_status = "🟢充足" if p[8] > 5000 else "🟡偏少" if p[8] > 1000 else "🔴紧张" if p[8] > 0 else "⚫缺货"
        results.append({
            "id": p[0],
            "name": p[1],
            "stock": p[8],
            "status": stock_status,
            "lead_days": p[9],
            "price": p[6]
        })
    return results

def get_stock_alerts():
    """库存告警"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM v_stock_alert")
    results = cur.fetchall()
    conn.close()
    return results

def search_orders(keyword=None, status=None):
    """查订单"""
    conn = get_conn()
    cur = conn.cursor()
    
    sql = """
        SELECT o.id, o.customer, p.name, o.quantity, o.price, o.amount, 
               o.status, o.delivery, o.logistics, o.created_at
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE 1=1
    """
    params = []
    
    if keyword:
        sql += " AND (o.id LIKE ? OR o.customer LIKE ? OR p.name LIKE ?)"
        k = f"%{keyword}%"
        params = [k, k, k]
    
    if status:
        sql += " AND o.status = ?"
        params.append(status)
    
    sql += " ORDER BY o.created_at DESC LIMIT 20"
    
    cur.execute(sql, params)
    results = cur.fetchall()
    conn.close()
    return results

def get_order_detail(order_id):
    """订单详情"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, p.name as product_name, p.spec
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE o.id = ?
    """, (order_id,))
    result = cur.fetchone()
    conn.close()
    return result

def get_pending_inquiries():
    """待跟进询价"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM v_pending_inquiries")
    results = cur.fetchall()
    conn.close()
    return results

def get_hot_products(limit=5):
    """热销产品"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM v_hot_products LIMIT ?", (limit,))
    results = cur.fetchall()
    conn.close()
    return results

def create_order(customer, product_id, quantity, price, contact="", phone="", remark=""):
    """创建订单"""
    conn = get_conn()
    cur = conn.cursor()
    
    # 生成订单号
    today = datetime.now().strftime("%Y%m%d")
    cur.execute("SELECT COUNT(*) FROM orders WHERE id LIKE ?", (f"DD-{today}%",))
    seq = cur.fetchone()[0] + 1
    order_id = f"DD-{today}-{seq:03d}"
    
    amount = float(price) * int(quantity)
    
    # 计算交期
    cur.execute("SELECT lead_days FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    lead_days = row[0] if row else 7
    delivery = (datetime.now() + timedelta(days=lead_days)).strftime("%Y-%m-%d")
    
    cur.execute("""
        INSERT INTO orders 
        (id, customer, contact, phone, product_id, quantity, price, amount, status, delivery, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_id, customer, product_id, int(quantity), float(price), amount, "待确认", delivery, remark))
    
    conn.commit()
    conn.close()
    return order_id, amount, delivery

# ========== 格式化输出 ==========

def format_product(p):
    """格式化产品信息"""
    if not p:
        return "未找到相关产品"
    
    # id=0, name=1, category=2, subcategory=3, spec=4, composition=5, width=6, weight=7, craft=8
    # price=9, moq=10, stock=11, lead_days=12, status=13, features=14, scenes=15, colors=16
    stock_emoji = "🟢" if p[11] > 5000 else "🟡" if p[11] > 1000 else "🔴" if p[11] > 0 else "⚫"
    
    return f"""📦 {p[1]}

🏷️ 编号: {p[0]}
📂 分类: {p[2]} / {p[3]}
📐 规格: {p[4]}
🧵 成分: {p[5]}
📏 门幅: {p[6]}cm | 克重: {p[7]}g/m²
🎨 工艺: {p[8]}
━━━━━━━━━━━━━━━
💰 价格: ¥{p[9]}/米
📦 起订量: {p[10]}米
{stock_emoji} 库存: {p[11]}米
⏱️ 交期: {p[12]}天
📌 状态: {p[13]}
━━━━━━━━━━━━━━━
✨ 特点: {p[14] or '暂无'}
🏠 适用: {p[15] or '暂无'}
🎨 可选: {p[16] or '支持定染'}"""

def format_product_list(products):
    """格式化产品列表"""
    if not products:
        return "未找到相关产品，换个关键词试试~"
    
    lines = [f"🔍 找到 {len(products)} 个相关产品:\n"]
    for i, p in enumerate(products, 1):
        stock = p[8] if len(p) > 8 else p[7]
        price = p[6] if len(p) > 8 else p[5]
        stock_emoji = "🟢" if stock > 5000 else "🟡" if stock > 1000 else "🔴" if stock > 0 else "⚫"
        lines.append(f"{i}. {p[1]} | ¥{price}/米 | {stock_emoji}{stock}米 | {p[9]}天")
    
    lines.append("\n回复产品编号即可查看详情，如: FC-001")
    return "\n".join(lines)

def format_stock_check(results):
    """格式化库存查询"""
    if not results:
        return "未找到相关产品库存信息"
    
    lines = [f"📦 库存查询结果 ({len(results)}款):\n"]
    for r in results:
        lines.append(f"{r['name']}\n  库存: {r['status']} {r['stock']}米 | 交期: {r['lead_days']}天 | ¥{r['price']}/米")
    
    return "\n\n".join(lines)

def format_orders(orders):
    """格式化订单列表"""
    if not orders:
        return "未找到相关订单"
    
    status_emoji = {
        "待确认": "⏳",
        "已确认": "✅",
        "排产中": "📋",
        "生产中": "🔨",
        "染整中": "🎨",
        "已完成": "🏁",
        "已发货": "📦",
        "已交付": "✔️"
    }
    
    lines = [f"📋 订单列表 ({len(orders)}条):\n"]
    for o in orders:
        emoji = status_emoji.get(o[6], "❓")
        lines.append(f"{emoji} {o[0]} | {o[1]}\n  {o[2]} ×{o[3]}米 | ¥{o[5]} | {o[6]}\n  交期: {o[7]} | 下单: {o[9][:10]}")
    
    return "\n\n".join(lines)

def format_order_detail(order):
    """格式化订单详情"""
    if not order:
        return "未找到该订单"
    
    status_emoji = {
        "待确认": "⏳",
        "已确认": "✅",
        "排产中": "📋",
        "生产中": "🔨",
        "染整中": "🎨",
        "已完成": "🏁",
        "已发货": "📦",
        "已交付": "✔️"
    }
    
    emoji = status_emoji.get(order[11], "❓")
    
    return f"""📋 订单详情

订单号: {order[0]}
━━━━━━━━━━━━━━━
👤 客户: {order[1]}
📞 联系: {order[3]}
━━━━━━━━━━━━━━━
📦 产品: {order[17]} ({order[18]})
🔢 数量: {order[5]}米
💰 单价: ¥{order[6]}/米
💵 总价: ¥{order[7]}
━━━━━━━━━━━━━━━
{emoji} 状态: {order[11]}
📅 交期: {order[12]}
🚚 物流: {order[13] or '待发货'}
💰 定金: ¥{order[10]}元
📝 备注: {order[14] or '无'}
━━━━━━━━━━━━━━━
📅 下单: {order[15][:10]}"""

# ========== 主程序测试 ==========
if __name__ == "__main__":
    print("=" * 50)
    print("来财AI客服 - 查询工具测试")
    print("=" * 50)
    
    # 测试搜索
    print("\n[测试] 搜索 '天丝':")
    results = search_products("天丝")
    print(format_product_list(results))
    
    print("\n[测试] 产品详情 FC-001:")
    p = get_product_by_id("FC-001")
    print(format_product(p))
    
    print("\n[测试] 订单查询:")
    orders = search_orders()
    print(format_orders(orders))
