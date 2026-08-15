# E-Commerce Customer & Sales Intelligence

End-to-end Data Analytics & Business Intelligence project analyzing a global
electronics retailer's sales, customers, and product performance using
**Python, SQL, Power BI, and Tableau**.

> **Status: Phase 8 — RFM Customer Segmentation (complete)**
> This project is being built phase-by-phase. See [`docs/phases.md`](docs/phases.md)
> for the full roadmap and current status. Later phases (cohort analysis,
> dashboards, insights) have **not** been implemented yet.

---

## 1. Project Overview

Retailers generate large volumes of transactional data but often struggle to
convert it into decisions. This project builds an analytics pipeline that takes
raw point-of-sale/e-commerce data and turns it into:

**Raw Data → Clean Data → SQL Analysis → Python Analytics → Customer
Segmentation → BI Dashboards → Business Insights → Recommendations**

The goal is to demonstrate a realistic, reproducible analyst workflow — not a
single notebook or dashboard tutorial.

## 2. Business Questions

1. How is the business performing (revenue, orders, growth)?
2. What products and categories drive revenue?
3. Which customers generate the most value?
4. Who are the most loyal and least engaged customers?
5. How well are customers being retained over time?
6. Which customer segments require attention?
7. Which regions/channels/categories are underperforming?
8. What business actions should management take?

## 3. Dataset

Source data: **Global Electronics Retailer** transactional dataset (provided
as CSV exports), stored under `data/raw/` (untouched) and profiled/cleaned
into `data/processed/` in later phases.

| File | Rows (excl. header) | Description |
|---|---|---|
| `Sales.csv` | 62,884 | Order/line-item level transactions: order number, line item, order/delivery dates, customer, store, product, quantity, currency |
| `Customers.csv` | 15,266 | Customer master data: demographics, location, birthday |
| `Products.csv` | 2,517 | Product catalog: name, brand, color, unit cost/price (USD), category/subcategory |
| `Stores.csv` | 67 | Store master data: country, state, size, open date |
| `Exchange_Rates.csv` | 11,215 | Daily currency exchange rates vs. USD |
| `Data_Dictionary.csv` | 37 | Source-provided field descriptions per table |

Full column-level details are in [`docs/data_dictionary/data_dictionary.md`](docs/data_dictionary/data_dictionary.md),
and the full Phase 2 profiling output (missing values, duplicates, ranges,
referential integrity) is in [`reports/phase2_data_profiling_report.md`](reports/phase2_data_profiling_report.md).

**Confirmed data characteristics (Phase 2 findings — facts, not assumptions):**
* `Sales.csv` has no direct revenue column — revenue is derived as `Quantity × Products.Unit Price USD`, currency-adjusted via `Exchange_Rates.csv`.
* `Delivery Date` is 79.06% missing (structural, not corrupted — 0 cases of delivery before order date).
* `StoreKey = 0` represents the **Online** sales channel (confirmed via `Stores.csv`), covering 20.94% of all sales rows — giving the project a genuine online vs. in-store dimension.
* Referential integrity is fully intact across all tables (0 orphaned foreign keys).
* `Products.csv` price/cost fields are stored as formatted text (e.g. `"$6.62 "`) and require parsing.

**Phase 3 result:** a validated analytical dataset now exists in
`data/processed/` (0 rows dropped, 13/13 automated validation checks pass).
**Total revenue across the full dataset: $55,755,479.59** (computed as
`Quantity × Unit Price USD`, no FX conversion — see
[`docs/cleaning_log.md`](docs/cleaning_log.md) for why).

**Phase 4 result:** cleaned data is now loaded into a validated relational
(SQLite) database at `data/processed/ecommerce_analytics.db`, modeled as a
star schema (`fact_sales` + 6 dimension tables). All 21 schema/integrity
checks pass, including an exact revenue reconciliation between the database
and the Phase 3 CSVs. See [`docs/database_schema.md`](docs/database_schema.md)
and [`reports/phase4_database_validation_report.md`](reports/phase4_database_validation_report.md).

