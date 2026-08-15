-- ============================================================================
-- Phase 6 — SQL Customer Analytics
-- ============================================================================
-- Every query answers a specific question about customer purchasing
-- behavior. Run against data/processed/ecommerce_analytics.db via
-- python/run_sql_analytics.py (same runner as Phase 5).
--
-- Scope note: "customers" here always means the 11,887 CustomerKeys that
-- appear in fact_sales at least once (of 15,266 total in dim_customer).
-- The other 3,379 customers exist in the customer master data but have
-- never placed an order — a separate fact, reported below.
-- ============================================================================


-- @query: customers_with_zero_orders
-- Business question: How many registered customers have never purchased?
SELECT
    (SELECT COUNT(*) FROM dim_customer) AS total_customers_in_master_data,
    (SELECT COUNT(DISTINCT customer_key) FROM fact_sales) AS customers_with_at_least_one_order,
    (SELECT COUNT(*) FROM dim_customer) - (SELECT COUNT(DISTINCT customer_key) FROM fact_sales) AS customers_never_ordered,
    ROUND(
        100.0 * ((SELECT COUNT(*) FROM dim_customer) - (SELECT COUNT(DISTINCT customer_key) FROM fact_sales))
        / (SELECT COUNT(*) FROM dim_customer)
    , 2) AS pct_never_ordered;


-- @query: repeat_vs_onetime_customers
-- Business question: What percentage of customers are repeat purchasers?
-- "Repeat" = placed 2+ distinct orders (by Order Number), not just 2+ line items.
WITH customer_orders AS (
    SELECT customer_key, COUNT(DISTINCT order_number) AS order_count
    FROM fact_sales
    GROUP BY customer_key
)
SELECT
    CASE WHEN order_count = 1 THEN 'One-time (1 order)' ELSE 'Repeat (2+ orders)' END AS customer_type,
    COUNT(*) AS num_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_orders), 2) AS pct_of_customers
FROM customer_orders
GROUP BY customer_type;


-- @query: revenue_contribution_repeat_vs_onetime
-- Business question: Do repeat customers also generate disproportionate revenue,
-- or just disproportionate order counts?
WITH customer_orders AS (
    SELECT customer_key, COUNT(DISTINCT order_number) AS order_count, SUM(revenue_usd) AS revenue_usd
    FROM fact_sales
    GROUP BY customer_key
)
SELECT
    CASE WHEN order_count = 1 THEN 'One-time (1 order)' ELSE 'Repeat (2+ orders)' END AS customer_type,
    COUNT(*) AS num_customers,
    ROUND(SUM(revenue_usd), 2) AS total_revenue_usd,
    ROUND(100.0 * SUM(revenue_usd) / (SELECT SUM(revenue_usd) FROM fact_sales), 2) AS pct_of_total_revenue,
    ROUND(AVG(revenue_usd), 2) AS avg_revenue_per_customer_usd
FROM customer_orders
GROUP BY customer_type;


-- @query: purchase_frequency_distribution
-- Business question: How many orders does a typical customer place?
WITH customer_orders AS (
    SELECT customer_key, COUNT(DISTINCT order_number) AS order_count
    FROM fact_sales
    GROUP BY customer_key
)
SELECT
    order_count AS orders_placed,
    COUNT(*) AS num_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_orders), 2) AS pct_of_customers
FROM customer_orders
GROUP BY order_count
ORDER BY order_count;


-- @query: top_20_customers_by_revenue
-- Business question: Who are the highest-value customers?
SELECT
    cu.customer_key,
    cu.name,
    cu.country,
    COUNT(DISTINCT f.order_number)  AS total_orders,
    ROUND(SUM(f.revenue_usd), 2)    AS total_revenue_usd,
    RANK() OVER (ORDER BY SUM(f.revenue_usd) DESC) AS revenue_rank
FROM fact_sales f
JOIN dim_customer cu ON f.customer_key = cu.customer_key
GROUP BY cu.customer_key, cu.name, cu.country
ORDER BY total_revenue_usd DESC
LIMIT 20;


