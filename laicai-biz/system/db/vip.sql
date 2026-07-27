-- VIP会员 - 坯布库存 & 加工费数据表

-- ========== 坯布表 ==========
CREATE TABLE IF NOT EXISTS greycloth (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,           -- 坯布名称
    spec        TEXT,                   -- 规格
    composition TEXT,                   -- 成分
    width_cm    INTEGER,                -- 门幅(cm)
    weight_gm2  INTEGER,                -- 克重(g/m²)
    price       REAL NOT NULL,           -- 单价(元/米)
    unit        TEXT DEFAULT '米',       -- 单位
    stock       INTEGER DEFAULT 0,       -- 库存(米)
    supplier    TEXT,                   -- 供应商
    remark      TEXT,                   -- 备注
    created_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

CREATE INDEX IF NOT EXISTS idx_greycloth_name ON greycloth(name);
CREATE INDEX IF NOT EXISTS idx_greycloth_stock ON greycloth(stock);

-- ========== 加工工艺表 ==========
CREATE TABLE IF NOT EXISTS processing (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,           -- 工艺名称
    category    TEXT,                   -- 工艺类别
    unit        TEXT DEFAULT '元/米',    -- 计价单位
    price       REAL NOT NULL,           -- 加工费
    min_order   INTEGER DEFAULT 0,       -- 最低起订量
    lead_days   INTEGER,                -- 加工周期(天)
    quality_req TEXT,                   -- 质量要求
    remark      TEXT,                   -- 备注
    created_at  TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

CREATE INDEX IF NOT EXISTS idx_processing_category ON processing(category);
CREATE INDEX IF NOT EXISTS idx_processing_price ON processing(price);

-- ========== 加工厂表 ==========
CREATE TABLE IF NOT EXISTS factories (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,           -- 工厂名称
    location    TEXT,                   -- 所在地
    specialty   TEXT,                   -- 专长
    contact     TEXT,                   -- 联系方式
    rating      REAL DEFAULT 5.0,       -- 评分(1-5)
    status      TEXT DEFAULT '正常',     -- 合作状态
    remark      TEXT,
    created_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

-- ========== 工厂工艺关联表 ==========
CREATE TABLE IF NOT EXISTS factory_processing (
    factory_id  TEXT,
    process_id TEXT,
    price      REAL,                   -- 该工厂此工艺的具体报价
    lead_days  INTEGER,                -- 该工厂此工艺的实际周期
    PRIMARY KEY (factory_id, process_id)
);

-- ========== VIP名单 ==========
CREATE TABLE IF NOT EXISTS vip_members (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,           -- 客户名称
    phone       TEXT,                   -- 联系方式
    level       TEXT DEFAULT '普通VIP',  -- VIP等级
    company     TEXT,                   -- 公司/单位
    credit_limit REAL DEFAULT 0,        -- 信用额度
    discount    REAL DEFAULT 1.0,        -- 折扣系数(1.0=无折扣)
    status      TEXT DEFAULT '正常',     -- 状态
    remark      TEXT,
    created_at  TEXT DEFAULT (datetime('now', '+8 hours'))
);

CREATE INDEX IF NOT EXISTS idx_vip_name ON vip_members(name);
CREATE INDEX IF NOT EXISTS idx_vip_level ON vip_members(level);
CREATE INDEX IF NOT EXISTS idx_vip_status ON vip_members(status);
