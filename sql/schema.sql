-- ============================================================================
-- E-Commerce Customer & Sales Intelligence — Database Schema
-- Phase 4: SQL Database & Data Modeling
-- ============================================================================
-- Design: star schema — one fact table (fact_sales) surrounded by dimension
-- tables (customers, products, categories, subcategories, stores, dates).
--
-- Written in Postgres-compatible SQL. The project database engine is SQLite
-- (see docs/database_schema.md for why), so python/build_database.py adapts
-- these statements slightly for SQLite (e.g. SERIAL -> INTEGER, DATE type
-- handling) — the structure, keys, and relationships are identical.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Dimension: Categories
-- ---------------------------------------------------------------------------
CREATE TABLE dim_category (
    category_key    TEXT PRIMARY KEY,
    category_name   TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Dimension: Subcategories (each belongs to exactly one category)
-- ---------------------------------------------------------------------------
CREATE TABLE dim_subcategory (
    subcategory_key     TEXT PRIMARY KEY,
    subcategory_name    TEXT NOT NULL,
    category_key        TEXT NOT NULL REFERENCES dim_category(category_key)
);

-- ---------------------------------------------------------------------------
-- Dimension: Products
-- ---------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key      INTEGER PRIMARY KEY,
    product_name     TEXT NOT NULL,
    brand            TEXT,
    color            TEXT,
    unit_cost_usd    NUMERIC(10,2) NOT NULL,
    unit_price_usd   NUMERIC(10,2) NOT NULL,
    subcategory_key  TEXT NOT NULL REFERENCES dim_subcategory(subcategory_key)
);

-- ---------------------------------------------------------------------------
-- Dimension: Customers
-- ---------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key   INTEGER PRIMARY KEY,
    gender         TEXT,
    name           TEXT,
    city           TEXT,
    state_code     TEXT,
    state          TEXT,
    zip_code       TEXT,
    country        TEXT,
    continent      TEXT,
    birthday       DATE
);

-- ---------------------------------------------------------------------------
-- Dimension: Stores (StoreKey 0 = "Online" channel — see is_online flag)
-- ---------------------------------------------------------------------------
CREATE TABLE dim_store (
    store_key       INTEGER PRIMARY KEY,
    country         TEXT NOT NULL,
    state           TEXT,
    square_meters   NUMERIC(10,2),
    open_date       DATE,
    is_online       BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
-- Dimension: Date (generated to cover the full Sales Order Date range)
-- ---------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key        DATE PRIMARY KEY,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    day             INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,
    day_name        TEXT NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

-- ---------------------------------------------------------------------------
-- Reference: Exchange rates (kept for optional local-currency reporting;
-- not used in the core Revenue USD calculation — see docs/cleaning_log.md)
-- ---------------------------------------------------------------------------
CREATE TABLE exchange_rate (
    rate_date   DATE NOT NULL,
    currency    TEXT NOT NULL,
    exchange    NUMERIC(12,6) NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

-- ---------------------------------------------------------------------------
-- Fact: Sales (one row per order line item)
-- ---------------------------------------------------------------------------
CREATE TABLE fact_sales (
    order_number     INTEGER NOT NULL,
    line_item        INTEGER NOT NULL,
    order_date       DATE NOT NULL REFERENCES dim_date(date_key),
    delivery_date    DATE,               -- nullable: ~79% of orders have no recorded delivery date
    is_delivered     BOOLEAN NOT NULL,
    customer_key     INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    store_key        INTEGER NOT NULL REFERENCES dim_store(store_key),
    product_key      INTEGER NOT NULL REFERENCES dim_product(product_key),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    currency_code    TEXT NOT NULL,
    unit_price_usd   NUMERIC(10,2) NOT NULL,
    unit_cost_usd    NUMERIC(10,2) NOT NULL,
    revenue_usd      NUMERIC(12,2) NOT NULL,
    cost_usd         NUMERIC(12,2) NOT NULL,
    profit_usd       NUMERIC(12,2) NOT NULL,
    PRIMARY KEY (order_number, line_item)
);

-- ---------------------------------------------------------------------------
-- Indexes to support common analytical query patterns
-- ---------------------------------------------------------------------------
CREATE INDEX idx_fact_sales_customer   ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product    ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_store      ON fact_sales(store_key);
CREATE INDEX idx_fact_sales_order_date ON fact_sales(order_date);
CREATE INDEX idx_product_subcategory   ON dim_product(subcategory_key);
CREATE INDEX idx_subcategory_category  ON dim_subcategory(category_key);

-- ============================================================================
-- Conceptual model:
--
-- dim_customer ──┐
--                │
-- dim_store ─────┼──> fact_sales <── dim_product ──> dim_subcategory ──> dim_category
--                │        │
-- dim_date <─────┘        └── (currency_code, joinable to exchange_rate for
--                              optional local-currency reporting only)
-- ============================================================================
