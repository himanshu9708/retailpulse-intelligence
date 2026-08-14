# Development Phases & Status

Rule: each phase is completed and validated before the next one begins.
Nothing below "Not started" has been implemented.

| # | Phase | Deliverable | Status |
|---|---|---|---|
| 1 | Project Planning & Repository Setup | Repo structure, docs, config files | ✅ Done |
| 2 | Dataset Ingestion & Data Understanding | Data profiling report + data dictionary | ✅ Done (this commit) |
| 3 | Data Cleaning & Validation | `data/processed/` clean dataset + decisions log | ✅ Done (this commit) |
| 4 | SQL Database & Data Modeling | Schema + loaded relational DB | ✅ Done (this commit) |
| 5 | SQL Sales Analytics | Revenue/product/geo SQL queries | ⬜ Not started |
| 6 | SQL Customer Analytics | Customer behavior SQL queries | ⬜ Not started |
| 7 | Python Exploratory Data Analysis | EDA notebook/report | ⬜ Not started |
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
