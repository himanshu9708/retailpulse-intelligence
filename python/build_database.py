"""
Phase 4 — SQL Database & Data Modeling.

Builds a SQLite database at data/processed/ecommerce_analytics.db from the
cleaned CSVs in data/processed/ (output of Phase 3). Creates the star-schema
tables described in sql/schema.sql (dim_customer, dim_store, dim_product,
dim_subcategory, dim_category, dim_date, exchange_rate, fact_sales) with
primary keys, foreign keys, and indexes, then loads and validates row counts.

Run from the project root:
    python python/build_database.py
"""

from pathlib import Path
import sqlite3
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
DB_PATH = PROCESSED_DIR / "ecommerce_analytics.db"

# SQLite-adapted DDL (same structure/keys as sql/schema.sql; SQLite has no
# NUMERIC precision/scale or native BOOLEAN, so types are simplified but
# PRIMARY KEY / FOREIGN KEY / CHECK constraints are preserved).
SQLITE_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE dim_category (
    category_key    TEXT PRIMARY KEY,
    category_name   TEXT NOT NULL
);

CREATE TABLE dim_subcategory (
    subcategory_key     TEXT PRIMARY KEY,
    subcategory_name    TEXT NOT NULL,
    category_key        TEXT NOT NULL REFERENCES dim_category(category_key)
);

CREATE TABLE dim_product (
    product_key      INTEGER PRIMARY KEY,
    product_name     TEXT NOT NULL,
    brand            TEXT,
    color            TEXT,
    unit_cost_usd    REAL NOT NULL,
    unit_price_usd   REAL NOT NULL,
    subcategory_key  TEXT NOT NULL REFERENCES dim_subcategory(subcategory_key)
);

CREATE TABLE dim_customer (
    customer_key   INTEGER PRIMARY KEY,
    gender         TEXT,
    name           TEXT,
    city           TEXT,
    state_code     TEXT,
    state          TEXT,
    zip_code       TEXT,
    country        TEXT,
    continent      TEXT,
    birthday       TEXT
);

