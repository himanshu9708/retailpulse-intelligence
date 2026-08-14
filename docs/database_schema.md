# Database Schema

## Engine Decision

**Problem:** The project brief prefers PostgreSQL if practical.

**Decision:** Use **SQLite** for this project's database.

**Reason:** This development environment has no network access and no
PostgreSQL server available to install or connect to. SQLite requires no
server process, ships with Python's standard library, and is fully
sufficient to demonstrate schema design, keys, relationships, and SQL
analytics. The schema (`sql/schema.sql`) is written in Postgres-compatible
SQL and documented so it could be migrated to a real PostgreSQL instance
with minimal changes (mainly: `SERIAL`/native `BOOLEAN` types instead of
SQLite's simplified equivalents). This is a pragmatic substitution, not a
design shortcut — every constraint (PK, FK, CHECK) that Postgres would
enforce is also enforced here via `PRAGMA foreign_keys = ON` and validated
in `reports/phase4_database_validation_report.md`.

Database file: `data/processed/ecommerce_analytics.db` (excluded from git
via `.gitignore`; rebuilt anytime from `data/processed/*.csv` by running
`python python/build_database.py`).

## Design: Star Schema

One fact table (`fact_sales`, grain = one order line item) surrounded by
dimension tables, matching the conceptual model from the project plan:

```text
dim_customer ──┐
               │
dim_store ─────┼──> fact_sales <── dim_product ──> dim_subcategory ──> dim_category
               │        │
dim_date <─────┘        └── currency_code (optionally joinable to
                             exchange_rate for local-currency reporting)
```

## Tables

| Table | Grain / Purpose | Primary Key | Rows |
|---|---|---|---|
| `dim_customer` | One row per customer | `customer_key` | 15,266 |
| `dim_store` | One row per store (incl. StoreKey 0 = "Online") | `store_key` | 67 |
| `dim_product` | One row per product | `product_key` | 2,517 |
| `dim_subcategory` | One row per product subcategory | `subcategory_key` | 32 |
| `dim_category` | One row per product category | `category_key` | 8 |
| `dim_date` | One row per calendar day, spanning the full Sales date range | `date_key` | 1,878 |
| `exchange_rate` | One row per (date, currency) | (`rate_date`, `currency`) composite | 11,215 |
| `fact_sales` | One row per order line item | (`order_number`, `line_item`) composite | 62,884 |

## Foreign Keys

| From | To |
|---|---|
| `fact_sales.customer_key` | `dim_customer.customer_key` |
| `fact_sales.store_key` | `dim_store.store_key` |
| `fact_sales.product_key` | `dim_product.product_key` |
| `fact_sales.order_date` | `dim_date.date_key` |
| `dim_product.subcategory_key` | `dim_subcategory.subcategory_key` |
| `dim_subcategory.category_key` | `dim_category.category_key` |

`exchange_rate` is not foreign-keyed to `fact_sales` — it's a reference
table joinable on `(order_date, currency_code)` for anyone who wants
local-currency figures. It is **not** used in the core `revenue_usd`
calculation (see `docs/cleaning_log.md`, decision #2).

## Why a Star Schema (not a single flat table)

* Matches the phase's required conceptual model: Customers → Orders → Order
  Items → Products → Categories.
* Normalizing `Category`/`Subcategory` out of `Products` avoids repeating
  the category name on every one of 2,517 products and makes category-level
  SQL joins/aggregations explicit and indexed.
* `dim_date` supports date-based rollups (month, quarter, weekday) directly
  in SQL without repeated date-parsing logic in every query — used
  extensively in Phase 5/6 SQL analytics.
* `fact_sales` retains the derived `revenue_usd` / `cost_usd` / `profit_usd`
  columns computed in Phase 3, so every downstream query (SQL, Python, BI
  tool) uses the exact same numbers — critical for the project's KPI
  consistency requirement (Phase 10/14).

## Indexes

Added on all foreign key columns used in typical filter/join patterns
(`fact_sales.customer_key/product_key/store_key/order_date`,
`dim_product.subcategory_key`, `dim_subcategory.category_key`) to keep
aggregation queries in Phase 5/6 performant.

## Rebuilding the Database

```bash
python python/build_database.py     # builds/rebuilds data/processed/ecommerce_analytics.db
python python/validate_phase4.py    # runs all 21 integrity/consistency checks
```

Both scripts are idempotent — re-running `build_database.py` drops and
recreates the database file from the Phase 3 processed CSVs.
