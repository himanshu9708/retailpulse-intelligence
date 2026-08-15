"""
Phase 11 — Power BI Executive Dashboard: Data Export.

Power BI Desktop itself isn't available in this sandboxed Linux
environment (no Windows/GUI), so this project ships (a) a full Power BI
build specification (docs/powerbi_design_spec.md) with DAX measures someone
with Power BI Desktop could use to build the real .pbix, and (b) a working
HTML/JS executive dashboard (powerbi/executive_dashboard.html) as a
functional stand-in, built from the exact same KPI definitions
(docs/kpi_framework.md) and pre-aggregated data.

This script produces that pre-aggregated data as JSON, small enough to
embed client-side while still supporting real Year/Channel filtering
(the dashboard aggregates monthly-grain rows on the fly in JS, rather than
shipping the full 62,884-row transaction table to the browser).

Run from the project root:
    python python/export_dashboard_data.py
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "ecommerce_analytics.db"
OUT_PATH = Path(__file__).resolve().parent.parent / "powerbi" / "dashboard_data.json"


def rows_as_dicts(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    data = {}

    # ---- Overall KPI summary ----
    cur.execute("""
        SELECT
            ROUND(SUM(revenue_usd), 2) AS revenue,
            COUNT(DISTINCT order_number) AS orders,
            COUNT(DISTINCT customer_key) AS customers,
            SUM(quantity) AS units,
            ROUND(SUM(revenue_usd) * 1.0 / COUNT(DISTINCT order_number), 2) AS aov,
            ROUND(SUM(revenue_usd) * 1.0 / COUNT(DISTINCT customer_key), 2) AS revenue_per_customer
        FROM fact_sales
    """)
    data["kpi_summary"] = rows_as_dicts(cur)[0]

    # ---- Monthly overall (revenue, orders, units, distinct customers) ----
    cur.execute("""
        SELECT
            substr(order_date, 1, 7) AS year_month,
            ROUND(SUM(revenue_usd), 2) AS revenue,
            COUNT(DISTINCT order_number) AS orders,
            SUM(quantity) AS units,
            COUNT(DISTINCT customer_key) AS customers
        FROM fact_sales
        GROUP BY 1 ORDER BY 1
    """)
    data["monthly_overall"] = rows_as_dicts(cur)

    # ---- Monthly x Category ----
    cur.execute("""
        SELECT
            substr(f.order_date, 1, 7) AS year_month,
            c.category_name AS category,
            ROUND(SUM(f.revenue_usd), 2) AS revenue,
            SUM(f.quantity) AS units
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_subcategory sc ON p.subcategory_key = sc.subcategory_key
        JOIN dim_category c ON sc.category_key = c.category_key
        GROUP BY 1, 2 ORDER BY 1, 2
    """)
    data["monthly_category"] = rows_as_dicts(cur)

    # ---- Monthly x Country (customer-side geography, per KPI framework) ----
    cur.execute("""
        SELECT
            substr(f.order_date, 1, 7) AS year_month,
            cu.country AS country,
            ROUND(SUM(f.revenue_usd), 2) AS revenue,
            COUNT(DISTINCT f.order_number) AS orders
        FROM fact_sales f
        JOIN dim_customer cu ON f.customer_key = cu.customer_key
        GROUP BY 1, 2 ORDER BY 1, 2
    """)
    data["monthly_country"] = rows_as_dicts(cur)

    # ---- Monthly x Channel ----
    cur.execute("""
        SELECT
            substr(f.order_date, 1, 7) AS year_month,
            CASE WHEN s.is_online = 1 THEN 'Online' ELSE 'In-Store' END AS channel,
            ROUND(SUM(f.revenue_usd), 2) AS revenue,
            COUNT(DISTINCT f.order_number) AS orders
        FROM fact_sales f
        JOIN dim_store s ON f.store_key = s.store_key
        GROUP BY 1, 2 ORDER BY 1, 2
    """)
    data["monthly_channel"] = rows_as_dicts(cur)

    # ---- Top 20 products (overall, with category for client-side filtering) ----
    cur.execute("""
        SELECT
            p.product_name AS product,
            c.category_name AS category,
            ROUND(SUM(f.revenue_usd), 2) AS revenue,
            SUM(f.quantity) AS units
        FROM fact_sales f
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_subcategory sc ON p.subcategory_key = sc.subcategory_key
        JOIN dim_category c ON sc.category_key = c.category_key
        GROUP BY p.product_key, p.product_name, c.category_name
        ORDER BY revenue DESC
        LIMIT 20
    """)
    data["top_products"] = rows_as_dicts(cur)

    # ---- Yearly revenue + growth ----
    cur.execute("""
        WITH yearly AS (
            SELECT CAST(strftime('%Y', order_date) AS INTEGER) AS year, SUM(revenue_usd) AS revenue
            FROM fact_sales GROUP BY 1
        )
        SELECT year, ROUND(revenue, 2) AS revenue,
            ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year)) / NULLIF(LAG(revenue) OVER (ORDER BY year), 0), 2) AS yoy_growth_pct
        FROM yearly ORDER BY year
    """)
    data["yearly_revenue_growth"] = rows_as_dicts(cur)

    # ---- New customers per year ----
    cur.execute("""
        WITH first_order AS (SELECT customer_key, MIN(order_date) AS fo FROM fact_sales GROUP BY customer_key)
        SELECT CAST(strftime('%Y', fo) AS INTEGER) AS year, COUNT(*) AS new_customers
        FROM first_order GROUP BY year ORDER BY year
    """)
    data["new_customers_per_year"] = rows_as_dicts(cur)

    # ---- Repeat vs one-time ----
    cur.execute("""
        WITH co AS (SELECT customer_key, COUNT(DISTINCT order_number) AS oc, SUM(revenue_usd) AS rev
                     FROM fact_sales GROUP BY customer_key)
        SELECT
            CASE WHEN oc = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
            COUNT(*) AS customers, ROUND(SUM(rev), 2) AS revenue
        FROM co GROUP BY customer_type
    """)
    data["repeat_vs_onetime"] = rows_as_dicts(cur)
    conn.close()

    # ---- RFM segments (from Phase 8 output CSV, not the SQLite DB) ----
    import csv
    rfm_path = DB_PATH.parent / "customer_rfm.csv"
    seg_agg = {}
    with open(rfm_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seg = row["segment"]
            seg_agg.setdefault(seg, {"segment": seg, "customers": 0, "revenue": 0.0})
            seg_agg[seg]["customers"] += 1
            seg_agg[seg]["revenue"] += float(row["monetary"])
    for v in seg_agg.values():
        v["revenue"] = round(v["revenue"], 2)
    data["rfm_segments"] = sorted(seg_agg.values(), key=lambda r: -r["revenue"])

    # ---- Cohort retention curve (avg % active by month, full-exposure cohorts, Phase 9) ----
    pct_path = DB_PATH.parent / "cohort_retention_pct.csv"
    counts_path = DB_PATH.parent / "cohort_retention_matrix.csv"
    import pandas as pd
    pct = pd.read_csv(pct_path, index_col=0)
    pct.columns = [int(c) for c in pct.columns]
    pct.index = [pd.Period(i) for i in pct.index]
    last_month = pct.index.max()
    avg_retention = []
    for period in sorted(pct.columns):
        if period == 0:
            continue
        eligible = [c for c in pct.index if (c + period) <= last_month]
        if eligible and period <= 24:  # cap at 24 months for a readable, reliable curve
            avg_retention.append({"month": period, "avg_retention_pct": round(pct.loc[eligible, period].mean(), 2),
                                   "cohorts_averaged": len(eligible)})
    data["cohort_retention_curve"] = avg_retention

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=None, separators=(",", ":")), encoding="utf-8")

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Dashboard data written to {OUT_PATH} ({size_kb:.1f} KB)")
    for k, v in data.items():
        if isinstance(v, list):
            print(f" - {k}: {len(v)} rows")
        else:
            print(f" - {k}: {v}")


if __name__ == "__main__":
    main()
