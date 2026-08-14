-- ============================================================================
-- Phase 5 — SQL Sales Analytics
-- ============================================================================
-- Every query here answers a specific business question (see comments).
-- Run against data/processed/ecommerce_analytics.db.
-- Queries are delimited by "-- @query: <name>" markers, parsed and executed
-- by python/run_sql_analytics.py, which writes results to
-- reports/phase5_sales_analytics_report.md.
--
-- NOTE ON DATE RANGE: data spans 2016-01-01 to 2021-02-20. 2021 is a
-- PARTIAL year (only Jan-Feb) — flagged wherever it affects interpretation
-- (e.g. year-over-year comparisons).
-- ============================================================================


-- ============================================================================
-- SECTION 1: SALES KPIs
-- ============================================================================

-- @query: kpi_summary
-- Business question: How is the business performing overall?
SELECT
    ROUND(SUM(revenue_usd), 2)                          AS total_revenue_usd,
    COUNT(DISTINCT order_number)                         AS total_orders,
    COUNT(DISTINCT customer_key)                          AS total_customers_who_ordered,
    SUM(quantity)                                         AS total_units_sold,
    ROUND(SUM(revenue_usd) * 1.0 / COUNT(DISTINCT order_number), 2) AS avg_order_value_usd,
    ROUND(SUM(revenue_usd) * 1.0 / COUNT(DISTINCT customer_key), 2) AS avg_revenue_per_customer_usd
FROM fact_sales;


-- @query: monthly_revenue_and_growth
-- Business question: How is revenue trending month over month?
-- Uses a CTE, date functions (strftime), and a window function (LAG) for
-- month-over-month growth %.
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date)  AS year_month,
        SUM(revenue_usd)               AS revenue_usd,
        COUNT(DISTINCT order_number)   AS orders
    FROM fact_sales
    GROUP BY 1
)
SELECT
    year_month,
    ROUND(revenue_usd, 2)              AS revenue_usd,
    orders,
    ROUND(revenue_usd - LAG(revenue_usd) OVER (ORDER BY year_month), 2)         AS revenue_change_usd,
    ROUND(
        100.0 * (revenue_usd - LAG(revenue_usd) OVER (ORDER BY year_month))
        / NULLIF(LAG(revenue_usd) OVER (ORDER BY year_month), 0)
    , 2)                                AS mom_growth_pct
FROM monthly
ORDER BY year_month;


-- @query: yearly_revenue_and_growth
-- Business question: How is revenue trending year over year? (2021 is partial: Jan-Feb only)
WITH yearly AS (
    SELECT
        CAST(strftime('%Y', order_date) AS INTEGER) AS year,
        SUM(revenue_usd)                             AS revenue_usd,
        COUNT(DISTINCT order_number)                 AS orders
    FROM fact_sales
    GROUP BY 1
)
SELECT
    year,
    ROUND(revenue_usd, 2) AS revenue_usd,
    orders,
    ROUND(
        100.0 * (revenue_usd - LAG(revenue_usd) OVER (ORDER BY year))
        / NULLIF(LAG(revenue_usd) OVER (ORDER BY year), 0)
    , 2) AS yoy_growth_pct,
    CASE WHEN year = (SELECT CAST(strftime('%Y', MAX(order_date)) AS INTEGER) FROM fact_sales)
         THEN 'PARTIAL YEAR' ELSE 'FULL YEAR' END AS year_completeness
FROM yearly
ORDER BY year;


-- ============================================================================
-- SECTION 2: PRODUCT ANALYSIS
-- ============================================================================

