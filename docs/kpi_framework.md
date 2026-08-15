# Business KPI Framework

This is the **single source of truth** for every KPI used anywhere in this
project — Power BI (Phase 11), Tableau (Phase 12), and this documentation.
Per the project's own rule, no KPI is defined differently across tools:
every dashboard must reference the definitions below exactly.

Every "Verified Current Value" in this document was recomputed directly
against `data/processed/ecommerce_analytics.db` while writing this phase —
not copied forward from memory — and reconciles exactly with the figures
already established in Phases 5, 6, 8, and 9.

## Global Conventions (apply to every KPI below)

| Convention | Decision | Why |
|---|---|---|
| Currency | All revenue/cost/profit figures are in **USD**, computed as `Quantity × Unit Price USD` with **no FX conversion** | `Unit Price USD` is already USD-denominated; `Exchange_Rates.csv` converts USD → local currency, not the reverse (verified Phase 3) |
| Geography | **Customer location** (`dim_customer.country/state`) is the default geography for revenue/regional KPIs, unless a KPI is explicitly labeled "by store" or "by channel" | Two valid geography dimensions exist (customer vs. store); customer location is used by default because it answers "where is our revenue coming from," the more common executive question — see `docs/database_schema.md` |
| Channel | "Online" = `dim_store.is_online = 1` (StoreKey 0); "In-Store" = all other stores | Established in Phase 3/4 |
| Customer scope | Unless stated otherwise, customer-based KPIs (repeat rate, CLV, RFM, cohorts) are scoped to the **11,887 customers with ≥1 order**, not all 15,266 in `dim_customer` | RFM/frequency/monetary are undefined for customers with no purchase history (Phase 6/8) |
| Time period completeness | **2021 is a partial year** (Jan–Feb only, dataset ends 2021-02-20) | Any YoY/growth KPI must flag 2021 as partial, not compare it to full years without normalization (Phase 5) |

---

## KPI Dictionary

### Revenue

* **Definition:** Total sales value generated, in USD.
* **Formula:** `SUM(Quantity × Unit Price USD)` across all order line items.
* **Source:** `fact_sales.revenue_usd` (computed in Phase 3, loaded in Phase 4); SQL: `sql/05_sales_analytics.sql` (`kpi_summary`).
* **Verified current value:** **$55,755,479.59**
* **Business interpretation:** The headline top-line performance number. Should always reconcile exactly regardless of how it's sliced (by country, category, channel, segment) — verified in Phases 5, 6, and 8.

### Orders

* **Definition:** Count of distinct customer transactions (an order may contain multiple line items).
* **Formula:** `COUNT(DISTINCT Order Number)`.
* **Source:** `fact_sales.order_number`; SQL: `kpi_summary`.
* **Verified current value:** **26,326**
* **Business interpretation:** Transaction volume — distinct from revenue, since order size varies (avg 2.39 line items/order, Phase 7).

### Customers (Active / Purchasing)

* **Definition:** Count of distinct customers who have placed at least one order.
* **Formula:** `COUNT(DISTINCT CustomerKey)` in `fact_sales`.
* **Source:** `fact_sales.customer_key`; SQL: `kpi_summary`.
* **Verified current value:** **11,887** (of 15,266 total registered customers — 22.13% have never ordered, Phase 6).
* **Business interpretation:** The addressable base actually generating revenue. Always distinguish from total registered customers.

### Units Sold

* **Definition:** Total quantity of individual product units sold.
* **Formula:** `SUM(Quantity)`.
* **Source:** `fact_sales.quantity`; SQL: `kpi_summary`.
* **Verified current value:** **197,757**

### Average Order Value (AOV)

* **Definition:** Average revenue per order.
* **Formula:** `Total Revenue / Total Orders`.
* **Source:** Derived; SQL: `kpi_summary`.
* **Verified current value:** **$2,117.89**
* **Business interpretation:** Note this is the *mean* — Phase 7 established order revenue is strongly right-skewed (skewness 3.51), so the *median* order ($1,146.00) is meaningfully lower. Both figures should be available where order-size KPIs are shown; AOV alone can overstate the "typical" order.

### Revenue per Customer

* **Definition:** Average total spend per purchasing customer.
* **Formula:** `Total Revenue / Total Purchasing Customers`.
* **Source:** Derived; SQL: `kpi_summary`.
* **Verified current value:** **$4,690.46**

### New Customers

* **Definition:** Count of customers whose *first-ever order* falls within a given period.
* **Formula:** `COUNT(DISTINCT CustomerKey)` where `MIN(Order Date)` for that customer falls in the period.
* **Source:** SQL: `sql/06_customer_analytics.sql` (`new_customers_per_year`); Python: `python/cohort_analysis.py` (cohort sizes, monthly grain).
* **Verified current value (2018, peak year):** **3,104**; (2020): **947**.
* **Business interpretation:** Acquisition trend. Do not confuse with "Customers" (total active base) — this is a period-scoped inflow metric.

