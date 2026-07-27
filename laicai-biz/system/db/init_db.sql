-- 来财AI客服 - SQLite 数据库初始化脚本
-- 运行: sqlite3 laicai.db < init_db.sql

-- ========== 产品表 ==========
CREATE TABLE IF NOT EXISTS products (
    id          TEXT PRIMARY KEY,       -- 产品编号 FC-001
    name        TEXT NOT NULL,          -- 产品名称
    category    TEXT,                   -- 大类 (天丝/全棉/竹纤维/交织/提花/功能)
    subcategory TEXT,                   -- 小类 (印花/染色/提花)
    spec        TEXT,                   -- 规格
    composition TEXT,                   -- 成分
    width_cm    INTEGER,                -- 门幅(cm)
    weight_gm2  INTEGER,                -- 克重(g/m²)
    craft       TEXT,                   -- 工艺
    price       REAL NOT NULL,          -- 单价(元/米)
    moq         INTEGER DEFAULT 300,    -- 最小起订量(米)
    stock       INTEGER DEFAULT 0,       -- 库存(米)
    lead_days   INTEGER DEFAULT 7,       -- 交期(天)
    status      TEXT DEFAULT '正常',     -- 状态 (正常/新品/预售/缺货)
    features    TEXT,                   -- 产品特点
    scenes      TEXT,                   -- 适用场景
    colors      TEXT,                   -- 可选颜色
    created_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);

-- ========== 客户询价表 ==========
CREATE TABLE IF NOT EXISTS inquiries (
    id          TEXT PRIMARY KEY,       -- 询价编号
    customer    TEXT NOT NULL,           -- 客户名称
    contact     TEXT,                   -- 联系人
    phone       TEXT,                   -- 联系方式
    product_id  TEXT,                   -- 产品编号
    quantity    INTEGER,                -- 意向数量
    intent_price REAL,                  -- 意向单价
    source      TEXT,                   -- 来源 (微信/电话/展会/老客户)
    status      TEXT DEFAULT '跟进中',   -- 跟进状态 (已报价/跟进中/已下单/无效)
    remark      TEXT,                   -- 备注
    created_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_inquiries_customer ON inquiries(customer);
CREATE INDEX IF NOT EXISTS idx_inquiries_status ON inquiries(status);

-- ========== 订单表 ==========
CREATE TABLE IF NOT EXISTS orders (
    id          TEXT PRIMARY KEY,       -- 订单编号
    customer    TEXT NOT NULL,          -- 客户名称
    contact     TEXT,                   -- 联系人
    phone       TEXT,                   -- 联系方式
    product_id  TEXT NOT NULL,          -- 产品编号
    quantity    INTEGER NOT NULL,        -- 数量(米)
    price       REAL NOT NULL,          -- 单价(元/米)
    amount      REAL NOT NULL,          -- 总金额(元)
    color       TEXT,                   -- 颜色要求
    craft_req   TEXT,                   -- 工艺要求
    deposit     REAL DEFAULT 0,         -- 定金(元)
    status      TEXT DEFAULT '待确认',   -- 生产状态 (待确认/已确认/排产中/生产中/染整中/已完成/已发货/已交付)
    delivery    TEXT,                   -- 交期
    logistics   TEXT,                   -- 物流信息
    remark      TEXT,                   -- 备注
    created_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_id);

-- ========== 系统日志表 ==========
CREATE TABLE IF NOT EXISTS chat_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_msg    TEXT NOT NULL,          -- 用户消息
    intent      TEXT,                   -- 识别意图
    reply       TEXT,                   -- AI回复
    session_id  TEXT,                   -- 会话ID
    created_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

-- ========== 视图 ==========
-- 库存告警视图
CREATE VIEW IF NOT EXISTS v_stock_alert AS
SELECT 
    id, name, category, stock, lead_days,
    CASE 
        WHEN stock = 0 THEN '🔴 缺货'
        WHEN stock < 500 THEN '🔴 紧张'
        WHEN stock < 2000 THEN '🟡 偏少'
        ELSE '🟢 充足'
    END as stock_status
FROM products
WHERE stock < 2000 OR stock = 0
ORDER BY stock ASC;

-- 热销产品视图
CREATE VIEW IF NOT EXISTS v_hot_products AS
SELECT 
    p.id, p.name, p.category, p.price, p.stock,
    COUNT(o.id) as order_count,
    SUM(o.quantity) as total_sold,
    SUM(o.amount) as total_amount
FROM products p
LEFT JOIN orders o ON p.id = o.product_id
GROUP BY p.id
ORDER BY order_count DESC
LIMIT 10;

-- 待跟进询价视图
CREATE VIEW IF NOT EXISTS v_pending_inquiries AS
SELECT 
    i.id, i.customer, i.contact, p.name as product_name, 
    i.quantity, i.status, i.created_at
FROM inquiries i
LEFT JOIN products p ON i.product_id = p.id
WHERE i.status = '跟进中'
ORDER BY i.created_at DESC;
