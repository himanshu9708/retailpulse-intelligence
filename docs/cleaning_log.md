# Data Cleaning Log

Every cleaning decision made in `python/clean_data.py`, documented as
**Problem → Decision → Reason**. Raw data in `data/raw/` is never modified;
all output goes to `data/processed/`.

---

### 1. Products price/cost fields stored as formatted text

**Problem:** `Unit Cost USD` and `Unit Price USD` in `Products.csv` are
stored as text with a `$` prefix and trailing space (e.g. `"$6.62 "`), not
numeric.

**Decision:** Strip `$`, `,`, and whitespace, then parse to float
(`parse_money()` helper).

**Reason:** Required for any arithmetic (revenue, cost, profit). Phase 2
profiling confirmed 0 values fail this parse — it's a formatting issue only,
not corrupted data, so no rows are dropped.

---

### 2. No direct revenue column in Sales.csv

**Problem:** `Sales.csv` has `Quantity` and `Currency Code` but no
price/revenue field. `Products.csv` has `Unit Price USD` (already
USD-denominated, per its own column name) and `Exchange_Rates.csv` gives a
USD → local-currency multiplier (confirmed: `Exchange == 1.0` for every USD
row).

**Decision:** Compute `Revenue USD = Quantity × Products.Unit Price USD`
directly — **no FX conversion applied** to the core revenue figure.
`Currency Code` is retained on each row as metadata (what currency the
customer transacted in) but is not used to convert Unit Price USD.

**Reason:** `Unit Price USD` is explicitly already in USD. Exchange rates in
this dataset convert *from* USD *to* local currency (verified: non-USD rates
are all > 1, e.g. CAD ≈ 1.16, consistent with "1 USD buys 1.16 CAD", and USD
rate is exactly 1.0 for all dates). Applying the rate to Unit Price USD would
incorrectly deflate/inflate revenue. `Exchange_Rates.csv` is preserved in
`data/processed/exchange_rates_clean.csv` for any future local-currency
reporting need, but is not part of the core USD revenue calculation.
`Cost USD` and `Profit USD` are computed the same way, using `Unit Cost USD`.

---

### 3. Delivery Date is 79.06% missing

**Problem:** 49,719 of 62,884 Sales rows have a blank `Delivery Date`.

**Decision:** Keep these as null (do not impute, do not drop the rows). Add
an explicit `Is_Delivered` boolean column so downstream analysis can filter
delivery-time metrics without losing the underlying order/revenue record.

**Reason:** Phase 2 confirmed 0 cases of Delivery Date preceding Order Date,
and missingness is consistent with orders that simply haven't been
delivered yet or aren't tracked for delivery — dropping these rows would
incorrectly remove ~79% of all revenue from the dataset. Revenue is
recognized at order time (`Order Date`), not delivery time, for this
project's KPIs.

---

### 4. Customers `State Code` missing for 10 rows (0.07%)

**Problem:** 10 of 15,266 customers have a null `State Code`.

**Decision:** Keep as null; no row dropped, no value imputed.

**Reason:** 0.07% of rows — immaterial to aggregate analysis. `State` (full
name) and `Country` remain available for geographic grouping on these rows.
Imputing a fabricated state code would violate the "never fabricate data"
project rule.

---

### 5. Stores `Square Meters` missing for 1 row (the Online "store")

**Problem:** `StoreKey = 0` (Country = "Online") has a null `Square Meters`
value, since it isn't a physical location.

**Decision:** Leave as null. Add an explicit `Is_Online` boolean column
(`Country == "Online"`) to `stores_clean.csv` rather than relying on the
implicit convention that `StoreKey == 0` means online.

**Reason:** A missing footprint for a non-physical "store" is not a data
error — imputing a value (e.g. 0 or an average) would misrepresent it as a
physical store with a defined size. The explicit flag makes channel
filtering (online vs. in-store) reliable for all downstream SQL/Python/BI
work instead of depending on analysts remembering `StoreKey == 0`.

---

### 6. Duplicate customer `Name` values (148 rows)

**Problem:** 148 customer names are duplicated across different
`CustomerKey` values.

**Decision:** No action — `Name` was never used as an identifier.
`CustomerKey` remains the sole customer identity key throughout the project.

**Reason:** Confirmed these are distinct customers (different
`CustomerKey`s) who happen to share a name (e.g. common names), not
duplicate records of the same person. Deduplicating by name would
incorrectly merge unrelated customers.

---

### 7. Outlier review (Quantity, Price, Cost)

**Problem:** Per project rules, outliers must not be blindly deleted, but
should be reviewed.

**Decision:** No rows removed as outliers.

**Reason:** Phase 2 profiling showed `Quantity` is bounded and sane (1–10,
mean 3.14, no zero/negative values), and no product has `Unit Price USD <
Unit Cost USD` (i.e., no built-in loss-making list prices). Nothing in the
raw ranges indicated corrupted or implausible values requiring removal or
capping.

---

### 8. Duplicate transaction rows

**Problem:** Per project rules, duplicate transaction records must be
checked.

**Decision:** No rows removed.

**Reason:** Phase 2 and Phase 3 validation both confirm 0 duplicate
`(Order Number, Line Item)` combinations and 0 full-row duplicates across
all 6 raw tables.

---

## Summary of Output Files (`data/processed/`)

| File | Rows | Notes |
|---|---|---|
| `sales_clean.csv` | 62,884 | Adds `Is_Delivered`, `Unit Price USD`, `Unit Cost USD`, `Revenue USD`, `Cost USD`, `Profit USD` |
| `customers_clean.csv` | 15,266 | `Birthday` parsed to date; `Zip Code` kept as text |
| `products_clean.csv` | 2,517 | `Unit Cost USD` / `Unit Price USD` parsed to float |
| `stores_clean.csv` | 67 | `Open Date` parsed to date; adds `Is_Online` flag |
| `exchange_rates_clean.csv` | 11,215 | `Date` parsed to date; preserved for optional local-currency reporting |

No rows were dropped from any table during cleaning. Row counts match the
raw files exactly (see `reports/phase2_data_profiling_report.md`).

Full automated validation results: `reports/phase3_cleaning_validation_report.md`
(generated by `python/validate_phase3.py`).