CREATE TABLE dim_store (
    store_key       INTEGER PRIMARY KEY,
    country         TEXT NOT NULL,
    state           TEXT,
    square_meters   REAL,
    open_date       TEXT,
    is_online       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE dim_date (
    date_key        TEXT PRIMARY KEY,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    day             INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,
    day_name        TEXT NOT NULL,
    is_weekend      INTEGER NOT NULL
);

CREATE TABLE exchange_rate (
    rate_date   TEXT NOT NULL,
    currency    TEXT NOT NULL,
    exchange    REAL NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

CREATE TABLE fact_sales (
    order_number     INTEGER NOT NULL,
    line_item        INTEGER NOT NULL,
    order_date       TEXT NOT NULL REFERENCES dim_date(date_key),
    delivery_date    TEXT,
    is_delivered     INTEGER NOT NULL,
    customer_key     INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    store_key        INTEGER NOT NULL REFERENCES dim_store(store_key),
    product_key      INTEGER NOT NULL REFERENCES dim_product(product_key),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    currency_code    TEXT NOT NULL,
    unit_price_usd   REAL NOT NULL,
    unit_cost_usd    REAL NOT NULL,
    revenue_usd      REAL NOT NULL,
    cost_usd         REAL NOT NULL,
    profit_usd       REAL NOT NULL,
    PRIMARY KEY (order_number, line_item)
);

CREATE INDEX idx_fact_sales_customer   ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product    ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_store      ON fact_sales(store_key);
CREATE INDEX idx_fact_sales_order_date ON fact_sales(order_date);
CREATE INDEX idx_product_subcategory   ON dim_product(subcategory_key);
CREATE INDEX idx_subcategory_category  ON dim_subcategory(category_key);
"""


def build_dim_date(min_date, max_date) -> pd.DataFrame:
    dates = pd.date_range(min_date, max_date, freq="D")
    df = pd.DataFrame({"date_key": dates})
    df["year"] = df["date_key"].dt.year
    df["quarter"] = df["date_key"].dt.quarter
    df["month"] = df["date_key"].dt.month
    df["month_name"] = df["date_key"].dt.month_name()
    df["day"] = df["date_key"].dt.day
    df["day_of_week"] = df["date_key"].dt.dayofweek
    df["day_name"] = df["date_key"].dt.day_name()
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["date_key"] = df["date_key"].dt.strftime("%Y-%m-%d")
    return df


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()

    customers = pd.read_csv(PROCESSED_DIR / "customers_clean.csv")
    products = pd.read_csv(PROCESSED_DIR / "products_clean.csv")
    stores = pd.read_csv(PROCESSED_DIR / "stores_clean.csv")
    exchange = pd.read_csv(PROCESSED_DIR / "exchange_rates_clean.csv")
    sales = pd.read_csv(PROCESSED_DIR / "sales_clean.csv")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SQLITE_DDL)

    # --- dim_category / dim_subcategory (derived from Products) ---
    dim_category = (
        products[["CategoryKey", "Category"]]
        .drop_duplicates()
        .rename(columns={"CategoryKey": "category_key", "Category": "category_name"})
    )
    dim_category["category_key"] = dim_category["category_key"].astype(str)

    dim_subcategory = (
        products[["SubcategoryKey", "Subcategory", "CategoryKey"]]
        .drop_duplicates()
        .rename(columns={
            "SubcategoryKey": "subcategory_key",
            "Subcategory": "subcategory_name",
            "CategoryKey": "category_key",
        })
    )
    dim_subcategory["subcategory_key"] = dim_subcategory["subcategory_key"].astype(str)
    dim_subcategory["category_key"] = dim_subcategory["category_key"].astype(str)

    dim_product = products.rename(columns={
        "ProductKey": "product_key", "Product Name": "product_name",
        "Brand": "brand", "Color": "color",
        "Unit Cost USD": "unit_cost_usd", "Unit Price USD": "unit_price_usd",
        "SubcategoryKey": "subcategory_key",
    })[["product_key", "product_name", "brand", "color", "unit_cost_usd",
        "unit_price_usd", "subcategory_key"]]
    dim_product["subcategory_key"] = dim_product["subcategory_key"].astype(str)

    dim_customer = customers.rename(columns={
        "CustomerKey": "customer_key", "Gender": "gender", "Name": "name",
        "City": "city", "State Code": "state_code", "State": "state",
        "Zip Code": "zip_code", "Country": "country", "Continent": "continent",
        "Birthday": "birthday",
    })[["customer_key", "gender", "name", "city", "state_code", "state",
        "zip_code", "country", "continent", "birthday"]]

    dim_store = stores.rename(columns={
        "StoreKey": "store_key", "Country": "country", "State": "state",
        "Square Meters": "square_meters", "Open Date": "open_date",
        "Is_Online": "is_online",
    })[["store_key", "country", "state", "square_meters", "open_date", "is_online"]]
    dim_store["is_online"] = dim_store["is_online"].astype(int)

    dim_date = build_dim_date(sales["Order Date"].min(), sales["Order Date"].max())

    exchange_rate = exchange.rename(columns={
        "Date": "rate_date", "Currency": "currency", "Exchange": "exchange"
    })[["rate_date", "currency", "exchange"]]

    fact_sales = sales.rename(columns={
        "Order Number": "order_number", "Line Item": "line_item",
        "Order Date": "order_date", "Delivery Date": "delivery_date",
        "Is_Delivered": "is_delivered", "CustomerKey": "customer_key",
        "StoreKey": "store_key", "ProductKey": "product_key",
        "Quantity": "quantity", "Currency Code": "currency_code",
        "Unit Price USD": "unit_price_usd", "Unit Cost USD": "unit_cost_usd",
        "Revenue USD": "revenue_usd", "Cost USD": "cost_usd", "Profit USD": "profit_usd",
    })[["order_number", "line_item", "order_date", "delivery_date", "is_delivered",
        "customer_key", "store_key", "product_key", "quantity", "currency_code",
        "unit_price_usd", "unit_cost_usd", "revenue_usd", "cost_usd", "profit_usd"]]
    fact_sales["is_delivered"] = fact_sales["is_delivered"].astype(int)

    # Load in FK-safe order: categories -> subcategories -> products,
    # customers, stores, dates, exchange rates, then the fact table last.
    dim_category.to_sql("dim_category", conn, if_exists="append", index=False)
    dim_subcategory.to_sql("dim_subcategory", conn, if_exists="append", index=False)
    dim_product.to_sql("dim_product", conn, if_exists="append", index=False)
    dim_customer.to_sql("dim_customer", conn, if_exists="append", index=False)
    dim_store.to_sql("dim_store", conn, if_exists="append", index=False)
    dim_date.to_sql("dim_date", conn, if_exists="append", index=False)
    exchange_rate.to_sql("exchange_rate", conn, if_exists="append", index=False)
    fact_sales.to_sql("fact_sales", conn, if_exists="append", index=False)

    conn.commit()

    print(f"Database built at {DB_PATH}")
    for table in ["dim_category", "dim_subcategory", "dim_product", "dim_customer",
                  "dim_store", "dim_date", "exchange_rate", "fact_sales"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f" - {table}: {n:,} rows")

    conn.close()


if __name__ == "__main__":
    main()
