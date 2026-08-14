# Development Phases & Status

Rule: each phase is completed and validated before the next one begins.
Nothing below "Not started" has been implemented.

| # | Phase | Deliverable | Status |
|---|---|---|---|
| 1 | Project Planning & Repository Setup | Repo structure, docs, config files | ✅ Done |
| 2 | Dataset Ingestion & Data Understanding | Data profiling report + data dictionary | ✅ Done (this commit) |
| 3 | Data Cleaning & Validation | `data/processed/` clean dataset + decisions log | ⬜ Not started |
| 4 | SQL Database & Data Modeling | Schema + loaded relational DB | ⬜ Not started |
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