### Repeat Customers

* **Definition:** Purchasing customers who have placed 2 or more distinct orders (ever, not period-scoped).
* **Formula:** `COUNT(DISTINCT CustomerKey)` where `COUNT(DISTINCT Order Number) >= 2`.
* **Source:** SQL: `repeat_vs_onetime_customers` (Phase 6).
* **Verified current value:** **7,272** customers (61.18% of purchasing customers).

### Repeat Purchase Rate

* **Definition:** % of purchasing customers who are repeat customers.
* **Formula:** `Repeat Customers / Total Purchasing Customers × 100`.
* **Source:** SQL: `repeat_vs_onetime_customers` (Phase 6).
* **Verified current value:** **61.18%**
* **Business interpretation:** This is the project's primary "retention" headline KPI for dashboard purposes (see distinction from "Customer Retention (Cohort)" below) — it answers "of everyone who has ever bought, what fraction came back at least once," with no time-window restriction. Repeat customers generate 82.39% of total revenue (Phase 6).

### Customer Lifetime Value (CLV) — Historical/Realized

* **Definition:** Average total revenue generated per customer over the entire dataset period. **This is a backward-looking, realized average — not a predictive/probabilistic CLV model** (which would require a churn-rate or survival model; per this project's own rules, no ML/predictive modeling is used unless explicitly added as a future extension — see Phase 15's "Future Improvements").
* **Formula:** Same as "Revenue per Customer": `Total Revenue / Total Purchasing Customers`.
* **Source:** Derived; also directly visible in the RFM `monetary` field's average (Phase 8).
* **Verified current value:** **$4,690.46** (identical to Revenue per Customer — same calculation, different name/context depending on dashboard framing).
* **Business interpretation:** Explicitly labeled "Historical CLV" on any dashboard using it, to avoid implying a predictive forecast this project doesn't produce.

### Revenue Growth (YoY)

* **Definition:** Year-over-year % change in total revenue, full years only.
* **Formula:** `(Revenue[year] - Revenue[year-1]) / Revenue[year-1] × 100`.
* **Source:** SQL: `sql/05_sales_analytics.sql` (`yearly_revenue_and_growth`).
* **Verified current values:** 2017: +6.83% • 2018: +72.32% • 2019: +42.81% • **2020: −49.11%** • 2021: not applicable (partial year).
* **Business interpretation:** Always exclude/flag 2021 in any YoY comparison. The 2020 decline is broad-based across all 8 product categories (Phase 5) and predates most RFM "disengagement" (Phase 8) — i.e., it's a real, dataset-wide fact, not a data artifact.

### Customer Retention (Cohort, Month-1)

* **Definition:** Average % of a monthly acquisition cohort that places another order exactly 1 calendar month after their first order, averaged across all cohorts with full exposure to that period.
* **Formula:** See `python/cohort_analysis.py` — `mean(active_customers_month1 / cohort_size)` across eligible cohorts.
* **Source:** Python: `python/cohort_analysis.py`; data: `data/processed/cohort_retention_pct.csv`.
* **Verified current value:** **2.84%**
* **Business interpretation:** **This is deliberately a different, much stricter metric than "Repeat Purchase Rate" above** — it measures return-within-exactly-one-month, not ever-returning. Given this is a long-cycle durable-goods business (median 2 orders/customer, 44.74% of repeat customers spacing orders >1 year apart — Phase 6/9), a low Month-1 figure is expected and should **never be displayed alongside Repeat Purchase Rate without this distinction being labeled**, to avoid the dashboard appearing to contradict itself (2.84% vs. 61.18% are both correct, at different time grains).

---

## Dashboard KPI Assignment (Applies to Phase 11/12)

To keep Power BI and Tableau consistent, each is assigned a fixed set of
headline KPIs, per the phase 11 brief:

| Dashboard Page | Headline KPIs (all defined above, no re-derivation) |
|---|---|
| Power BI — Executive Overview | Revenue, Orders, Customers, AOV, Revenue Growth (YoY), Repeat Purchase Rate |
| Power BI — Sales Performance | Revenue, Revenue Growth (Monthly/YoY), Units Sold, category/regional revenue breakdowns |
| Power BI — Customer Intelligence | Customers, New Customers, Repeat Customers, Repeat Purchase Rate, RFM segment distribution |
| Power BI — Retention | Repeat Purchase Rate (headline), Customer Retention (Cohort) matrix (supporting detail, explicitly labeled as a stricter month-grain metric) |
| Tableau — all views | Same KPI definitions as above; Tableau's role (Phase 12) is different *visual treatment and exploration*, not different numbers |

## Change Control

Any future change to a KPI formula must be made **here first**, then
propagated to SQL/Python sources and both BI tools — never the reverse.
This prevents the exact inconsistency this framework exists to avoid.
