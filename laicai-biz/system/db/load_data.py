#!/usr/bin/env python3
"""
来财AI客服 - 数据导入脚本
将 CSV 数据导入 SQLite 数据库
"""

import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = os.path.dirname(os.path.abspath(__file__)) + "/laicai.db"
DATA_DIR = "/Users/wushixiaoshenxian/.openclaw/workspace/laicai-biz/产品资料"

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    with open(os.path.dirname(__file__) + "/init_db.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    print(f"✅ 数据库初始化完成: {DB_PATH}")
    return conn

def load_products(conn):
    """导入产品数据"""
    csv_path = DATA_DIR + "/产品目录_20250525.csv"
    cur = conn.cursor()
    count = 0
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 映射分类
            name = row["产品名称"]
            if "天丝" in name:
                category = "天丝"
            elif "全棉" in name or "棉布" in name:
                category = "全棉"
            elif "竹纤维" in name:
                category = "竹纤维"
            elif "交织" in name:
                category = "交织"
            elif "提花" in name:
                category = "提花"
            elif "抗菌" in name:
                category = "功能"
            else:
                category = "其他"
            
            if "印花" in row["工艺"]:
                subcategory = "印花"
            elif "染色" in row["工艺"]:
                subcategory = "染色"
            elif "提花" in row["工艺"]:
                subcategory = "提花"
            else:
                subcategory = "其他"
            
            # 解析成分
            comp = row["成分"].replace("%", "").strip()
            
            cur.execute("""
                INSERT OR REPLACE INTO products 
                (id, name, category, subcategory, spec, composition, width_cm, weight_gm2, 
                 craft, price, moq, stock, lead_days, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["产品编号"],
                row["产品名称"],
                category,
                subcategory,
                row["规格"],
                row["成分"],
                int(row["门幅(cm)"]),
                int(row["克重(g/m²)"]),
                row["工艺"],
                float(row["单价(元/米)"]),
                int(row["起订量(米)"]),
                int(row["库存(米)"]),
                int(row["交期(天)"]),
                row["状态"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))
            count += 1
    
    conn.commit()
    print(f"✅ 已导入 {count} 个产品")

def load_orders(conn):
    """导入订单数据"""
    csv_path = DATA_DIR + "/订单记录_20250525.csv"
    cur = conn.cursor()
    count = 0
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
                INSERT OR REPLACE INTO orders 
                (id, customer, contact, phone, product_id, quantity, price, amount,
                 color, craft_req, deposit, status, delivery, logistics, remark, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["订单编号"],
                row["客户名称"],
                row["联系人"],
                row["联系方式"],
                row["产品编号"],
                int(row["数量(米)"]),
                float(row["单价(元/米)"]),
                float(row["金额(元)"]),
                row.get("颜色", ""),
                row.get("工艺要求", ""),
                float(row.get("定金(元)", 0)),
                row["生产状态"],
                row.get("交期", ""),
                row.get("物流信息", ""),
                row.get("备注", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))
            count += 1
    
    conn.commit()
    print(f"✅ 已导入 {count} 条订单")

def load_inquiries(conn):
    """导入询价数据"""
    csv_path = DATA_DIR + "/客户询价记录_20250525.csv"
    cur = conn.cursor()
    count = 0
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
                INSERT OR REPLACE INTO inquiries 
                (id, customer, contact, phone, product_id, quantity, intent_price, source, status, remark, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["询价编号"],
                row["客户名称"],
                row["联系人"],
                row["联系方式"],
                row["产品编号"],
                int(row["数量(米)"]) if row["数量(米)"] else 0,
                float(row["意向单价"]) if row.get("意向单价") else None,
                row["询价来源"],
                row["跟进状态"],
                row["备注"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))
            count += 1
    
    conn.commit()
    print(f"✅ 已导入 {count} 条询价记录")

def query_db(conn, sql, params=None):
    """查询数据库"""
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    return cur.fetchall()

def main():
    print("=" * 50)
    print("来财AI客服 - 数据导入工具")
    print("=" * 50)
    
    # 初始化
    conn = init_db()
    
    # 导入数据
    load_products(conn)
    load_orders(conn)
    load_inquiries(conn)
    
    # 验证
    print("\n📊 数据验证:")
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM products")
    print(f"  产品数量: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM orders")
    print(f"  订单数量: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM inquiries")
    print(f"  询价数量: {cur.fetchone()[0]}")
    
    print("\n✅ 数据导入完成!")
    conn.close()

if __name__ == "__main__":
    main()
