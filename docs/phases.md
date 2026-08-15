# Development Phases & Status

Rule: each phase is completed and validated before the next one begins.
Nothing below "Not started" has been implemented.

| # | Phase | Deliverable | Status |
|---|---|---|---|
| 1 | Project Planning & Repository Setup | Repo structure, docs, config files | ✅ Done |
| 2 | Dataset Ingestion & Data Understanding | Data profiling report + data dictionary | ✅ Done (this commit) |
| 3 | Data Cleaning & Validation | `data/processed/` clean dataset + decisions log | ✅ Done (this commit) |
| 4 | SQL Database & Data Modeling | Schema + loaded relational DB | ✅ Done (this commit) |
| 5 | SQL Sales Analytics | Revenue/product/geo SQL queries | ✅ Done (this commit) |
| 6 | SQL Customer Analytics | Customer behavior SQL queries | ✅ Done (this commit) |
| 7 | Python Exploratory Data Analysis | EDA notebook/report | ✅ Done (this commit) |
| 8 | RFM Customer Segmentation | RFM scores + segments | ⬜ Not started |
| 9 | Cohort & Retention Analysis | Cohort retention matrix | ⬜ Not started |
| 10 | Business KPI Framework | KPI dictionary | ⬜ Not started |
| 11 | Power BI Executive Dashboard | `.pbix` file | ⬜ Not started |
| 12 | Tableau Customer & Product Analytics | `.twbx` workbook/story | ⬜ Not started |
| 13 | Business Insights & Recommendations | Insights report | ⬜ Not started |
| 14 | Testing & Data Quality | Validation scripts | ⬜ Not started |
| 15 | Documentation & Portfolio Prep | Final README polish | ⬜ Not started |

## Phase 1 — Detail

**Objective:** Define project scope, architecture, tech stack, and repo structure.

**Deliverables:**
- Repository folder structure (`data/`, `python/`, `sql/`, `powerbi/`, `tableau/`, `notebooks/`, `reports/`, `docs/`, `tests/`, `scripts/`)
- `README.md`, `requirements.txt`, `.gitignore`, `.env.example`
- Documentation: objective, business questions, tech stack, architecture, dataset requirements, phase roadmap

**Explicitly NOT done in this phase:** data cleaning, SQL analysis, RFM, cohort analysis, dashboards, statistical analysis.

**Validation:**
- [x] Repository structure exists
- [x] Configuration files exist (`requirements.txt`, `.gitignore`, `.env.example`)
- [x] `README.md` exists and documents the project
- [x] Dataset requirements documented and checked against the actual provided files (6 CSVs: Sales, Customers, Products, Stores, Exchange_Rates, Data_Dictionary)

**Commit:** `chore: initialize ecommerce analytics project`

## Phase 2 — Detail

**Objective:** Load the raw dataset and understand its structure, quality, and content before any cleaning.

**Deliverables:**
- `python/profile_data.py` — reproducible profiling script (reads `data/raw/` only, writes a report; makes no changes to the data)
- `reports/phase2_data_profiling_report.md` — generated profiling report (row/column counts, dtypes, missing values, duplicates, cardinalities, date ranges, categorical values, numeric ranges, referential integrity checks)
- `docs/data_dictionary/data_dictionary.md` — column-level data dictionary (source description + verified business meaning) for all 6 tables

**Explicitly NOT done in this phase:** permanent data cleaning, feature engineering, RFM, cohort analysis, dashboards.

**Key verified findings (facts, not assumptions):**
- No direct revenue column — must be derived from `Quantity × Unit Price USD`, currency-adjusted.
- `Delivery Date` is 79.06% missing (49,719 / 62,884 rows), with 0 logically invalid (delivery-before-order) cases.
- `StoreKey = 0` = "Online" channel (20.94% of sales rows) — confirmed via `Stores.csv`.
- Full referential integrity across Sales ↔ Customers/Products/Stores/Exchange_Rates (0 orphan keys, 0 missing FX currency coverage).
- `Products.csv` price/cost fields are formatted as text (e.g. `"$6.62 "`) and need parsing.
- 148 duplicate customer names map to distinct `CustomerKey`s (not the same person).
- 10 missing `State Code` values in Customers.csv; 1 missing `Square Meters` in Stores.csv (the Online "store" — expected).

**Validation:**
- [x] Profiling script runs end-to-end against `data/raw/` without modifying it
- [x] Report generated with real, verifiable numbers (no estimates)
- [x] Data dictionary covers all 6 tables with source description + business meaning
- [x] Data-quality issues documented as facts, with open items carried into Phase 3

**Commit:** `feat: add dataset profiling and data dictionary`

## Phase 3 — Detail

**Objective:** Create a reliable analytical dataset in `data/processed/`, with every cleaning decision documented and validated. `data/raw/` remains untouched.

**Deliverables:**
- `python/clean_data.py` — reproducible cleaning script (raw → processed)
- `python/validate_phase3.py` — automated validation (13 checks; writes `reports/phase3_cleaning_validation_report.md`)
- `docs/cleaning_log.md` — every decision as Problem → Decision → Reason
- `data/processed/` — 5 cleaned CSVs (sales, customers, products, stores, exchange rates)

