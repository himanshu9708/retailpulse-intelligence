# E-Commerce Customer & Sales Intelligence

End-to-end Data Analytics & Business Intelligence project analyzing a global
electronics retailer's sales, customers, and product performance using
**Python, SQL, Power BI, and Tableau**.

> **Status: Phase 1 — Project Planning & Repository Setup (in progress)**
> This project is being built phase-by-phase. See [`docs/phases.md`](docs/phases.md)
> for the full roadmap and current status. Later phases (cleaning, SQL modeling,
> RFM, cohort analysis, dashboards, insights) have **not** been implemented yet.

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

Full column-level details are in [`docs/dataset_requirements.md`](docs/dataset_requirements.md).
A deeper profiling report (missing values, duplicates, ranges, data-quality
issues) will be produced in **Phase 2** and is intentionally not included here.

**Known limitation (documented now, addressed later):** `Sales.csv` does not
include a price/revenue column directly — revenue must be derived by joining
Sales → Products (`Unit Price USD`) and converting currencies via
`Exchange_Rates.csv` where `Currency Code != USD`. This join logic will be
formalized in Phase 4 (data modeling) and Phase 5 (SQL analytics).

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
