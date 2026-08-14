# Phase 4 — Database Validation Report

Generated: 2026-08-14 16:11

Database: `data/processed/ecommerce_analytics.db` (SQLite)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | dim_customer row count matches source CSV | ✅ PASS | table=15,266, csv=15,266 |
| 2 | dim_product row count matches source CSV | ✅ PASS | table=2,517, csv=2,517 |
| 3 | dim_store row count matches source CSV | ✅ PASS | table=67, csv=67 |
| 4 | exchange_rate row count matches source CSV | ✅ PASS | table=11,215, csv=11,215 |
| 5 | fact_sales row count matches source CSV | ✅ PASS | table=62,884, csv=62,884 |
| 6 | dim_customer.customer_key is a valid primary key (unique, no nulls) | ✅ PASS | 15,266 rows, 15,266 distinct customer_key values |
| 7 | dim_product.product_key is a valid primary key (unique, no nulls) | ✅ PASS | 2,517 rows, 2,517 distinct product_key values |
| 8 | dim_store.store_key is a valid primary key (unique, no nulls) | ✅ PASS | 67 rows, 67 distinct store_key values |
| 9 | dim_category.category_key is a valid primary key (unique, no nulls) | ✅ PASS | 8 rows, 8 distinct category_key values |
| 10 | dim_subcategory.subcategory_key is a valid primary key (unique, no nulls) | ✅ PASS | 32 rows, 32 distinct subcategory_key values |
| 11 | dim_date.date_key is a valid primary key (unique, no nulls) | ✅ PASS | 1,878 rows, 1,878 distinct date_key values |
| 12 | fact_sales (order_number, line_item) is a valid composite primary key | ✅ PASS | 62,884 rows, 62,884 distinct composite keys |
| 13 | No foreign key violations (PRAGMA foreign_key_check) | ✅ PASS | 0 violations |
| 14 | fact_sales.customer_key -> dim_customer fully resolved | ✅ PASS | 0 orphan rows |
| 15 | fact_sales.product_key -> dim_product fully resolved | ✅ PASS | 0 orphan rows |
| 16 | fact_sales.store_key -> dim_store fully resolved | ✅ PASS | 0 orphan rows |
| 17 | fact_sales.order_date -> dim_date fully resolved | ✅ PASS | 0 orphan rows |
| 18 | dim_product.subcategory_key -> dim_subcategory fully resolved | ✅ PASS | 0 orphan rows |
| 19 | dim_subcategory.category_key -> dim_category fully resolved | ✅ PASS | 0 orphan rows |
| 20 | No duplicate customer_key groups in dim_customer | ✅ PASS | 0 duplicate groups |
| 21 | Total revenue (DB) matches total revenue (CSV) | ✅ PASS | DB=$55,755,479.59, CSV=$55,755,479.59 |

**Overall result: ✅ ALL CHECKS PASSED**

- Total Revenue (fact_sales): **$55,755,479.59**