-- @query: top_10_products_by_revenue
-- Business question: What products drive the most revenue?
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    ROUND(SUM(f.revenue_usd), 2) AS total_revenue_usd,
    SUM(f.quantity)              AS total_units_sold,
    RANK() OVER (ORDER BY SUM(f.revenue_usd) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p       ON f.product_key = p.product_key
JOIN dim_subcategory sc  ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c      ON sc.category_key = c.category_key
GROUP BY p.product_key, p.product_name, p.brand, c.category_name
ORDER BY total_revenue_usd DESC
LIMIT 10;


-- @query: top_10_products_by_quantity
-- Business question: What products sell the most units (may differ from revenue leaders)?
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    SUM(f.quantity)               AS total_units_sold,
    ROUND(SUM(f.revenue_usd), 2)  AS total_revenue_usd,
    RANK() OVER (ORDER BY SUM(f.quantity) DESC) AS quantity_rank
FROM fact_sales f
JOIN dim_product p       ON f.product_key = p.product_key
JOIN dim_subcategory sc  ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c      ON sc.category_key = c.category_key
GROUP BY p.product_key, p.product_name, p.brand, c.category_name
ORDER BY total_units_sold DESC
LIMIT 10;


-- @query: bottom_10_products_by_revenue
-- Business question: Which products (that sold at least once) underperform?
-- Excludes products with zero sales — those are a separate "never sold" question, handled below.
SELECT
    p.product_name,
    p.brand,
    c.category_name,
    ROUND(SUM(f.revenue_usd), 2) AS total_revenue_usd,
    SUM(f.quantity)              AS total_units_sold
FROM fact_sales f
JOIN dim_product p       ON f.product_key = p.product_key
JOIN dim_subcategory sc  ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c      ON sc.category_key = c.category_key
GROUP BY p.product_key, p.product_name, p.brand, c.category_name
ORDER BY total_revenue_usd ASC
LIMIT 10;


-- @query: products_never_sold
-- Business question: Are there catalog products with zero recorded sales?
SELECT COUNT(*) AS products_never_sold
FROM dim_product p
LEFT JOIN fact_sales f ON p.product_key = f.product_key
WHERE f.product_key IS NULL;


-- @query: category_revenue
-- Business question: What product categories drive revenue?
SELECT
    c.category_name,
    ROUND(SUM(f.revenue_usd), 2) AS total_revenue_usd,
    SUM(f.quantity)              AS total_units_sold,
    COUNT(DISTINCT f.order_number) AS orders_containing_category,
    ROUND(100.0 * SUM(f.revenue_usd) / (SELECT SUM(revenue_usd) FROM fact_sales), 2) AS pct_of_total_revenue,
    RANK() OVER (ORDER BY SUM(f.revenue_usd) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_product p      ON f.product_key = p.product_key
JOIN dim_subcategory sc ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c     ON sc.category_key = c.category_key
GROUP BY c.category_name
ORDER BY total_revenue_usd DESC;


-- @query: category_growth_yoy
-- Business question: Which categories are growing vs. shrinking? (2021 excluded: partial year)
WITH cat_year AS (
    SELECT
        c.category_name,
        CAST(strftime('%Y', f.order_date) AS INTEGER) AS year,
        SUM(f.revenue_usd) AS revenue_usd
    FROM fact_sales f
    JOIN dim_product p      ON f.product_key = p.product_key
    JOIN dim_subcategory sc ON p.subcategory_key = sc.subcategory_key
    JOIN dim_category c     ON sc.category_key = c.category_key
    WHERE strftime('%Y', f.order_date) != (SELECT strftime('%Y', MAX(order_date)) FROM fact_sales)  -- exclude partial year
    GROUP BY c.category_name, year
)
SELECT
    category_name,
    year,
    ROUND(revenue_usd, 2) AS revenue_usd,
    ROUND(
        100.0 * (revenue_usd - LAG(revenue_usd) OVER (PARTITION BY category_name ORDER BY year))
        / NULLIF(LAG(revenue_usd) OVER (PARTITION BY category_name ORDER BY year), 0)
    , 2) AS yoy_growth_pct
FROM cat_year
ORDER BY category_name, year;


-- @query: product_profitability_top10
-- Business question: Which products are most profitable in absolute terms, and what's their margin?
SELECT
    p.product_name,
    c.category_name,
    ROUND(SUM(f.revenue_usd), 2)  AS total_revenue_usd,
    ROUND(SUM(f.profit_usd), 2)   AS total_profit_usd,
    ROUND(100.0 * SUM(f.profit_usd) / NULLIF(SUM(f.revenue_usd), 0), 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p       ON f.product_key = p.product_key
JOIN dim_subcategory sc  ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c      ON sc.category_key = c.category_key
GROUP BY p.product_key, p.product_name, c.category_name
ORDER BY total_profit_usd DESC
LIMIT 10;


-- @query: category_profit_margin
-- Business question: Which categories are most/least profitable as a % margin (not just absolute $)?
SELECT
    c.category_name,
    ROUND(SUM(f.revenue_usd), 2)  AS total_revenue_usd,
    ROUND(SUM(f.profit_usd), 2)   AS total_profit_usd,
    ROUND(100.0 * SUM(f.profit_usd) / NULLIF(SUM(f.revenue_usd), 0), 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p      ON f.product_key = p.product_key
JOIN dim_subcategory sc ON p.subcategory_key = sc.subcategory_key
JOIN dim_category c     ON sc.category_key = c.category_key
GROUP BY c.category_name
ORDER BY profit_margin_pct DESC;


-- ============================================================================
-- SECTION 3: GEOGRAPHIC ANALYSIS
-- ============================================================================
-- NOTE: geography here is CUSTOMER location (dim_customer.country/state), not
-- store location. This is a deliberate choice — see docs/kpi_framework.md
-- (Phase 10) for why, and channel (online/in-store) analysis below for the
-- store-side view.

-- @query: revenue_by_customer_country
-- Business question: Which countries generate the most revenue?
SELECT
    cu.country,
    ROUND(SUM(f.revenue_usd), 2)     AS total_revenue_usd,
    COUNT(DISTINCT f.order_number)   AS total_orders,
    COUNT(DISTINCT f.customer_key)   AS total_customers,
    ROUND(SUM(f.revenue_usd) * 1.0 / COUNT(DISTINCT f.order_number), 2) AS aov_usd,
    ROUND(100.0 * SUM(f.revenue_usd) / (SELECT SUM(revenue_usd) FROM fact_sales), 2) AS pct_of_total_revenue,
    RANK() OVER (ORDER BY SUM(f.revenue_usd) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_customer cu ON f.customer_key = cu.customer_key
GROUP BY cu.country
ORDER BY total_revenue_usd DESC;


-- @query: revenue_by_customer_state_top15
-- Business question: Which states/regions generate the most revenue?
SELECT
    cu.country,
    cu.state,
    ROUND(SUM(f.revenue_usd), 2)   AS total_revenue_usd,
    COUNT(DISTINCT f.order_number) AS total_orders,
    ROUND(SUM(f.revenue_usd) * 1.0 / COUNT(DISTINCT f.order_number), 2) AS aov_usd
FROM fact_sales f
JOIN dim_customer cu ON f.customer_key = cu.customer_key
GROUP BY cu.country, cu.state
ORDER BY total_revenue_usd DESC
LIMIT 15;


-- @query: revenue_by_channel
-- Business question: How much revenue comes from online vs. in-store, and how do they compare?
SELECT
    CASE WHEN s.is_online = 1 THEN 'Online' ELSE 'In-Store' END AS channel,
    ROUND(SUM(f.revenue_usd), 2)      AS total_revenue_usd,
    COUNT(DISTINCT f.order_number)    AS total_orders,
    SUM(f.quantity)                   AS total_units_sold,
    ROUND(SUM(f.revenue_usd) * 1.0 / COUNT(DISTINCT f.order_number), 2) AS aov_usd,
    ROUND(100.0 * SUM(f.revenue_usd) / (SELECT SUM(revenue_usd) FROM fact_sales), 2) AS pct_of_total_revenue
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
GROUP BY channel
ORDER BY total_revenue_usd DESC;


-- @query: revenue_by_store_country
-- Business question: Which physical-store countries perform best (store-side geography)?
SELECT
    s.country,
    ROUND(SUM(f.revenue_usd), 2)      AS total_revenue_usd,
    COUNT(DISTINCT f.order_number)    AS total_orders,
    COUNT(DISTINCT f.store_key)       AS store_count,
    ROUND(SUM(f.revenue_usd) / COUNT(DISTINCT f.store_key), 2) AS avg_revenue_per_store_usd
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
GROUP BY s.country
ORDER BY total_revenue_usd DESC;
