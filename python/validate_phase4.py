"""
Phase 4 — Database Validation.

Checks the SQLite database built by python/build_database.py:
- Primary keys enforced (no duplicates on PK columns)
- Foreign keys valid (no orphan references)
- Row counts match the source CSVs exactly
- No unexpected duplicate records
- Referential integrity (SQLite's own foreign_key_check)

Writes reports/phase4_database_validation_report.md and exits non-zero on
any failure.

Run from the project root:
    python python/validate_phase4.py
"""

from pathlib import Path
from datetime import datetime
import sqlite3
import sys
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
DB_PATH = PROCESSED_DIR / "ecommerce_analytics.db"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "phase4_database_validation_report.md"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    checks = []

    def check(name, passed, detail):
        checks.append((name, passed, detail))

    # --- Row counts vs source CSVs ---
    source_counts = {
        "dim_customer": len(pd.read_csv(PROCESSED_DIR / "customers_clean.csv")),
        "dim_product": len(pd.read_csv(PROCESSED_DIR / "products_clean.csv")),
        "dim_store": len(pd.read_csv(PROCESSED_DIR / "stores_clean.csv")),
        "exchange_rate": len(pd.read_csv(PROCESSED_DIR / "exchange_rates_clean.csv")),
        "fact_sales": len(pd.read_csv(PROCESSED_DIR / "sales_clean.csv")),
    }
    for table, expected in source_counts.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        check(f"{table} row count matches source CSV", actual == expected,
              f"table={actual:,}, csv={expected:,}")

    # --- Primary key uniqueness ---
    pk_checks = {
        "dim_customer": "customer_key",
        "dim_product": "product_key",
        "dim_store": "store_key",
        "dim_category": "category_key",
        "dim_subcategory": "subcategory_key",
        "dim_date": "date_key",
    }
    for table, pk in pk_checks.items():
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        distinct = conn.execute(f"SELECT COUNT(DISTINCT {pk}) FROM {table}").fetchone()[0]
        check(f"{table}.{pk} is a valid primary key (unique, no nulls)", total == distinct,
              f"{total:,} rows, {distinct:,} distinct {pk} values")

    total_fact = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    distinct_fact_pk = conn.execute(
        "SELECT COUNT(DISTINCT order_number || '-' || line_item) FROM fact_sales"
    ).fetchone()[0]
    check("fact_sales (order_number, line_item) is a valid composite primary key",
          total_fact == distinct_fact_pk,
          f"{total_fact:,} rows, {distinct_fact_pk:,} distinct composite keys")

    # --- Foreign key integrity (SQLite built-in check) ---
    fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    check("No foreign key violations (PRAGMA foreign_key_check)", len(fk_violations) == 0,
          f"{len(fk_violations)} violation(s): {fk_violations[:5]}" if fk_violations else "0 violations")

    # --- Manual referential integrity spot-checks (belt and suspenders) ---
    orphan_customers = conn.execute("""
        SELECT COUNT(*) FROM fact_sales f
        LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
        WHERE c.customer_key IS NULL
    """).fetchone()[0]
    check("fact_sales.customer_key -> dim_customer fully resolved", orphan_customers == 0,
          f"{orphan_customers} orphan rows")

    orphan_products = conn.execute("""
        SELECT COUNT(*) FROM fact_sales f
        LEFT JOIN dim_product p ON f.product_key = p.product_key
        WHERE p.product_key IS NULL
    """).fetchone()[0]
    check("fact_sales.product_key -> dim_product fully resolved", orphan_products == 0,
          f"{orphan_products} orphan rows")

    orphan_stores = conn.execute("""
        SELECT COUNT(*) FROM fact_sales f
        LEFT JOIN dim_store s ON f.store_key = s.store_key
        WHERE s.store_key IS NULL
    """).fetchone()[0]
    check("fact_sales.store_key -> dim_store fully resolved", orphan_stores == 0,
          f"{orphan_stores} orphan rows")

    orphan_dates = conn.execute("""
        SELECT COUNT(*) FROM fact_sales f
        LEFT JOIN dim_date d ON f.order_date = d.date_key
        WHERE d.date_key IS NULL
    """).fetchone()[0]
    check("fact_sales.order_date -> dim_date fully resolved", orphan_dates == 0,
          f"{orphan_dates} orphan rows")

    orphan_subcats = conn.execute("""
        SELECT COUNT(*) FROM dim_product p
        LEFT JOIN dim_subcategory s ON p.subcategory_key = s.subcategory_key
        WHERE s.subcategory_key IS NULL
    """).fetchone()[0]
    check("dim_product.subcategory_key -> dim_subcategory fully resolved", orphan_subcats == 0,
          f"{orphan_subcats} orphan rows")

    orphan_cats = conn.execute("""
        SELECT COUNT(*) FROM dim_subcategory s
        LEFT JOIN dim_category c ON s.category_key = c.category_key
        WHERE c.category_key IS NULL
    """).fetchone()[0]
    check("dim_subcategory.category_key -> dim_category fully resolved", orphan_cats == 0,
          f"{orphan_cats} orphan rows")

    # --- No unexpected duplicate records ---
    dup_customers = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT customer_key, COUNT(*) c FROM dim_customer GROUP BY customer_key HAVING c > 1
        )
    """).fetchone()[0]
    check("No duplicate customer_key groups in dim_customer", dup_customers == 0,
          f"{dup_customers} duplicate groups")

    # --- Cross-check: total revenue in DB vs CSV (consistency) ---
    db_revenue = conn.execute("SELECT SUM(revenue_usd) FROM fact_sales").fetchone()[0]
    csv_revenue = pd.read_csv(PROCESSED_DIR / "sales_clean.csv")["Revenue USD"].sum()
    check("Total revenue (DB) matches total revenue (CSV)",
          abs(db_revenue - csv_revenue) < 0.01,
          f"DB=${db_revenue:,.2f}, CSV=${csv_revenue:,.2f}")

    # ---- Write report ----
    lines = []
    lines.append("# Phase 4 — Database Validation Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nDatabase: `{DB_PATH.relative_to(DB_PATH.parent.parent.parent)}` (SQLite)\n")
    lines.append("| # | Check | Result | Detail |")
    lines.append("|---|---|---|---|")
    all_passed = True
    for i, (name, passed, detail) in enumerate(checks, 1):
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        lines.append(f"| {i} | {name} | {status} | {detail} |")

    lines.append(f"\n**Overall result: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}**")
    lines.append(f"\n- Total Revenue (fact_sales): **${db_revenue:,.2f}**")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    conn.close()
    print(f"Report written to {REPORT_PATH}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
