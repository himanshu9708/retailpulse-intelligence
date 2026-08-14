# Dataset Requirements

## Minimum Requirements for This Project

To answer the business questions in `project_plan.md`, the dataset must
provide, at minimum:

* Transaction-level records (order date, customer, product, quantity)
* A way to derive revenue (price per product, currency)
* Customer identifiers usable across orders (for repeat-purchase / RFM / cohort analysis)
* Product identifiers with category/subcategory grouping
* Some geographic dimension (store or customer location)

## Provided Files (as uploaded, unmodified, stored in `data/raw/`)

| File | Rows | Columns |
|---|---|---|
| `Sales.csv` | 62,884 | `Order Number`, `Line Item`, `Order Date`, `Delivery Date`, `CustomerKey`, `StoreKey`, `ProductKey`, `Quantity`, `Currency Code` |
| `Customers.csv` | 15,266 | `CustomerKey`, `Gender`, `Name`, `City`, `State Code`, `State`, `Zip Code`, `Country`, `Continent`, `Birthday` |
| `Products.csv` | 2,517 | `ProductKey`, `Product Name`, `Brand`, `Color`, `Unit Cost USD`, `Unit Price USD`, `SubcategoryKey`, `Subcategory`, `CategoryKey`, `Category` |
| `Stores.csv` | 67 | `StoreKey`, `Country`, `State`, `Square Meters`, `Open Date` |
| `Exchange_Rates.csv` | 11,215 | `Date`, `Currency`, `Exchange` |
| `Data_Dictionary.csv` | 37 | `Table`, `Field`, `Description` (source-provided) |

Row counts above are raw line counts (excluding header) from the files as
uploaded on 2026-08-14 — confirmed by direct inspection, not estimated.

## Requirement Coverage Check

| Requirement | Covered by | Notes |
|---|---|---|
| Transaction-level records | `Sales.csv` | One row per order line item |
| Revenue derivation | `Sales.csv` (Quantity, Currency) + `Products.csv` (Unit Price USD) + `Exchange_Rates.csv` | Revenue is **not** a direct column — must be calculated: `Quantity × Unit Price USD`, then currency-adjusted if `Currency Code != USD`. This will be implemented and validated in Phase 3/4. |
| Customer identifier | `Sales.CustomerKey` → `Customers.CustomerKey` | ✔ |
| Product / category grouping | `Sales.ProductKey` → `Products.CategoryKey`/`SubcategoryKey` | ✔ |
| Geography | `Customers.Country/State/City` and `Stores.Country/State` | Two possible geography dimensions (customer location vs. store location) — which one is authoritative for "regional performance" will be decided and documented in Phase 4. |
| Profitability | `Products.Unit Cost USD` vs `Unit Price USD` | Profit is derivable (Price − Cost) × Quantity; not a raw column. |
| Order recency/frequency (for RFM) | `Sales.Order Date`, `Sales.CustomerKey` | ✔ |
| Cohort basis (first purchase month) | `Sales.Order Date` per `CustomerKey` | ✔ |

**Conclusion: the provided dataset satisfies the minimum requirements for
this project.** No additional data sources are required to proceed.

## Known Open Questions (to resolve in Phase 2 profiling — not answered here)

* Do `Sales.Order Date` / `Delivery Date` contain missing or invalid values (e.g. undelivered orders)?
* Are there `CustomerKey` or `ProductKey` values in `Sales.csv` with no matching master record?
* What is the exact date range covered by `Sales.csv` vs. `Exchange_Rates.csv` (must fully overlap for currency conversion)?
* Are there duplicate `(Order Number, Line Item)` combinations?
* Data types on disk are all plain text/CSV — numeric fields like `Unit Cost USD` / `Unit Price USD` are stored with `$` and formatting that will need parsing.

These will be answered with evidence in **Phase 2 — Dataset Ingestion & Data
Understanding**, not assumed here.

## Source-Provided Data Dictionary

The uploaded `Data_Dictionary.csv` (37 entries across `Sales`, `Customers`,
`Products`, `Stores`, `Exchange_Rates` tables) will be reproduced verbatim
and cross-checked against actual column contents as part of Phase 2's data
dictionary deliverable.
