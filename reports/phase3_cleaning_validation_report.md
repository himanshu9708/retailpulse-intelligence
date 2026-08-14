# Phase 3 — Cleaning Validation Report

Generated: 2026-08-14 11:35

Validated against `data/processed/` (output of `python/clean_data.py`).

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | No duplicate (Order Number, Line Item) records | ✅ PASS | 0 duplicate transaction keys found |
| 2 | Order Date fully valid (no unparseable) | ✅ PASS | 0 unparseable Order Date values |
| 3 | No Delivery Date before Order Date | ✅ PASS | 0 rows with delivery before order |
| 4 | Quantity valid (>0, non-null) | ✅ PASS | 0 invalid Quantity values |
| 5 | Unit Price USD valid (parsed, non-negative) | ✅ PASS | 0 invalid Unit Price USD values |
| 6 | Unit Cost USD valid (parsed, non-negative) | ✅ PASS | 0 invalid Unit Cost USD values |
| 7 | Category <-> CategoryKey is 1:1 consistent | ✅ PASS | 0 CategoryKey values map to multiple Category labels |
| 8 | CustomerKey is unique per customer | ✅ PASS | 0 duplicate CustomerKey values |
| 9 | All Sales CustomerKey values exist in Customers | ✅ PASS | 0 orphan CustomerKey rows in Sales |
| 10 | Every Order Number has at least one Line Item | ✅ PASS | OK |
| 11 | Revenue USD == Quantity x Unit Price USD for every row | ✅ PASS | 0 rows where stored Revenue USD does not match recomputation |
| 12 | Total revenue is a finite positive number | ✅ PASS | Total Revenue USD = $55,755,479.59 |
| 13 | Profit USD has no negative values (Price >= Cost for all products) | ✅ PASS | 0 rows with negative profit |

**Overall result: ✅ ALL CHECKS PASSED**

- Total Revenue (USD), full dataset: **$55,755,479.59**
- Total rows in cleaned Sales: **62,884**
- Total unique orders: **26,326**
- Total unique customers with orders: **11,887**