#!/usr/bin/env python3
"""来财AI客服 - 扩展数据导入"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), "laicai.db")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 建表
schema = open(os.path.join(os.path.dirname(__file__), "schema.sql"), encoding='utf-8').read()
conn.executescript(schema)
conn.commit()
print("✅ 表结构创建完成")

# 员工: 8列 (id, name, phone, wechat, department, role, is_active, created_at)
employees = [
    (1, '刘老板', '13800138000', 'liulaoban', '管理', '老板', 1, None),
    (2, '王销售', '13900139000', 'wangxiaoshou', '销售', '主管', 1, None),
    (3, '陈设计', '13700137000', 'chensheji', '产品开发', '员工', 1, None),
    (4, '赵跟单', '13600136000', 'zhaogendan', '生产跟单', '员工', 1, None),
    (5, '周仓管', '13500135000', 'zhoucangguan', '仓库', '员工', 1, None),
    (6, '吴品控', '13400134000', 'wupinkong', '品控', '员工', 1, None),
]
cur.executemany("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)", employees)

# 质检: 13列 (id, order_id, product_id, batch_no, check_type, result, defect_type, defect_meters, total_meters, inspector, check_date, notes, created_at)
qc_records = [
    (1, 'DD-20250501-001', 'FC-003', 'B-20250501', '出库检', '合格', None, 0, 1000, '吴品控', '2025-05-01', '外观合格，无异常', None),
    (2, 'DD-20250502-001', 'FC-007', 'B-20250502', '入库检', '待处理', '色差', 50, 300, '吴品控', '2025-05-02', '部分色差待确认，已通知工厂', None),
    (3, 'DD-20250503-001', 'FC-009', 'B-20250503', '巡检', '不合格', '破洞', 20, 800, '吴品控', '2025-05-03', '2处破洞已返工处理', None),
    (4, 'DD-20260525-001', 'FC-001', 'B-20260525', '出库检', '合格', None, 0, 300, '吴品控', '2026-05-25', '外观合格，可发货', None),
    (5, None, 'FC-003', 'B-20260525-2', '入库检', '待处理', '缩水率偏差', 30, 500, '吴品控', '2026-05-25', '待工厂确认缩水率', None),
    (6, None, 'FC-005', 'B-20260525-3', '出库检', '合格', None, 0, 2000, '吴品控', '2026-05-25', '外观合格', None),
]
cur.executemany("INSERT OR REPLACE INTO quality_checks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", qc_records)

# 物流: 12列 (id, order_id, express_company, tracking_no, sender, receiver, receiver_address, status, shipped_at, delivered_at, notes, created_at)
logistics = [
    (1, 'DD-20250501-001', '顺丰', 'SF1234567890', '南通希格斯', '李总', '江苏省南通市家纺城', '已签收', '2025-05-06', '2025-05-08', None, None),
    (2, 'DD-20250502-001', '京东', 'JDG9876543210', '南通希格斯', '张总', '浙江省杭州市余杭区', '运输中', '2025-05-07', None, None, None),
    (3, 'DD-20250503-001', '德邦', 'DBP1112223330', '南通希格斯', '赵总', '广东省广州市海珠区', '待发货', None, None, '打包中', None),
]
cur.executemany("INSERT OR REPLACE INTO logistics VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", logistics)

# 跟进: 8列 (id, customer_id, order_id, followup_type, content, followup_by, next_followup_date, created_at)
followups = [
    (1, '南通家纺城李总', 'DD-20250501-001', '电话', '客户确认订单，要求5月8日前发货，已安排顺丰', '王销售', None, '2025-05-01'),
    (2, '浙江某服装厂张总', 'DD-20250502-001', '微信', '客户询问物流进度，已发京东单号，货物运输中', '王销售', None, '2025-05-03'),
    (3, '南通赵老板', None, '上门', '客户有意向订购天丝产品，约下周上门看样选花型', '王销售', None, '2025-05-04'),
    (4, '广州面料采购王小姐', 'DD-20250505-001', '微信', '客户询问能否加急，已回复排产中，预计周三完成', '王销售', None, '2025-05-06'),
    (5, '钻石VIP张总', 'DD-20260525-001', '电话', '确认首批订单500米，月底结算，可享受VIP折扣', '王销售', None, '2026-05-25'),
]
cur.executemany("INSERT OR REPLACE INTO customer_followups VALUES(?,?,?,?,?,?,?,?)", followups)

# 生产进度: 9列 (id, order_id, stage, status, start_date, end_date, operator, notes, updated_at)
progress = [
    (1, 'DD-20250501-001', '备料', '已完成', '2025-05-01', '2025-05-01', '赵跟单', None, None),
    (2, 'DD-20250501-001', '印染', '已完成', '2025-05-02', '2025-05-04', '赵跟单', None, None),
    (3, 'DD-20250501-001', '定型', '已完成', '2025-05-05', '2025-05-05', '赵跟单', None, None),
    (4, 'DD-20250501-001', '质检', '已完成', '2025-05-05', '2025-05-05', '吴品控', '合格', None),
    (5, 'DD-20250501-001', '包装发货', '已完成', '2025-05-06', '2025-05-06', '周仓管', None, None),
    (6, 'DD-20260525-001', '备料', '进行中', '2026-05-25', None, '赵跟单', '面料已裁剪', None),
    (7, 'DD-20260525-001', '印染', '待开始', None, None, '赵跟单', None, None),
    (8, 'DD-20260525-001', '定型', '待开始', None, None, '赵跟单', None, None),
    (9, 'DD-20260525-001', '质检', '待开始', None, None, '吴品控', None, None),
    (10, 'DD-20260525-001', '包装发货', '待开始', None, None, '周仓管', None, None),
]
cur.executemany("INSERT OR REPLACE INTO production_progress VALUES(?,?,?,?,?,?,?,?,?)", progress)

conn.commit()

# 验证
for t in ['employees', 'quality_checks', 'logistics', 'customer_followups', 'production_progress']:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cur.fetchone()[0]}条")

conn.close()
print("\n✅ 扩展数据导入完成!")