-- @query: revenue_concentration_deciles
-- Business question: Is revenue concentrated among a small number of customers?
-- Splits purchasing customers into 10 equal-size groups (deciles) by their
-- individual revenue using NTILE, then shows how much total revenue each
-- decile controls. Decile 1 = highest-spending 10% of customers.
WITH customer_revenue AS (
    SELECT customer_key, SUM(revenue_usd) AS revenue_usd
    FROM fact_sales
    GROUP BY customer_key
),
deciled AS (
    SELECT
        customer_key,
        revenue_usd,
        NTILE(10) OVER (ORDER BY revenue_usd DESC) AS decile
    FROM customer_revenue
)
SELECT
    decile,
    COUNT(*)                       AS num_customers,
    ROUND(SUM(revenue_usd), 2)     AS decile_revenue_usd,
    ROUND(100.0 * SUM(revenue_usd) / (SELECT SUM(revenue_usd) FROM customer_revenue), 2) AS pct_of_total_revenue,
    ROUND(
        100.0 * SUM(SUM(revenue_usd)) OVER (ORDER BY decile) / (SELECT SUM(revenue_usd) FROM customer_revenue)
    , 2) AS cumulative_pct_of_revenue
FROM deciled
GROUP BY decile
ORDER BY decile;


-- @query: new_customers_per_year
-- Business question: Is the customer base growing? How many new customers acquired each year?
-- "New" = the year of a customer's first-ever order (first-order-year, not registration date).
WITH first_order AS (
    SELECT customer_key, MIN(order_date) AS first_order_date
    FROM fact_sales
    GROUP BY customer_key
)
SELECT
    CAST(strftime('%Y', first_order_date) AS INTEGER) AS year,
    COUNT(*) AS new_customers,
    CASE WHEN CAST(strftime('%Y', first_order_date) AS INTEGER) =
              (SELECT CAST(strftime('%Y', MAX(order_date)) AS INTEGER) FROM fact_sales)
         THEN 'PARTIAL YEAR' ELSE 'FULL YEAR' END AS year_completeness
FROM first_order
GROUP BY year
ORDER BY year;


-- @query: avg_spend_and_frequency_by_country
-- Business question: Which customer segments (by country) generate the majority of revenue,
-- and how do their spending patterns differ?
WITH customer_summary AS (
    SELECT
        f.customer_key,
        cu.country,
        COUNT(DISTINCT f.order_number) AS order_count,
        SUM(f.revenue_usd) AS revenue_usd
    FROM fact_sales f
    JOIN dim_customer cu ON f.customer_key = cu.customer_key
    GROUP BY f.customer_key, cu.country
)
SELECT
    country,
    COUNT(*) AS num_customers,
    ROUND(AVG(order_count), 2) AS avg_orders_per_customer,
    ROUND(AVG(revenue_usd), 2) AS avg_revenue_per_customer_usd,
    ROUND(SUM(revenue_usd), 2) AS total_revenue_usd,
    ROUND(100.0 * SUM(revenue_usd) / (SELECT SUM(revenue_usd) FROM fact_sales), 2) AS pct_of_total_revenue
FROM customer_summary
GROUP BY country
ORDER BY total_revenue_usd DESC;


-- @query: customer_lifespan_summary
-- Business question: Over what time span do customers typically keep purchasing
-- (single-visit vs. spread over months/years)?
WITH customer_span AS (
    SELECT
        customer_key,
        MIN(order_date) AS first_order,
        MAX(order_date) AS last_order,
        COUNT(DISTINCT order_number) AS order_count,
        CAST(julianday(MAX(order_date)) - julianday(MIN(order_date)) AS INTEGER) AS lifespan_days
    FROM fact_sales
    GROUP BY customer_key
)
SELECT
    CASE
        WHEN order_count = 1 THEN 'Single order (no lifespan)'
        WHEN lifespan_days = 0 THEN 'Multiple orders, same day'
        WHEN lifespan_days <= 30 THEN '2+ orders within 30 days'
        WHEN lifespan_days <= 180 THEN '2+ orders, 31-180 days apart'
        WHEN lifespan_days <= 365 THEN '2+ orders, 181-365 days apart'
        ELSE '2+ orders, over 1 year apart'
    END AS lifespan_bucket,
    COUNT(*) AS num_customers,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_span), 2) AS pct_of_customers
FROM customer_span
GROUP BY lifespan_bucket
ORDER BY num_customers DESC;
