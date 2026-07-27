-- 员工表
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    wechat TEXT,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (date('now'))
);

-- 质检记录表
CREATE TABLE IF NOT EXISTS quality_checks (
    id INTEGER PRIMARY KEY,
    order_id TEXT,
    product_id TEXT,
    batch_no TEXT,
    check_type TEXT,
    result TEXT,
    defect_type TEXT,
    defect_meters REAL,
    total_meters REAL,
    inspector TEXT,
    check_date TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (date('now'))
);

-- 物流发货表
CREATE TABLE IF NOT EXISTS logistics (
    id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    express_company TEXT,
    tracking_no TEXT,
    sender TEXT,
    receiver TEXT,
    receiver_address TEXT,
    status TEXT DEFAULT '待发货',
    shipped_at TEXT,
    delivered_at TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (date('now'))
);

-- 客户跟进记录表
CREATE TABLE IF NOT EXISTS customer_followups (
    id INTEGER PRIMARY KEY,
    customer_id TEXT,
    order_id TEXT,
    followup_type TEXT,
    content TEXT,
    followup_by TEXT,
    next_followup_date TEXT,
    created_at TEXT DEFAULT (date('now'))
);

-- 生产进度表
CREATE TABLE IF NOT EXISTS production_progress (
    id INTEGER PRIMARY KEY,
    order_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    status TEXT DEFAULT '待开始',
    start_date TEXT,
    end_date TEXT,
    operator TEXT,
    notes TEXT,
    updated_at TEXT DEFAULT (date('now'))
);
