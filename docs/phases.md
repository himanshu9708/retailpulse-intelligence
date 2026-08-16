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
| 8 | RFM Customer Segmentation | RFM scores + segments | ✅ Done (this commit) |
| 9 | Cohort & Retention Analysis | Cohort retention matrix | ✅ Done (this commit) |
| 10 | Business KPI Framework | KPI dictionary | ✅ Done (this commit) |
| 11 | Power BI Executive Dashboard | `.pbix` file | ✅ Done (as `.pbip` project — see below) |
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

## Phase 8 — Detail

**Objective:** Segment customers by purchasing behavior (Recency, Frequency, Monetary), with methodology documented and labels validated against the actual data.

**Deliverables:**
- `python/rfm_segmentation.py` — reproducible RFM scoring + segmentation script
- `data/processed/customer_rfm.csv` — one row per purchasing customer (R/F/M values, scores, segment)
- `reports/phase8_rfm_segment_summary.md` — segment-level aggregates (count, revenue, avg spend/frequency/recency)
- `docs/phase8_rfm_methodology.md` — full methodology + findings, including why 2 of the brief's suggested segment names were deliberately dropped

**Key methodology decisions:**
- Scope: 11,887 customers with ≥1 order (Phase 6). The 3,379 non-purchasers are excluded, not labeled "Lost" — RFM is undefined without a purchase history.
- Snapshot date: 2021-02-21 (day after last order in dataset).
- Quintile-based (data-driven) scoring, not fixed day/order thresholds — justified by Phase 6's finding that this is a long-cycle, durable-goods business (median 2 orders/customer, 44.74% of repeat customers spread over 1+ years).
- Frequency has too few unique values (1–14) for plain quintile cuts, so ties are broken by rank before cutting — documented, not silently patched.
- Segment grid intentionally drops "Hibernating" from the brief's suggested list — its intent is already covered by "About To Sleep"/"Lost", and keeping it would only fragment identical customer groups (the phase's own "don't force labels the data doesn't support" rule, applied).

