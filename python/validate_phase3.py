"""
Phase 3 — Validation.

Checks the cleaned data/processed/ dataset against the criteria required
before moving to Phase 4:
- No unexpected duplicate transaction records
- Valid dates
- Valid numeric fields
- Consistent categories
- Customer IDs are usable
- Order IDs are usable
- Revenue calculations are consistent

Writes results to reports/phase3_cleaning_validation_report.md and exits
with a non-zero status if any check fails.

Run from the project root:
    python python/validate_phase3.py
"""

from pathlib import Path
from datetime import datetime
import sys
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "phase3_cleaning_validation_report.md"


def main():
    sales = pd.read_csv(PROCESSED_DIR / "sales_clean.csv", parse_dates=["Order Date", "Delivery Date"])
    customers = pd.read_csv(PROCESSED_DIR / "customers_clean.csv", parse_dates=["Birthday"])
    products = pd.read_csv(PROCESSED_DIR / "products_clean.csv")
    stores = pd.read_csv(PROCESSED_DIR / "stores_clean.csv", parse_dates=["Open Date"])

    checks = []

    def check(name, passed, detail):
        checks.append((name, passed, detail))

    # 1. No unexpected duplicate transaction records
    dup_key = sales.duplicated(subset=["Order Number", "Line Item"]).sum()
    check("No duplicate (Order Number, Line Item) records", dup_key == 0,
          f"{dup_key} duplicate transaction keys found")

    # 2. Valid dates
    bad_order_dates = sales["Order Date"].isna().sum()
    check("Order Date fully valid (no unparseable)", bad_order_dates == 0,
          f"{bad_order_dates} unparseable Order Date values")

    delivery_before_order = (sales["Delivery Date"] < sales["Order Date"]).sum()
    check("No Delivery Date before Order Date", delivery_before_order == 0,
          f"{delivery_before_order} rows with delivery before order")

    # 3. Valid numeric fields
    bad_qty = ((sales["Quantity"] <= 0) | sales["Quantity"].isna()).sum()
    check("Quantity valid (>0, non-null)", bad_qty == 0, f"{bad_qty} invalid Quantity values")

    bad_price = (products["Unit Price USD"].isna() | (products["Unit Price USD"] < 0)).sum()
    check("Unit Price USD valid (parsed, non-negative)", bad_price == 0,
          f"{bad_price} invalid Unit Price USD values")

    bad_cost = (products["Unit Cost USD"].isna() | (products["Unit Cost USD"] < 0)).sum()
    check("Unit Cost USD valid (parsed, non-negative)", bad_cost == 0,
          f"{bad_cost} invalid Unit Cost USD values")

    # 4. Consistent categories
    n_categories = products["Category"].nunique()
    cat_key_consistency = products.groupby("CategoryKey")["Category"].nunique()
    check("Category <-> CategoryKey is 1:1 consistent", (cat_key_consistency <= 1).all(),
          f"{(cat_key_consistency > 1).sum()} CategoryKey values map to multiple Category labels")

    # 5. Customer IDs usable
    dup_customer_keys = customers["CustomerKey"].duplicated().sum()
    check("CustomerKey is unique per customer", dup_customer_keys == 0,
          f"{dup_customer_keys} duplicate CustomerKey values")

    orphan_customers = (~sales["CustomerKey"].isin(customers["CustomerKey"])).sum()
    check("All Sales CustomerKey values exist in Customers", orphan_customers == 0,
          f"{orphan_customers} orphan CustomerKey rows in Sales")

    # 6. Order IDs usable
    orders_have_lines = sales.groupby("Order Number")["Line Item"].nunique()
    check("Every Order Number has at least one Line Item", (orders_have_lines >= 1).all(),
          "OK" if (orders_have_lines >= 1).all() else "Some orders have zero line items")

    # 7. Revenue calculations are consistent
    recomputed_revenue = sales["Quantity"] * sales["Unit Price USD"]
    revenue_mismatch = (~((recomputed_revenue - sales["Revenue USD"]).abs() < 1e-6)).sum()
    check("Revenue USD == Quantity x Unit Price USD for every row", revenue_mismatch == 0,
          f"{revenue_mismatch} rows where stored Revenue USD does not match recomputation")

    total_revenue = sales["Revenue USD"].sum()
    check("Total revenue is a finite positive number", total_revenue > 0 and pd.notna(total_revenue),
          f"Total Revenue USD = ${total_revenue:,.2f}")

    negative_profit_rows = (sales["Profit USD"] < 0).sum()
    check("Profit USD has no negative values (Price >= Cost for all products)",
          negative_profit_rows == 0, f"{negative_profit_rows} rows with negative profit")

    # ---- Write report ----
    lines = []
    lines.append("# Phase 3 — Cleaning Validation Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\nValidated against `data/processed/` (output of `python/clean_data.py`).\n")
    lines.append("| # | Check | Result | Detail |")
    lines.append("|---|---|---|---|")
    all_passed = True
    for i, (name, passed, detail) in enumerate(checks, 1):
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False
        lines.append(f"| {i} | {name} | {status} | {detail} |")

    lines.append(f"\n**Overall result: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}**")
    lines.append(f"\n- Total Revenue (USD), full dataset: **${total_revenue:,.2f}**")
    lines.append(f"- Total rows in cleaned Sales: **{len(sales):,}**")
    lines.append(f"- Total unique orders: **{sales['Order Number'].nunique():,}**")
    lines.append(f"- Total unique customers with orders: **{sales['CustomerKey'].nunique():,}**")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {REPORT_PATH}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
