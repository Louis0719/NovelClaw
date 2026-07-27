#!/usr/bin/env python3
"""VIP数据导入工具"""
import sqlite3, csv, os
from datetime import datetime

DB = "/Users/wushixiaoshenxian/.openclaw/workspace/laicai-biz/system/db/laicai.db"
VIP_DIR = "/Users/wushixiaoshenxian/.openclaw/workspace/laicai-biz/VIP资料"

def init_vip_db():
    conn = sqlite3.connect(DB)
    with open("/Users/wushixiaoshenxian/.openclaw/workspace/laicai-biz/system/db/vip.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    print("VIP表初始化完成")
    return conn

def load_vip_members(conn):
    path = VIP_DIR + "/VIP名单_20250525.csv"
    cur = conn.cursor()
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cur.execute("""INSERT OR REPLACE INTO vip_members 
                (id,name,phone,level,company,credit_limit,discount,status,remark)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (row["客户名称"][:8], row["客户名称"], row["联系电话"],
                 row["VIP等级"], row["公司/单位"],
                 float(row["信用额度(万)"]), float(row["折扣系数"]),
                 row["状态"], row.get("备注", "")))
            count += 1
    conn.commit()
    print(f"VIP名单：导入 {count} 条")

def load_greycloth(conn):
    path = VIP_DIR + "/坯布库存_20250525.csv"
    cur = conn.cursor()
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cur.execute("""INSERT OR REPLACE INTO greycloth
                (id,name,spec,composition,width_cm,weight_gm2,price,stock,supplier,remark)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (row["坯布编号"], row["坯布名称"], row["规格"],
                 row["成分"], int(row["门幅(cm)"]), int(row["克重(g/m²)"]),
                 float(row["单价(元/米)"]), int(row["库存(米)"]),
                 row["供应商"], row.get("备注", "")))
            count += 1
    conn.commit()
    print(f"坯布库存：导入 {count} 条")

def load_processing(conn):
    path = VIP_DIR + "/加工费_20250525.csv"
    cur = conn.cursor()
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cur.execute("""INSERT OR REPLACE INTO processing
                (id,name,category,unit,price,min_order,lead_days,quality_req,remark)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (row["工艺编号"], row["工艺名称"], row["类别"], row["计价单位"],
                 float(row["加工费(元/米)"]), int(row["最低起订(米)"]),
                 int(row["周期(天)"]), row["质量要求"], row.get("备注", "")))
            count += 1
    conn.commit()
    print(f"加工费：导入 {count} 条")

def main():
    print("=" * 50)
    print("VIP数据导入工具")
    print("=" * 50)
    conn = init_vip_db()
    load_vip_members(conn)
    load_greycloth(conn)
    load_processing(conn)
    # 验证
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM vip_members"); print(f"VIP总数：{cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM greycloth"); print(f"坯布总数：{cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM processing"); print(f"加工工艺：{cur.fetchone()[0]}")
    conn.close()
    print("导入完成！")

if __name__ == "__main__":
    main()
