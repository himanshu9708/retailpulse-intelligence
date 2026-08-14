# Data Dictionary

Source: `Data_Dictionary.csv` (provided with the dataset) plus verified
business-meaning notes added during Phase 2 profiling. "Description" is the
source's own wording; "Business Meaning / Analytics Use" is added by this
project and confirmed against the actual data (see
`reports/phase2_data_profiling_report.md`), not assumed.

## Sales

| Column | Description | Data Type (as loaded) | Business Meaning / Analytics Use |
|---|---|---|---|
| Order Number | Unique ID for each order | int64 | Groups line items into a single order. Not unique per row — one order can have multiple line items. 26,326 unique orders across 62,884 rows. |
| Line Item | Identifies individual products purchased as part of an order | int64 | Combined with Order Number forms the true unique row key (verified: 62,884 unique combinations = row count). |
| Order Date | Date the order was placed | str → date | Basis for time-series, RFM recency, and cohort assignment. Range: 2016-01-01 to 2021-02-20. 0 missing/unparseable. |
| Delivery Date | Date the order was delivered | str → date | 79.06% missing (49,719 of 62,884 rows) — likely undelivered/in-transit orders or orders not tracked for delivery, not a data error. Should not be used as a denominator for order counts. No cases of delivery-before-order-date. |
| CustomerKey | Unique key identifying which customer placed the order | int64 | Foreign key → Customers.CustomerKey. 0 orphan keys — full referential integrity confirmed. 11,887 unique customers appear in Sales (of 15,266 total customers — i.e. some customers have never ordered). |
| StoreKey | Unique key identifying which store processed the order | int64 | Foreign key → Stores.StoreKey. 0 orphan keys. **StoreKey = 0 maps to Country = "Online" in Stores.csv** — this is the channel dimension (online vs. physical store). 20.94% of sales rows are online (StoreKey 0). |
| ProductKey | Unique key identifying which product was purchased | int64 | Foreign key → Products.ProductKey. 0 orphan keys. |
| Quantity | Number of items purchased | int64 | Range 1–10, mean 3.14. No zero/negative values. |
| Currency Code | Currency used to process the order | str | 5 values: AUD, CAD, EUR, GBP, USD. All present in Exchange_Rates.csv — safe to join for USD conversion. Sales.csv has **no price/revenue column** — revenue must be derived via Products.Unit Price USD × Quantity, converted using this code + Order Date against Exchange_Rates. |

## Customers

| Column | Description | Data Type | Business Meaning / Analytics Use |
|---|---|---|---|
| CustomerKey | Primary key to identify customers | int64 | Confirmed unique (15,266 rows = 15,266 unique keys). Primary key for RFM/cohort analysis. |
| Gender | Customer gender | str | Male: 7,748 / Female: 7,518. No other categories, no missing values. |
| Name | Customer full name | str | 148 duplicate names exist — **not** necessarily the same person (different CustomerKeys); do not use Name as an identity key. |
| City | Customer city | str | Geographic dimension (fine-grain). |
| State Code | Customer state (abbreviated) | str | 10 missing values (0.07%) — to be investigated/documented in Phase 3. |
| State | Customer state (full) | str | Geographic dimension (regional analysis). |
| Zip Code | Customer zip code | str | Loaded as text; some values may contain leading zeros — do not cast to int during cleaning. |
| Country | Customer country | str | 8 unique countries. Candidate geography dimension for "revenue by region" (alternative to Stores.Country). |
| Continent | Customer continent | str | 3 values: Australia, Europe, North America. Useful for high-level regional rollups. |
| Birthday | Customer date of birth | str → date | All 15,266 values parse validly (range: 1935-02-03 to 2002-02-18). Usable for age/generation segmentation if needed later — not part of the core RFM/cohort scope. |

## Products

| Column | Description | Data Type | Business Meaning / Analytics Use |
|---|---|---|---|
| ProductKey | Primary key to identify products | int64 | Confirmed unique (2,517 rows = 2,517 keys). |
| Product Name | Product name | str | No duplicates. |
| Brand | Product brand | str | 11 unique brands. |
| Color | Product color | str | Product attribute; not core to revenue/segmentation analysis but available for product-level EDA. |
| Unit Cost USD | Cost to produce the product in USD | str (formatted, e.g. `$6.62 `) | **Must be parsed** — stored as text with `$` and trailing space. Parsed range: $0.48–$1,060.22, 0 unparseable. Used for profitability (Price − Cost). |
| Unit Price USD | Product list price in USD | str (formatted) | Same formatting issue as Unit Cost. Parsed range: $0.95–$3,199.99, 0 unparseable. This is the price basis for revenue calculation (`Quantity × Unit Price USD`, currency-adjusted). Verified: 0 rows where Price < Cost, so no obvious loss-making list prices. |
| SubcategoryKey | Key to identify product subcategories | str/int | Foreign key within Products; used for category rollups. |
| Subcategory | Product subcategory name | str | 32 unique subcategories. |
| CategoryKey | Key to identify product categories | str | Consistent 1:1 mapping to Category label (verified — no key maps to >1 label). |
| Category | Product category name | str | 8 unique categories: Audio, Cameras and camcorders, Cell phones, Computers, Games and Toys, Home Appliances, Music/Movies/Audio Books, TV and Video. Primary product-grouping dimension. |