**Key decisions (see `docs/cleaning_log.md` for full detail):**
- Parsed `Products.csv` price/cost text fields (`"$6.62 "`) to numeric.
- `Revenue USD = Quantity × Unit Price USD` — **no FX conversion applied**, since `Unit Price USD` is already USD-denominated and `Exchange_Rates.csv` converts USD → local currency (verified: USD rate is always 1.0), not the reverse.
- `Delivery Date` nulls kept as-is (not imputed/dropped) with a new `Is_Delivered` flag — dropping would remove ~79% of revenue.
- `Stores.csv` gets an explicit `Is_Online` flag instead of relying on the `StoreKey == 0` convention.
- No rows dropped anywhere — 0 duplicates, 0 orphan keys, no outliers warranting removal (all confirmed in Phase 2).

**Explicitly NOT done in this phase:** SQL modeling, RFM, cohort analysis, dashboards.

**Validation (all 13 automated checks passed):**
- [x] No unexpected duplicate transaction records
- [x] Valid dates (Order Date 100% valid; 0 delivery-before-order cases)
- [x] Valid numeric fields (Quantity, Unit Price/Cost all pass range checks)
- [x] Consistent categories (Category ↔ CategoryKey 1:1)
- [x] Customer IDs usable (unique, 0 orphans in Sales)
- [x] Order IDs usable (every order has ≥1 line item)
- [x] Revenue calculations are consistent (`Revenue USD` matches recomputation for all 62,884 rows; total = $55,755,479.59)

**Commit:** `feat: implement data cleaning and validation`

## Phase 4 — Detail

**Objective:** Load the cleaned data into a relational database with a documented schema, proper keys, and validated referential integrity.

**Engine decision:** SQLite (no PostgreSQL server available in this sandboxed environment — no network access). Schema is written in Postgres-compatible SQL (`sql/schema.sql`) with a SQLite-adapted loader, documented in `docs/database_schema.md`.

**Deliverables:**
- `sql/schema.sql` — Postgres-flavored DDL (canonical schema documentation)
- `python/build_database.py` — builds `data/processed/ecommerce_analytics.db` from Phase 3's cleaned CSVs (idempotent, rebuildable)
- `python/validate_phase4.py` — 21 automated checks; writes `reports/phase4_database_validation_report.md`
- `docs/database_schema.md` — schema documentation, ERD, engine-choice rationale

**Design:** Star schema — `fact_sales` (62,884 rows, one per order line item, grain preserved from Phase 3) surrounded by `dim_customer`, `dim_store`, `dim_product`, `dim_subcategory`, `dim_category`, `dim_date`, plus a standalone `exchange_rate` reference table.

**Explicitly NOT done in this phase:** business-question SQL analytics (Phase 5/6), RFM, cohort analysis, dashboards.

**Validation (all 21 checks passed):**
- [x] Primary keys valid (unique, no nulls) on every table, including composite PK on `fact_sales`
- [x] Foreign keys valid (`PRAGMA foreign_key_check` = 0 violations; manual join checks confirm 0 orphan rows on every relationship)
- [x] Row counts match source CSVs exactly on every table
- [x] No duplicate records
- [x] Referential integrity fully intact end-to-end (customer → sales, product → subcategory → category, store, date)
- [x] Total revenue in the database ($55,755,479.59) matches the Phase 3 CSV exactly

**Commit:** `feat: create ecommerce analytics database schema`

## Phase 5 — Detail

**Objective:** Use SQL to answer core sales, product, and geographic business questions — every query tied to a specific business question, not written to demonstrate syntax.

**Deliverables:**
- `sql/05_sales_analytics.sql` — 15 named queries across 3 sections (KPIs, Product Analysis, Geographic Analysis), using JOINs, CTEs, GROUP BY, CASE, window functions (RANK, LAG), and date functions (strftime)
- `python/run_sql_analytics.py` — reusable runner that executes any `@query`-tagged `.sql` file against the database and renders a markdown report with actual results
- `reports/phase5_sales_analytics_report.md` — generated report (query + real output table for all 15 queries)
- `docs/phase5_findings.md` — findings summary, each item labeled Fact or Observation

**Key facts established (see `docs/phase5_findings.md` for full detail):**
- Total revenue $55,755,479.59 / 26,326 orders / AOV $2,117.89 — reconciles exactly across country, category, and channel breakdowns (cross-checked).
- Revenue grew every full year 2016→2019, then fell 49.11% in 2020 across all 8 categories; 2021 is partial-year only.
- Computers is the leading category (34.62% of revenue); 25 of 2,517 products have zero recorded sales.
- Product profit margins cluster around ~3 fixed tiers (~49%, ~54%, ~66.9%), not a continuous spread — verified directly against the product catalog.
- In-store = 79.55% of revenue vs. online 20.45%, with similar AOV — the gap is order volume, not order size.
- US = 53.58% of revenue (customer-side); the "Online" channel alone outsells every country's physical stores except the US.

