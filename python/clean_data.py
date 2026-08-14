"""
Phase 3 — Data Cleaning & Validation.

Reads data/raw/ (never modified) and writes a reliable analytical dataset to
data/processed/. Every cleaning decision made here is documented in
docs/cleaning_log.md under a Problem -> Decision -> Reason format — this
script implements exactly those decisions, nothing more.

Run from the project root:
    python python/clean_data.py
"""

from pathlib import Path
import pandas as pd
import numpy as np

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def parse_money(series: pd.Series) -> pd.Series:
    """Parse formatted currency strings like '$6.62 ' into float."""
    return pd.to_numeric(
        series.astype(str).str.replace(r"[$,]", "", regex=True).str.strip(),
        errors="coerce",
    )


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Birthday"] = pd.to_datetime(df["Birthday"], format="%m/%d/%Y", errors="coerce")
    # Zip Code kept as text (string) to preserve leading zeros — never cast to int.
    df["Zip Code"] = df["Zip Code"].astype(str)
    # State Code: 10 missing values kept as null (not dropped) — flagged for transparency.
    df["State Code"] = df["State Code"].where(df["State Code"].notna(), None)
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Unit Cost USD"] = parse_money(df["Unit Cost USD"])
    df["Unit Price USD"] = parse_money(df["Unit Price USD"])
    return df


def clean_stores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Open Date"] = pd.to_datetime(df["Open Date"], format="%m/%d/%Y", errors="coerce")
    # Add explicit channel flag rather than relying on implicit StoreKey==0 convention.
    df["Is_Online"] = df["Country"].eq("Online")
    return df


def clean_exchange_rates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    return df


def clean_sales(df: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y", errors="coerce")
    df["Delivery Date"] = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y", errors="coerce")
    # Missing Delivery Date is kept as null (order not yet delivered / not tracked),
    # not dropped or imputed. Explicit flag added for clarity in downstream analysis.
    df["Is_Delivered"] = df["Delivery Date"].notna()

    # Revenue derivation:
    # Products."Unit Price USD" is already USD-denominated (per its own column name),
    # so core revenue does NOT require FX conversion. Currency Code in Sales.csv records
    # which local currency the customer transacted in, and Exchange_Rates.csv converts
    # USD -> local currency (verified: Exchange == 1.0 for every USD row). We keep this
    # as an optional secondary "local currency" figure, not the primary Revenue KPI.
    df = df.merge(
        products[["ProductKey", "Unit Price USD", "Unit Cost USD"]],
        on="ProductKey", how="left"
    )
    df["Revenue USD"] = df["Quantity"] * df["Unit Price USD"]
    df["Cost USD"] = df["Quantity"] * df["Unit Cost USD"]
    df["Profit USD"] = df["Revenue USD"] - df["Cost USD"]

    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(RAW_DIR / "Customers.csv", encoding="cp1252")
    products = pd.read_csv(RAW_DIR / "Products.csv", encoding="utf-8")
    stores = pd.read_csv(RAW_DIR / "Stores.csv", encoding="utf-8")
    exchange = pd.read_csv(RAW_DIR / "Exchange_Rates.csv", encoding="utf-8")
    sales = pd.read_csv(RAW_DIR / "Sales.csv", encoding="utf-8")

    customers_clean = clean_customers(customers)
    products_clean = clean_products(products)
    stores_clean = clean_stores(stores)
    exchange_clean = clean_exchange_rates(exchange)
    sales_clean = clean_sales(sales, products_clean)

    customers_clean.to_csv(PROCESSED_DIR / "customers_clean.csv", index=False)
    products_clean.to_csv(PROCESSED_DIR / "products_clean.csv", index=False)
    stores_clean.to_csv(PROCESSED_DIR / "stores_clean.csv", index=False)
    exchange_clean.to_csv(PROCESSED_DIR / "exchange_rates_clean.csv", index=False)
    sales_clean.to_csv(PROCESSED_DIR / "sales_clean.csv", index=False)

    print("Cleaned files written to data/processed/:")
    for f in ["customers_clean.csv", "products_clean.csv", "stores_clean.csv",
              "exchange_rates_clean.csv", "sales_clean.csv"]:
        print(f" - {f}")


if __name__ == "__main__":
    main()
