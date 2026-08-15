"""
Phase 8 — RFM Customer Segmentation.

Computes Recency, Frequency, Monetary scores for every customer who has
placed at least one order (11,887 of 15,266 total customers — see Phase 6;
RFM is undefined for the 3,379 customers with zero orders, so they are
excluded, not scored as "Lost"), and assigns each to a named segment using
a documented, data-driven scoring rule.

Reads data/processed/sales_clean.csv. Writes:
  - data/processed/customer_rfm.csv       (one row per purchasing customer)
  - reports/phase8_rfm_segment_summary.md (segment-level aggregates)

Run from the project root:
    python python/rfm_segmentation.py
"""

from pathlib import Path
from datetime import timedelta
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "phase8_rfm_segment_summary.md"

# ----------------------------------------------------------------------------
# Segment grid: maps (R_score, FM_score) -> segment name.
# FM_score = round(mean(F_score, M_score)) — Frequency and Monetary are
# combined into one axis because Frequency alone has low granularity in this
# dataset (median 2 orders, max 14 — see docs/phase6_findings.md), so F and M
# are blended for a more stable second axis, following common RFM practice.
# ----------------------------------------------------------------------------
SEGMENT_GRID = {
    (5, 1): "New Customers",       (5, 2): "Potential Loyalists", (5, 3): "Potential Loyalists", (5, 4): "Loyal Customers", (5, 5): "Champions",
    (4, 1): "New Customers",       (4, 2): "Potential Loyalists", (4, 3): "Loyal Customers",      (4, 4): "Loyal Customers", (4, 5): "Champions",
    (3, 1): "Promising",           (3, 2): "Need Attention",       (3, 3): "Need Attention",       (3, 4): "Loyal Customers", (3, 5): "Loyal Customers",
    (2, 1): "About To Sleep",      (2, 2): "About To Sleep",       (2, 3): "At Risk",              (2, 4): "At Risk",         (2, 5): "Can't Lose Them",
    (1, 1): "Lost",                (1, 2): "Lost",                 (1, 3): "At Risk",              (1, 4): "Can't Lose Them", (1, 5): "Can't Lose Them",
}


def main():
    sales = pd.read_csv(PROCESSED_DIR / "sales_clean.csv", parse_dates=["Order Date"])

    # Snapshot date: one day after the last order in the dataset. Standard
    # RFM practice — treats "now" as the day after the most recent data point,
    # since this is a static historical dataset, not a live feed.
    snapshot_date = sales["Order Date"].max() + timedelta(days=1)

    rfm = sales.groupby("CustomerKey").agg(
        last_order_date=("Order Date", "max"),
        frequency=("Order Number", "nunique"),
        monetary=("Revenue USD", "sum"),
    ).reset_index()
    rfm["recency_days"] = (snapshot_date - rfm["last_order_date"]).dt.days

    # Quintile scoring. Recency: smaller = better (score 5 = most recent).
    rfm["R_score"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)

    # Frequency: low unique-value count (1-14) makes plain qcut fail on
    # duplicate bin edges, so rank-with-ties-broken-by-order is used to force
    # 5 equal-sized groups — a standard workaround, documented here rather
    # than silently applied.
    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["M_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["FM_score"] = ((rfm["F_score"] + rfm["M_score"]) / 2).round().astype(int)
    rfm["FM_score"] = rfm["FM_score"].clip(1, 5)

    rfm["segment"] = rfm.apply(
        lambda row: SEGMENT_GRID[(row["R_score"], row["FM_score"])], axis=1
    )

    rfm["rfm_score_label"] = (
        rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)
    )

    output_cols = ["CustomerKey", "last_order_date", "recency_days", "frequency",
                    "monetary", "R_score", "F_score", "M_score", "FM_score",
                    "rfm_score_label", "segment"]
    rfm[output_cols].to_csv(PROCESSED_DIR / "customer_rfm.csv", index=False)

    # ---- Segment-level summary ----
    total_customers = len(rfm)
    total_revenue = rfm["monetary"].sum()

    summary = rfm.groupby("segment").agg(
        num_customers=("CustomerKey", "count"),
        total_revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency_days=("recency_days", "mean"),
    ).reset_index()
    summary["pct_of_customers"] = (100 * summary["num_customers"] / total_customers).round(2)
    summary["pct_of_revenue"] = (100 * summary["total_revenue"] / total_revenue).round(2)
    summary = summary.sort_values("total_revenue", ascending=False)

    lines = []
    lines.append("# Phase 8 — RFM Segment Summary")
    lines.append(f"\nSnapshot date used for Recency: **{snapshot_date.date()}** "
                 f"(one day after the last order date in the dataset, {sales['Order Date'].max().date()}).")
    lines.append(f"\nScope: {total_customers:,} customers with at least one order "
                 f"(the 3,379 customers with zero orders — see Phase 6 — are excluded, "
                 f"not scored as 'Lost', since RFM is undefined without a purchase history).\n")

    lines.append("| Segment | Customers | % of Customers | Total Revenue | % of Revenue | Avg Spend | Avg Orders | Avg Recency (days) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['segment']} | {row['num_customers']:,} | {row['pct_of_customers']}% | "
            f"${row['total_revenue']:,.2f} | {row['pct_of_revenue']}% | "
            f"${row['avg_monetary']:,.2f} | {row['avg_frequency']:.2f} | {row['avg_recency_days']:.0f} |"
        )

    lines.append(f"\n**Total across all segments:** {total_customers:,} customers, ${total_revenue:,.2f} revenue "
                 f"(cross-check: matches the {total_customers:,}-customer, "
                 f"${total_revenue:,.2f} totals from Phase 6).")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"RFM table written to {PROCESSED_DIR / 'customer_rfm.csv'}")
    print(f"Segment summary written to {REPORT_PATH}")
    print(summary[["segment", "num_customers", "pct_of_customers", "pct_of_revenue"]].to_string(index=False))


if __name__ == "__main__":
    main()