## Stores

| Column | Description | Data Type | Business Meaning / Analytics Use |
|---|---|---|---|
| StoreKey | Primary key to identify stores | int64 | Confirmed unique (67 rows = 67 keys). Includes StoreKey 0 = "Online" (not a physical store). |
| Country | Store country | str | 9 unique values including **"Online"** as a pseudo-country — this is the store-side geography/channel field. |
| State | Store state | str | For StoreKey 0 (Online), State is also "Online" — a placeholder, not a real state. |
| Square Meters | Store footprint in square meters | float64 | 1 missing value — confirmed to be the Online "store" (StoreKey 0), which has no physical footprint. Not a data-quality error. Range (physical stores): 245–2,105 sqm. |
| Open Date | Store open date | str → date | Store launch date; useful for store-age or store-performance-over-time analysis if pursued later. |

## Exchange_Rates

| Column | Description | Data Type | Business Meaning / Analytics Use |
|---|---|---|---|
| Date | Date | str → date | Daily granularity. Range 2015-01-01 to 2021-02-20 — **fully covers** the Sales.csv order-date range (2016-01-01 to 2021-02-20), confirmed by direct check. Safe to join for currency conversion. |
| Currency | Currency code | str | 5 values (AUD, CAD, EUR, GBP, USD) — matches all currency codes present in Sales.csv exactly; no missing FX coverage. |
| Exchange | Exchange rate compared to USD | float64 | Multiplier to convert local currency → USD (USD rows = 1.0). Will be used in revenue derivation logic in Phase 3/4. |

---

## Summary of Verified Data-Quality Findings (Phase 2)

These are **facts** confirmed by the profiling script (`python/profile_data.py`,
output in `reports/phase2_data_profiling_report.md`) — not assumptions:

1. **No direct revenue column.** Revenue must be derived: `Quantity × Products.Unit Price USD`, currency-adjusted via `Exchange_Rates` where `Currency Code != USD`. To be implemented and validated in Phase 3/4.
2. **Delivery Date is 79.06% missing** (49,719 of 62,884 rows). This appears structural (not all orders tracked/delivered as of the data snapshot), not corrupted data — confirmed there are zero cases of delivery date preceding order date. Decision on how to treat this is deferred to Phase 3.
3. **`StoreKey = 0` represents the "Online" channel**, not a physical store (confirmed via `Stores.csv`: Country = "Online", State = "Online", Square Meters = missing). This gives the project a genuine **online vs. in-store** channel dimension. 20.94% of all sales rows are online.
4. **Referential integrity is fully intact**: 0 orphaned CustomerKey, ProductKey, or StoreKey values in Sales.csv; all Sales currency codes exist in Exchange_Rates.csv; Exchange_Rates date range fully covers the Sales date range.
5. **Numeric fields in Products.csv (`Unit Cost USD`, `Unit Price USD`) are stored as formatted text** (e.g. `"$6.62 "`) and must be parsed to numeric during cleaning (Phase 3) — 0 values failed a strip-and-parse test, so this is a formatting issue, not a data-corruption issue.
6. **`Customers.State Code` has 10 missing values** (0.07%) — minor, to be resolved in Phase 3.
7. **148 duplicate customer `Name` values** exist but map to distinct `CustomerKey`s — Name must never be used as an identity/join key.
8. **No duplicate rows** in any of the 6 raw files (exact full-row duplicates = 0 everywhere).
9. **No invalid Quantity values** (all 1–10, no zero/negative).
10. **No products priced below cost** (Unit Price ≥ Unit Cost for all 2,517 products) — worth re-confirming after numeric parsing is finalized in Phase 3, but no red flags at profiling stage.

## Open Items Carried Into Phase 3

* Decide how to treat missing `Delivery Date` (leave null / flag as "not yet delivered" / exclude from delivery-time analysis — but **do not** exclude these orders from revenue).
* Decide which geography field is authoritative for "regional performance": `Customers.Country/State` (customer location) vs `Stores.Country/State` (point of sale). Both are valid analytical lenses and will likely both be kept, but the KPI framework (Phase 10) must be explicit about which one each dashboard uses.
* Resolve the 10 missing `State Code` values in Customers.csv.
* Formally implement and unit-test the currency-conversion join logic.
