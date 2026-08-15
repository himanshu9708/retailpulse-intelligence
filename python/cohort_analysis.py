"""
Phase 9 — Cohort & Retention Analysis.

Builds monthly acquisition cohorts (based on each customer's first order
month) and a retention matrix showing what % of each cohort is still
active in subsequent months (Month 0, 1, 2, 3, ...).

Context carried forward from Phase 6/8: this is a long-cycle, durable-goods
business (median 2 orders/customer, many repeat gaps exceeding a year), so
month-over-month retention rates are expected to be low in absolute terms —
that is a business-model characteristic, not treated here as a data error
or automatically labeled "bad" without further analysis.

Reads data/processed/sales_clean.csv. Writes:
  - data/processed/cohort_retention_matrix.csv  (counts)
  - data/processed/cohort_retention_pct.csv     (percentages)
  - reports/figures/phase9/cohort_retention_heatmap.png
  - reports/phase9_cohort_analysis_stats.md

Run from the project root:
    python python/cohort_analysis.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
FIG_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures" / "phase9"
STATS_PATH = Path(__file__).resolve().parent.parent / "reports" / "phase9_cohort_analysis_stats.md"


def main():
    sales = pd.read_csv(PROCESSED_DIR / "sales_clean.csv", parse_dates=["Order Date"])
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    orders = sales[["CustomerKey", "Order Number", "Order Date"]].drop_duplicates()
    orders["order_month"] = orders["Order Date"].dt.to_period("M")

    # Cohort month = each customer's first order month
    cohort_month = orders.groupby("CustomerKey")["order_month"].min().rename("cohort_month")
    orders = orders.merge(cohort_month, on="CustomerKey")

    # Period number = months elapsed between order_month and cohort_month
    orders["period_number"] = (
        (orders["order_month"].dt.year - orders["cohort_month"].dt.year) * 12
        + (orders["order_month"].dt.month - orders["cohort_month"].dt.month)
    )

    # Active customers per (cohort_month, period_number)
    cohort_data = (
        orders.groupby(["cohort_month", "period_number"])["CustomerKey"]
        .nunique()
        .reset_index()
        .rename(columns={"CustomerKey": "active_customers"})
    )

    cohort_counts = cohort_data.pivot(index="cohort_month", columns="period_number", values="active_customers")

    # IMPORTANT: pivot() leaves a cell as NaN both when (a) zero customers
    # returned in that period (a real, valid 0% data point) and (b) that
    # period hasn't happened yet for that cohort (genuinely unknown/N/A).
    # These must be treated differently — collapsing them together would
    # silently drop legitimate "0% retention" months from every average.
    # Build an explicit period grid and fill only the "occurred but zero"
    # cells with 0, leaving genuinely future periods as NaN.
    last_month = orders["order_month"].max()
    max_period = cohort_counts.columns.max()
    cohort_counts = cohort_counts.reindex(columns=range(0, max_period + 1))
    for c in cohort_counts.index:
        max_valid_period = (last_month - c).n  # months of possible exposure for this cohort
        valid_cols = [p for p in cohort_counts.columns if p <= max_valid_period]
        cohort_counts.loc[c, valid_cols] = cohort_counts.loc[c, valid_cols].fillna(0)
        # columns beyond max_valid_period are left as NaN (period hasn't occurred yet)

    cohort_sizes = cohort_counts[0]  # Month 0 = cohort size by definition
    cohort_pct = cohort_counts.divide(cohort_sizes, axis=0) * 100

    cohort_counts.to_csv(PROCESSED_DIR / "cohort_retention_matrix.csv")
    cohort_pct.round(2).to_csv(PROCESSED_DIR / "cohort_retention_pct.csv")

    # ------------------------------------------------------------------
    # Only compute "average retention per period" using cohorts that had
    # enough elapsed time to reach that period — otherwise later cohorts
    # (which by definition can't have reached month 6, 12, etc.) would
    # drag the average down artificially. This is the standard cohort
    # analysis practice: only average over cohorts with full exposure.
    # ------------------------------------------------------------------
    last_month = orders["order_month"].max()
    n_periods = cohort_pct.shape[1]
    valid_avg = {}
    for period in cohort_pct.columns:
        # A cohort has "full exposure" to `period` if cohort_month + period <= last_month
        eligible_cohorts = [c for c in cohort_pct.index if (c + period) <= last_month]
        if eligible_cohorts:
            valid_avg[period] = cohort_pct.loc[eligible_cohorts, period].mean()
    avg_retention_by_period = pd.Series(valid_avg).sort_index()

    # ------------------------------------------------------------------
    # Trend: is Month-1 retention improving or declining over successive
    # cohorts? Only look at cohorts with full exposure to Month 1.
    # ------------------------------------------------------------------
    month1_eligible = [c for c in cohort_pct.index if (c + 1) <= last_month]
    month1_retention = cohort_pct.loc[month1_eligible, 1].dropna()

    # Best / worst cohorts by Month-1 retention (only eligible cohorts, to
    # keep the comparison fair — an incomplete cohort can't be "worst").
    best_cohort = month1_retention.idxmax()
    worst_cohort = month1_retention.idxmin()

    # Correlation between cohort start order (time) and Month-1 retention,
    # as a simple trend signal.
    trend_x = np.arange(len(month1_retention))
    trend_corr = np.corrcoef(trend_x, month1_retention.values)[0, 1] if len(month1_retention) > 2 else np.nan

    # ------------------------------------------------------------------
    # Heatmap(s)
    # ------------------------------------------------------------------
    # A single 62x62 annotated heatmap is unreadable (digits overlap). Two
    # views instead: (1) a full-range heatmap with color only, showing the
    # overall retention-decay shape across all 62 cohorts/periods, and
    # (2) an annotated zoomed-in heatmap limited to the first 12 months —
    # the standard, readable cohort-analysis window — with actual numbers.
    color_max = cohort_pct.drop(columns=[0]).max().max()

    plt.figure(figsize=(16, 10))
    sns.heatmap(
        cohort_pct, annot=False, cmap="YlGnBu", vmin=0, vmax=color_max,
        cbar_kws={"label": "% of cohort still active"},
    )
    plt.title("Monthly Cohort Retention Heatmap — Full Range (color only; see zoomed version for numbers)")
    plt.xlabel("Months Since First Purchase")
    plt.ylabel("Cohort (First Purchase Month)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "cohort_retention_heatmap_full.png", bbox_inches="tight")
    plt.close()

    zoom_periods = [p for p in cohort_pct.columns if p <= 12]
    cohort_pct_zoom = cohort_pct[zoom_periods]
    plt.figure(figsize=(11, 14))
    sns.heatmap(
        cohort_pct_zoom, annot=True, fmt=".0f", cmap="YlGnBu", vmin=0, vmax=color_max,
        cbar_kws={"label": "% of cohort still active"}, linewidths=0.3, annot_kws={"size": 7},
    )
    plt.title("Monthly Cohort Retention Heatmap — Months 0-12 (zoomed, annotated)")
    plt.xlabel("Months Since First Purchase")
    plt.ylabel("Cohort (First Purchase Month)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "cohort_retention_heatmap_zoom.png", bbox_inches="tight")
    plt.close()

    # Supplementary: retention curve (avg % active by month, full-exposure cohorts only)
    # Period 0 is excluded from the plot — it's trivially 100% by definition
    # and including it compresses the y-axis, hiding the real 0-10% variation
    # that matters in periods 1+.
    plt.figure(figsize=(9, 5))
    avg_retention_by_period.drop(0).plot(kind="line", marker="o", markersize=4, color="#4C72B0")
    plt.title("Average Retention Curve, Months 1+\n(averaged only over cohorts with full exposure to that period; Month 0 = 100% by definition, omitted)")
    plt.xlabel("Months Since First Purchase")
    plt.ylabel("% of Cohort Still Active")
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "avg_retention_curve.png", bbox_inches="tight")
    plt.close()

    # ------------------------------------------------------------------
    # Write stats report
    # ------------------------------------------------------------------
    lines = []
    lines.append("# Phase 9 — Cohort Analysis Computed Statistics\n")
    lines.append(f"- Number of monthly cohorts: {len(cohort_counts)} "
                 f"(first cohort: {cohort_counts.index.min()}, last cohort: {cohort_counts.index.max()})")
    lines.append(f"- Cohort sizes range from {cohort_sizes.min()} to {cohort_sizes.max()} customers\n")

    lines.append("## Average Retention by Period (full-exposure cohorts only)\n")
    lines.append("| Months Since First Purchase | Avg % Active | Cohorts Averaged |")
    lines.append("|---|---|---|")
    for period, val in avg_retention_by_period.items():
        n_elig = len([c for c in cohort_pct.index if (c + period) <= last_month])
        lines.append(f"| {period} | {val:.2f}% | {n_elig} |")

    lines.append(f"\n## Month-1 Retention Trend\n")
    lines.append(f"- Cohorts with full exposure to Month 1: {len(month1_retention)}")
    lines.append(f"- Best Month-1 retention: {best_cohort} ({month1_retention[best_cohort]:.2f}%)")
    lines.append(f"- Worst Month-1 retention: {worst_cohort} ({month1_retention[worst_cohort]:.2f}%)")
    lines.append(f"- Month-1 retention mean: {month1_retention.mean():.2f}%, std dev: {month1_retention.std():.2f}%")
    lines.append(f"- Correlation between cohort chronological order and Month-1 retention: {trend_corr:.3f} "
                 f"({'weak/no trend' if abs(trend_corr) < 0.3 else ('improving over time' if trend_corr > 0 else 'declining over time')})\n")

    lines.append("## Month-1 Retention by Cohort (chronological)\n")
    lines.append("| Cohort | Cohort Size | Month-1 Retention % |")
    lines.append("|---|---|---|")
    for c in month1_retention.index:
        lines.append(f"| {c} | {cohort_sizes[c]} | {month1_retention[c]:.2f}% |")

    STATS_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Cohort matrices written to {PROCESSED_DIR}")
    print(f"Figures written to {FIG_DIR}")
    print(f"Stats written to {STATS_PATH}")
    print(f"\nAvg retention by period (full-exposure cohorts only):\n{avg_retention_by_period.round(2)}")


if __name__ == "__main__":
    main()
