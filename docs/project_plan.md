# Project Plan

## 1. Objective

Build an end-to-end analytics system that turns raw e-commerce transaction
data into business decisions, covering:

**Sales → Customers → Products → Retention → Business Opportunities**

The finished project must be able to answer, using evidence from the actual
dataset (never fabricated):

1. How is the business performing?
2. What products and categories drive revenue?
3. Which customers generate the most value?
4. Who are the most loyal and least engaged customers?
5. How well are customers being retained?
6. Which customer segments require attention?
7. Which regions/channels/categories are performing poorly?
8. What business actions should management take?

## 2. Technology Stack

| Layer | Tool | Role |
|---|---|---|
| Data prep / EDA | Python (Pandas, NumPy, Matplotlib, Seaborn) | Cleaning, profiling, exploratory analysis, RFM, cohort analysis, statistics |
| Data modeling / analysis | SQL (PostgreSQL preferred, SQLite acceptable fallback) | Relational schema, business-question SQL analytics |
| Executive reporting | Power BI | Management-facing KPI dashboard |
| Exploratory / storytelling | Tableau | Customer & product analytics, retention story |
| Version control | Git / GitHub | Phase-by-phase history, reproducibility |

## 3. Architecture

```text
                    RAW E-COMMERCE DATA (data/raw/)
                            │
                            ▼
                     PYTHON / PANDAS
                    Data Cleaning (Phase 3)
                    Data Validation
                            │
                            ▼
                  SQL DATABASE (Phase 4)
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         Sales SQL     Customer SQL   Product SQL   (Phase 5–6)
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                  PYTHON ANALYTICS (Phase 7)
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
          RFM Analysis (P8)     Cohort Analysis (P9)
                  │                   │
                  └─────────┬─────────┘
                            ▼
                  KPI FRAMEWORK (Phase 10)
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          POWER BI (P11)         TABLEAU (P12)
         Executive BI          Exploratory BI
                 │                     │
                 └──────────┬──────────┘
                            ▼
               BUSINESS INSIGHTS (Phase 13)
                            │
                            ▼
                RECOMMENDATIONS (Phase 13)
```

## 4. Dataset Requirements

See [`dataset_requirements.md`](dataset_requirements.md) for the column-level
data dictionary and minimum data requirements confirmed against the actual
provided dataset.

## 5. Development Phases

See [`phases.md`](phases.md) for phase-by-phase objectives, deliverables,
validation criteria, and status tracking.
