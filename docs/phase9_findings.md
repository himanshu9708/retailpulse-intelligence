# Phase 9 — Cohort & Retention Analysis: Findings

Script: [`python/cohort_analysis.py`](../python/cohort_analysis.py). Full
matrices: `data/processed/cohort_retention_matrix.csv` (counts) and
`cohort_retention_pct.csv` (percentages). Computed stats:
[`reports/phase9_cohort_analysis_stats.md`](../reports/phase9_cohort_analysis_stats.md).
Figures: [`reports/figures/phase9/`](../reports/figures/phase9/).

## Methodology

* **Cohort definition:** each customer's cohort = the calendar month of
  their first order (`Order Date`, not registration date).
* **Period number:** months elapsed between an order and the customer's
  cohort month (0, 1, 2, ...).
* **Retention %:** for a given (cohort, period), the % of that cohort's
  original size (period 0) that placed at least one order in that period.
* **Bug caught and fixed during this phase:** a naive pivot of
  (cohort, period) → active-customer-count leaves a cell blank both when
  (a) genuinely zero customers returned that month, and (b) the period
  hasn't happened yet for that cohort. These are different things — (a) is
  a real 0% data point, (b) is legitimately unknown. The first version of
  this script conflated them (dropped both as missing), which inflated
  every average retention figure by silently excluding real zero months.
  Fixed by explicitly filling "occurred but zero" cells with 0 while
  leaving genuinely future cells as `NaN`. Verified directly against a
  known case: the 2017-03 cohort (98 customers) had 0 of them return in
  month 1 — a true 0%, now correctly counted rather than dropped.
* **"Average retention by period" only uses cohorts with full exposure**
  to that period (i.e., cohort start + period ≤ last month in the
  dataset). Without this, later cohorts — which by definition can't have
  reached month 12, 24, etc. yet — would silently pull long-horizon
  averages down.

## Retention Level (Context From Prior Phases)

* **Fact:** Average Month-1 retention (full-exposure cohorts only) is
  **2.84%**. This is low in absolute terms, but expected given this
  project's own prior findings: Phase 6 showed this is a durable-goods,
  long-purchase-cycle business (median 2 orders per customer over the
  entire ~5-year dataset, with 44.74% of repeat customers spacing their
  orders more than a year apart). A month-to-month retention lens is a
  demanding standard for a product category people don't buy monthly —
  low absolute retention here reflects the business model, not
  necessarily a problem, and should not be compared to subscription or
  consumables-business retention benchmarks.
* **Fact:** Retention gradually **rises** from ~2.8% at Month 1 to a peak
  around **Month 30 (4.46%)**, before declining in the final ~15 months of
  the curve (Months 48–61). See `avg_retention_curve.png`.
* **Important caveat on the tail:** the decline after Month 48 is based on
  very few eligible cohorts (14 cohorts at Month 48, down to just **1**
  cohort at Month 61) — see the "Cohorts Averaged" column in
  `reports/phase9_cohort_analysis_stats.md`. This tail is not treated as a
  reliable "retention gets worse long-term" signal; it's a small-sample
  artifact and is flagged as such rather than reported as a trend.

## Are Customers Becoming More or Less Likely to Return? (Required Question)

* **Fact:** Comparing Month-1 retention across the 61 eligible cohorts in
  chronological order, the correlation between cohort start time and
  Month-1 retention is **0.183** — a **weak, not meaningfully positive or
  negative** relationship. This is a materially different (and more
  accurate) conclusion than an earlier draft of this analysis produced
  (0.491, "improving") before the zero-vs-missing bug above was fixed.
* **Answer:** Based on this dataset, there is **no strong evidence that
  customers are becoming more or less likely to return** over the life of
  the business. Early-2019 cohorts do show somewhat higher Month-1
  retention than 2016–2017 cohorts on average (visible as a light
  diagonal band in `cohort_retention_heatmap_full.png`), but the
  correlation is too weak, and individual cohort-to-cohort variation too
  large, to call this a confirmed trend rather than noise.

## Best / Worst Performing Cohorts

* **Fact (unrestricted):** Best Month-1 retention is **2018-04 (8.70%)**;
  worst is **2017-03 (0.00%)**. However, the 2018-04 cohort had only 23
  customers — its 8.70% figure means just 2 people returned, so this
  "best" result is not statistically robust and shouldn't be read as a
  meaningfully different cohort experience.
* **Fact (restricted to cohorts ≥100 customers, for a reliable
  comparison):** Best Month-1 retention among larger cohorts is
  **2019-11 (8.64%, 220 customers)**; worst is **2019-03 (0.00%, 135
  customers)**. Even among reasonably sized cohorts, Month-1 retention
  swings from 0% to ~8.6% — cohort-to-cohort volatility is real and
  substantial, not just a small-sample artifact.

## Cohort Size Trend

* **Fact:** Monthly cohort sizes (new first-time customers per month)
  ranged from 19 to 482 across the dataset, consistent with Phase 6's
  acquisition finding: sizes generally grew through 2018, then declined
  sharply from 2020 onward (e.g. 2020-04: 19 customers, 2020-08: 29,
  2020-11: 33 — an order of magnitude below the 2018 peak months).

## Limitations

* Retention is measured by **any purchase in a given month**, not by
  engagement, satisfaction, or intent — a customer who simply hasn't
  needed to buy again yet (plausible for durable electronics) looks
  identical in this data to one who has churned.
* Long-horizon periods (40+ months) are based on shrinking numbers of
  eligible cohorts and should be read with proportionally less
  confidence — this is stated explicitly in the stats report's "Cohorts
  Averaged" column rather than hidden in an aggregate chart.
* This is month-grain cohort analysis as specified in the project brief;
  a quarter- or year-grain view (arguably more natural for this specific
  business's purchase cadence) was not built in this phase but would be a
  reasonable, low-effort future extension using the same underlying
  `period_number` calculation.