**Key facts established (see `docs/phase8_rfm_methodology.md` for full detail):**
- **Champions + Loyal Customers** (35.76% of customers) generate **61.66%** of revenue — the sharpest concentration finding in the project.
- Verified the "disengaged" segments (At Risk, Can't Lose Them, Lost — 30.85% of customers) are **not** an artifact of the 2020 revenue decline: 100% of their last orders predate 2020, while Champions/Loyal Customers skew heavily toward 2020 — confirming the segmentation reflects genuine long-term drop-off, not a one-year anomaly.
- All totals reconcile exactly to Phase 6: 11,887 customers, $55,755,479.59 revenue.

**Explicitly NOT done in this phase:** cohort/retention analysis (Phase 9), dashboards, recommendations.

**Validation:**
- [x] RFM computed only for customers with purchase history (scope documented)
- [x] Scoring method (quintiles) justified against the actual data distribution, not assumed
- [x] Segment counts, revenue, avg spend, avg frequency all computed and reported per segment
- [x] Segment totals reconcile exactly with Phase 6 (11,887 customers, $55,755,479.59)
- [x] Notable claim (disengagement predates 2020) independently verified by year-of-last-order breakdown before being reported as fact

**Commit:** `feat: implement RFM customer segmentation`

## Phase 9 — Detail

**Objective:** Build monthly acquisition cohorts and a retention matrix, and answer whether customers are becoming more or less likely to return.

**Deliverables:**
- `python/cohort_analysis.py` — reproducible cohort/retention script
- `data/processed/cohort_retention_matrix.csv` / `cohort_retention_pct.csv` — full 62×62 cohort matrices (counts and %)
- `reports/figures/phase9/` — full-range heatmap (color-only), zoomed 0-12 month annotated heatmap, average retention curve
- `reports/phase9_cohort_analysis_stats.md` — full computed stats
- `docs/phase9_findings.md` — findings + explicit answer to the phase's required question

**Bug caught and fixed mid-phase:** the initial pivot conflated "zero customers returned that month" with "period hasn't happened yet" (both showed as blank), which silently excluded real 0% months and inflated every retention average and the trend correlation (0.491 "improving" → corrected to 0.183 "weak/no trend"). Verified the fix against a specific case (2017-03 cohort, confirmed 0 of 98 customers returned in month 1) before trusting any downstream numbers.

**Key facts established (see `docs/phase9_findings.md` for full detail):**
- Average Month-1 retention is 2.84% — low in absolute terms but consistent with Phase 6's finding that this is a long-cycle, durable-goods business, not a benchmarking failure.
- **Answer to "are customers becoming more/less likely to return?": no strong trend either way** (correlation between cohort start time and Month-1 retention = 0.183, weak).
- Retention rises gradually to a peak around Month 30 (4.46%) then appears to decline — but the tail (Month 48+) is based on as few as 1 eligible cohort and is flagged as unreliable, not reported as a trend.
- Best/worst cohorts differ depending on whether small cohorts are included (2018-04's "best" 8.70% is just 2 of 23 customers) — reported both the unrestricted and a ≥100-customer-restricted comparison for a fair read.

**Explicitly NOT done in this phase:** KPI framework consolidation (Phase 10), dashboards, recommendations.

**Validation:**
- [x] Cohort matrix correctly distinguishes "0% retention" from "period not yet occurred" (verified against a specific known case)
- [x] Average retention by period only computed over cohorts with full exposure to that period (documented, not silently averaged over incomplete cohorts)
- [x] Required question explicitly answered with a number and appropriate uncertainty, not overstated
- [x] Best/worst cohort claims checked for small-sample reliability before being reported
- [x] Figures redesigned for readability after an initial version proved unreadable (62×62 annotated heatmap)

**Commit:** `feat: add cohort retention analysis`

## Phase 10 — Detail

**Objective:** Define the single, official set of KPIs that Power BI and Tableau (Phases 11-12) will both draw from — no re-derivation, no divergent definitions.

**Deliverables:**
- `docs/kpi_framework.md` — 12 KPIs (Revenue, Orders, Customers, Units Sold, AOV, Revenue per Customer, New Customers, Repeat Customers, Repeat Purchase Rate, Historical CLV, Revenue Growth, Customer Retention), each with Definition / Formula / Source / Verified Current Value / Business Interpretation, plus global conventions (currency, geography, channel, customer scope, partial-year handling) and a per-dashboard-page KPI assignment table

**Verification approach:** every "current value" in the framework was **recomputed fresh** against the database while writing this phase, not copied from earlier phase reports — this caught and corrected a citation error (initial YoY growth figures for 2017-2019 were wrong; corrected to +6.83% / +72.32% / +42.81% after re-querying). All other cross-referenced figures (2018/2020 new customer counts, median order value, skewness) were independently re-verified and confirmed exact.

**Key design decision:** "Repeat Purchase Rate" (61.18%, Phase 6) and "Customer Retention (Cohort, Month-1)" (2.84%, Phase 9) are **both legitimate but measure different things** at different time grains. The framework explicitly documents this distinction and mandates both labels always appear together on any dashboard showing retention, to prevent the two correct-but-different numbers from looking like a contradiction.

**Explicitly NOT done in this phase:** actual dashboard building (Phase 11/12), business recommendations (Phase 13).

**Validation:**
- [x] Every KPI has Definition, Formula, SQL/Python source, and Business Interpretation
- [x] Same KPI definitions apply across Power BI and Tableau — no tool-specific formulas
- [x] All current values recomputed and verified against the database during this phase (not assumed from earlier phase text)
- [x] Global conventions (currency, geography, channel, scope, partial-year) documented once, referenced everywhere
- [x] Potentially confusing KPI pair (Repeat Purchase Rate vs. Cohort Retention) explicitly reconciled to prevent dashboard inconsistency

**Commit:** `docs: define business KPI framework`

## Phase 11 — Detail

**Objective:** Build a management-focused executive dashboard answering "how is the business performing?"

**Environment constraint:** Power BI Desktop is a Windows GUI application and isn't available in this sandboxed Linux environment (no network, no Windows) — the same category of constraint already documented for PostgreSQL (Phase 4).

**Correction made mid-phase:** the first attempt at this phase shipped an HTML/JS mockup labeled a "Power BI stand-in." That was flagged, correctly, as not an acceptable substitute — it produces no artifact Power BI can open, so it doesn't demonstrate a Power BI build at all. It has been removed. In its place: a real **Power BI Project (`.pbip`)** — Microsoft's official plain-text project format (TMDL semantic model + JSON report), which Power BI Desktop opens directly and can convert to a genuine `.pbix` via Save As. A literal `.pbix` cannot be hand-authored outside Power BI Desktop (it's an undocumented, proprietary compiled binary) — producing a file merely named `.pbix` without going through that application would be invalid and would fail to open, so that was rejected rather than faked.

**Deliverables:**
- `powerbi/EcommerceExecutiveDashboard.pbip` + `.SemanticModel/` (TMDL) + `.Report/` — a real, openable Power BI Project: 8 tables, all relationships, all 12 DAX measures (matching `docs/kpi_framework.md` exactly), Power Query M sources reading from `data/processed/*.csv`, and 4 named empty report pages
- `powerbi/README.md` — how to open the project and what to do first (set the `DataFolder` parameter)
- `docs/powerbi_design_spec.md` — full explanation of the `.pbix` constraint, the data model, all DAX measures, and the page-by-page visual layout to build in Power BI Desktop's UI

**What's real vs. a documented starting point:** the semantic model (tables, relationships, all 12 measures, Power Query sources, generated date dimension) is fully authored, real TMDL — the well-documented, stable part of the `.pbip` format. The report pages are wired to the model but deliberately left empty of visuals: hand-authoring the visual-container JSON schema blind, with no way to test-open the result in a real Power BI Desktop instance from this sandbox, risked producing a corrupt report that fails to open entirely — worse than an empty one. This is documented explicitly rather than glossed over.

**Verification approach:** TMDL syntax was checked against Microsoft's official documentation (tab-based indentation confirmed via automated scan — zero mixed indentation outside fenced M/DAX code blocks); every JSON file (`.pbip`, `.pbism`, `.pbir`, `.platform`, `report.json`) was validated for syntactic correctness. This project could not be test-opened in actual Power BI Desktop — that limitation is stated plainly in the design spec rather than implied to be fully verified.

**Explicitly NOT done in this phase:** Tableau (Phase 12), business recommendations (Phase 13).

**Validation:**
- [x] No fabricated `.pbix` — a real, officially-supported alternative format used instead, with the constraint explained rather than hidden
- [x] All 4 required pages present and correctly wired to the semantic model
- [x] All 12 KPI measures match `docs/kpi_framework.md` exactly, authored as real DAX (not just documented)
- [x] Data model matches `docs/database_schema.md` (star schema, same tables/relationships)
- [x] Every file that could be syntax-checked without Power BI Desktop was checked (JSON validity, TMDL indentation)
- [x] Residual verification risk (no real Power BI Desktop available to test-open) stated explicitly, not implied away

**Commit:** `fix: replace HTML mockup with real Power BI Project (.pbip)`
