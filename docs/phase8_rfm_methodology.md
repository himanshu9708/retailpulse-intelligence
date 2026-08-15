# Phase 8 — RFM Customer Segmentation: Methodology & Findings

Script: [`python/rfm_segmentation.py`](../python/rfm_segmentation.py). Output
table: `data/processed/customer_rfm.csv` (one row per purchasing customer).
Segment summary: [`reports/phase8_rfm_segment_summary.md`](../reports/phase8_rfm_segment_summary.md).

## Methodology

### Scope

RFM is computed for the **11,887 customers who placed at least one order**.
The 3,379 customers in `dim_customer` with zero orders (confirmed in Phase
6) are **excluded**, not labeled "Lost" — Recency, Frequency, and Monetary
are all undefined without a purchase history, and forcing a "Lost" label on
someone who never bought anything would misrepresent them as a churned
customer rather than a non-customer.

### Recency, Frequency, Monetary — Definitions

| Metric | Definition | Direction |
|---|---|---|
| Recency | Days between snapshot date and customer's most recent `Order Date` | Lower = better |
| Frequency | Count of distinct `Order Number` values for the customer | Higher = better |
| Monetary | Sum of `Revenue USD` across all the customer's line items | Higher = better |

**Snapshot date:** 2021-02-21 — one day after the last order date in the
dataset (2021-02-20). This is standard practice for a static historical
dataset: "now" is treated as the day after the data ends, since there's no
live clock to measure against.

### Scoring

Each metric is scored 1–5 using **quintiles of the actual data**
(`pd.qcut`), not fixed day/order thresholds — per the phase's own rule to
not force generic definitions onto data that doesn't support them. Fixed
thresholds like "recent = within 30 days" would be meaningless here: Phase
6 already established this is a long-cycle, durable-goods business where
44.74% of repeat customers have orders spread over more than a year, and
the median customer places only 2 orders total.

* **R_score:** quintile of `recency_days`, reversed so 5 = most recent 20%.
* **F_score:** Frequency has only 14 unique values (1–14 orders, median 2)
  with heavy ties, so plain quintile cuts fail on duplicate bin edges.
  Ties are broken by row order (`rank(method="first")`) before cutting into
  5 equal-sized groups — a documented, standard workaround, not a silent
  fix.
* **M_score:** quintile of total `monetary` value, 5 = highest 20%.
* **FM_score:** `round(mean(F_score, M_score))`. Frequency and Monetary are
  blended into one axis (a common RFM simplification) because Frequency
  alone has low granularity in this dataset — blending with Monetary gives
  a more stable second axis for segmentation.

### Segment Assignment

Each customer's (R_score, FM_score) pair is mapped to a named segment via
a fixed 5×5 grid (see `SEGMENT_GRID` in the script) — a standard RFM
segment grid adapted from common industry practice, using 10 of the
segment names suggested in the project brief. Two suggested names
(**Hibernating**, from the brief's list) were **not used** in the final
grid — their intent is fully covered by **About To Sleep** and **Lost** in
this grid, and introducing a near-duplicate label would only fragment
otherwise-identical customer groups without adding distinct meaning. This
is the "do not blindly use labels the data doesn't support" instruction
applied directly: the grid was kept to the set of labels that map to
genuinely distinct (R, FM) regions.

## Segment Results

*(Full table with all metrics: see `reports/phase8_rfm_segment_summary.md`.
Cross-check: totals reconcile exactly to Phase 6's 11,887 customers and
$55,755,479.59 revenue.)*

| Segment | Customers | % of Customers | % of Revenue |
|---|---|---|---|
| Loyal Customers | 3,396 | 28.57% | 40.13% |
| Champions | 855 | 7.19% | 21.53% |
| At Risk | 1,316 | 11.07% | 13.70% |
| Can't Lose Them | 507 | 4.27% | 8.58% |
| Lost | 1,725 | 14.51% | 4.66% |
| Potential Loyalists | 1,401 | 11.79% | 4.25% |
| Need Attention | 1,117 | 9.40% | 3.93% |
| About To Sleep | 1,197 | 10.07% | 2.97% |
| New Customers | 216 | 1.82% | 0.14% |
| Promising | 157 | 1.32% | 0.11% |

## Findings

* **Fact:** **Champions + Loyal Customers** (35.76% of customers) generate
  **61.66%** of total revenue — the single largest concentration finding
  in the project, more pronounced than the raw revenue-decile analysis in
  Phase 6 because RFM incorporates recency, not just historical spend.
* **Fact:** Champions have by far the highest average spend ($14,039.84)
  and average order count (4.99) of any segment — nearly double the
  average frequency of Loyal Customers (3.03).
* **Fact:** **At Risk + Can't Lose Them + Lost** together represent
  **30.85%** of purchasing customers but only **26.94%** of revenue — a
  large group with meaningfully below-average value concentration,
  consistent with (but not identical to) the "bottom half of customers"
  finding from the Phase 6 decile analysis.
* **Fact:** Checking whether "disengaged" segments are an artifact of the
  broad 2020 revenue decline (Phase 5/7): they are **not** — for At Risk,
  Can't Lose Them, and Lost, **100% of customers' most recent orders fall
  in 2016–2019**, entirely predating the 2020 downturn (e.g. At Risk:
  53.8% of last orders in 2019, remainder 2016–2018; Lost: 37.7% in 2018
  alone, remainder 2016–2017). By contrast, Champions and Loyal Customers
  skew heavily toward 2019–2021 last-order dates (77.3% and 52.4%
  respectively had their last order in 2020). This means the segmentation
  is capturing genuine longer-term customer drop-off, not simply
  penalizing everyone for a company-wide bad year.
* **Observation:** New Customers (216 people) and Promising (157 people)
  are both very small segments with very low average spend (~$356–$374) —
  consistent with Phase 6's finding that 2020 new-customer acquisition
  collapsed (947 new customers vs. 3,104 in 2018); there simply aren't
  many recent, low-history customers left to populate these segments by
  the end of the dataset.

## Limitations

* RFM here is a snapshot as of 2021-02-21, using this static dataset. It
  says nothing about customer behavior after that date.
* The FM-blending approach (averaging F_score and M_score) is a modeling
  choice, not the only valid way to combine these two dimensions —
  documented above so it can be revisited if needed.
* Segment labels describe purchase *behavior patterns*, not customer
  intent or satisfaction — "At Risk" describes recency/frequency/monetary
  decline, not a directly measured churn signal.