**Explicitly NOT done in this phase:** customer-level behavior analytics (Phase 6), RFM, cohort analysis, dashboards, business recommendations.

**Validation:**
- [x] Every query answers a stated business question (documented inline)
- [x] Uses JOIN, GROUP BY, CASE, CTEs, window functions, date functions, ranking functions as required
- [x] All 15 queries execute successfully against the Phase 4 database
- [x] Revenue totals reconcile exactly across every breakdown (country/category/channel all sum to $55,755,479.59)
- [x] Findings labeled Fact vs. Observation; no unsupported claims

**Commit:** `feat: add sales and product SQL analytics`

## Phase 6 — Detail

**Objective:** Understand customer purchasing behavior — repeat rate, purchase frequency, revenue concentration, top customers, segment contribution.

**Deliverables:**
- `sql/06_customer_analytics.sql` — 9 named queries (CTEs, `NTILE` for decile analysis, `RANK`, `CASE`-based bucketing, `julianday` date-math)
- `reports/phase6_customer_analytics_report.md` — generated report with real results for all 9 queries
- `docs/phase6_findings.md` — findings summary (Fact vs. Observation) + explicit answers to the phase's 3 required business questions

**Key facts established (see `docs/phase6_findings.md` for full detail):**
- 22.13% of registered customers (3,379 of 15,266) have never ordered; customer-behavior metrics are scoped to the 11,887 who have.
- **61.18%** of purchasing customers are repeat buyers (2+ orders), generating **82.39%** of revenue — driven by both higher order counts and ~3x higher average spend per customer, not just order volume.
- Revenue concentration is moderate: top 10% of customers = 35.98% of revenue, top 30% = 69.07%, bottom 50% = only 13.36%. No single customer or small outlier group dominates (top customer = 0.11% of revenue).
- New-customer acquisition peaked in 2018 (3,104) and fell sharply in 2020 (947), mirroring the Phase 5 revenue decline.
- 44.74% of purchasing customers have repeat orders spread over more than a year — a long-cycle, durable-goods purchase pattern, relevant context for RFM recency thresholds in Phase 8.
- Revenue by country sums reconcile exactly to the same $55,755,479.59 total established in Phase 5.

**Explicitly NOT done in this phase:** RFM scoring/segmentation (Phase 8), cohort/retention analysis (Phase 9), dashboards, recommendations.

**Validation:**
- [x] Every query answers a stated business question (documented inline)
- [x] All 3 phase-required questions explicitly answered with numbers
- [x] Revenue totals reconcile exactly with Phase 5 SQL analytics and the Phase 3/4 dataset ($55,755,479.59)
- [x] Findings labeled Fact vs. Observation; no unsupported claims

**Commit:** `feat: add customer behavior SQL analytics`

## Phase 7 — Detail

**Objective:** Use Python (Pandas, NumPy, Matplotlib, Seaborn, SciPy) to surface patterns not obvious from SQL aggregates — distribution shape, outliers, seasonality, and bivariate relationships.

**Deliverables:**
- `python/eda.py` — reproducible EDA script (reads `data/processed/`, writes figures + stats, changes nothing)
- `reports/figures/phase7/` — 10 generated PNG figures
- `reports/phase7_eda_stats.md` — raw computed statistics backing every figure
- `docs/phase7_findings.md` — findings summary (Fact vs. Observation), including what Python EDA added beyond the SQL phases

**Key facts established (see `docs/phase7_findings.md` for full detail):**
- Order revenue is strongly right-skewed (skewness 3.51); IQR outliers (7.37% of orders) are legitimate large purchases contributing 34.58% of revenue, not data errors.
- **New finding not seen in SQL phases:** revenue by day-of-week is highly uneven — Saturday is the peak ($13.20M) and Sunday dramatically the trough ($0.91M, ~14x gap) — verified via order counts and confirmed to hold separately for both online and in-store channels.
- April is consistently the lowest-revenue month across all 5 full years (avg $121,466.81) vs. December's peak (avg $1,499,321.77) — a real recurring seasonal pattern.
- Product-level quantity-vs-revenue correlation is moderate (0.515), confirming top-sellers-by-volume and top-sellers-by-revenue are related but distinct lists.
- New dimension added: purchasing customers average 52.3 years old (median 52.4), a fairly centered distribution.

**Explicitly NOT done in this phase:** RFM segmentation (Phase 8), cohort/retention analysis (Phase 9), dashboards, recommendations.

**Validation:**
- [x] Script runs end-to-end against `data/processed/` without modifying it
- [x] All 10 figures generated and visually reviewed for correctness/readability
- [x] Every statistic in the findings doc traces to `reports/phase7_eda_stats.md`
- [x] Notable/surprising findings (e.g. Sunday revenue dip) independently verified with a second method (order counts, channel breakdown) before being reported as fact
- [x] No manufactured conclusions; findings labeled Fact vs. Observation

**Commit:** `feat: add exploratory data analysis`