**Phase 5 result:** SQL sales/product/geographic analytics complete —
15 business-question-driven queries, all results reconciling exactly to
**$55,755,479.59** total revenue across every breakdown. Headline findings:
Computers leads at 34.62% of revenue, revenue grew every year 2016-2019 then
fell 49% in 2020, in-store outsells online 79.55% to 20.45%, and the US
alone accounts for 53.58% of revenue. Full results:
[`reports/phase5_sales_analytics_report.md`](reports/phase5_sales_analytics_report.md);
findings summary (Fact vs. Observation): [`docs/phase5_findings.md`](docs/phase5_findings.md).

**Phase 6 result:** SQL customer analytics complete — 9 queries covering
repeat-purchase behavior, revenue concentration, and segment contribution.
Headline findings: **61.18%** of purchasing customers are repeat buyers,
generating **82.39%** of revenue; revenue concentration is moderate (top
10% of customers = 35.98% of revenue, no single "whale" customer); and
22.13% of registered customers have never ordered. Full results:
[`reports/phase6_customer_analytics_report.md`](reports/phase6_customer_analytics_report.md);
findings summary: [`docs/phase6_findings.md`](docs/phase6_findings.md).

**Phase 7 result:** Python EDA complete — 10 figures + computed statistics
surfacing patterns SQL alone didn't show. Headline new finding: revenue by
day-of-week is highly uneven (Saturday peak $13.20M vs. Sunday trough
$0.91M, ~14x gap), verified via order counts across both channels. Also
confirmed April is consistently the lowest-revenue month across all 5 full
years, and order/customer revenue distributions are strongly right-skewed.
Figures: [`reports/figures/phase7/`](reports/figures/phase7/); findings:
[`docs/phase7_findings.md`](docs/phase7_findings.md).

**Phase 8 result:** RFM segmentation complete for all 11,887 purchasing
customers, using quintile-based (data-driven) scoring and a documented
segment grid. Headline finding: **Champions + Loyal Customers (35.76% of
customers) generate 61.66% of revenue.** Verified this concentration isn't
an artifact of the 2020 downturn — 100% of "disengaged" segments' last
orders predate 2020. Full methodology and findings:
[`docs/phase8_rfm_methodology.md`](docs/phase8_rfm_methodology.md); segment
data: [`reports/phase8_rfm_segment_summary.md`](reports/phase8_rfm_segment_summary.md).

## 4. Tech Stack

```text
Python (Pandas, NumPy, Matplotlib, Seaborn)
SQL (PostgreSQL preferred; SQLite as fallback for portability)
Power BI       — executive/business reporting
Tableau        — exploratory customer/product analytics
Git / GitHub   — version control
```

## 5. Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline diagram.

## 6–10. SQL / Python / Dashboards / Insights / Recommendations

Not yet implemented. Each section will be filled in as its corresponding
phase is completed (see roadmap below).

## 11. Limitations (so far)

* Dataset is a static export (no live transactional feed); currency
  conversion introduces approximation depending on which exchange-rate date
  is matched to each order.
* No explicit "channel" (online vs. in-store) field has been confirmed yet —
  to be verified in Phase 2 profiling.
* Any causal claims (e.g. "campaign X caused retention increase") are out of
  scope — this is observational transactional data.

## 12. Future Improvements (out of scope for this project unless added later)

* Customer churn prediction
* Sales forecasting
* Recommendation system
* Automated reporting / scheduled refresh
* Cloud deployment

---

## Repository Structure

```text
ecommerce-customer-sales-analytics/
│
├── data/
│   ├── raw/            # Original, unmodified source CSVs
│   └── processed/      # Cleaned analytical datasets (Phase 3+)
│
├── python/              # EDA, RFM, cohort analysis scripts/modules
├── sql/                  # Schema + analytical SQL queries
├── powerbi/              # Power BI .pbix files
├── tableau/              # Tableau .twbx workbooks
├── notebooks/            # Jupyter notebooks
├── reports/               # Business insights & generated reports/figures
├── docs/                  # Project documentation (this phase)
├── tests/                 # Data quality / validation tests
├── scripts/               # Utility/automation scripts
│
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

## Development Rules

* Built phase-by-phase; each phase is validated and committed before the next begins.
* No fabricated data, metrics, or insights — every claim must trace back to the dataset.
* Facts, calculated metrics, assumptions, and recommendations are always labeled distinctly.
* No machine learning in the core project (analytics-only), unless explicitly added as a future extension.

## Project Phases & Status

See [`docs/phases.md`](docs/phases.md).
