# urbanmart_analysis.py
import os
import pandas as pd
from generate_urbanmart_sales import generate_urbanmart_sales

def main():
    # 2a) Welcome message using variables and f-strings
    store_name = "UrbanMart"
    print(f"Welcome to {store_name} Sales Analysis")

    # Ensure dataset exists
    csv_path = "urbanmart_sales.csv"
    if not os.path.exists(csv_path):
        print("Dataset not found. Generating urbanmart_sales.csv ...")
        generate_urbanmart_sales(out_path=csv_path, n_transactions=25000, seed=42)

    # 2b) Read CSV file using pandas.read_csv()
    df = pd.read_csv(csv_path)

    # 2c) Basic sanity checks
    print("\n--- Sanity Checks ---")
    print(f"Total number of rows: {len(df):,}")

    unique_store_ids = sorted(df["store_id"].dropna().unique().tolist())
    print(f"Unique store IDs: {unique_store_ids}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    print(f"Date range (min to max): {df['date'].min()} to {df['date'].max()}")

    # 3) Use basic lists, tuples, and dictionaries
    product_categories = sorted(df["product_category"].dropna().unique().tolist())
    print("\nProduct categories list:")
    print(product_categories)

    # store_id -> store_location dictionary
    store_map = {}
    store_rows = df[["store_id", "store_location"]].dropna().drop_duplicates()
    for _, row in store_rows.iterrows():
        store_map[row["store_id"]] = row["store_location"]

    print("\nStore dictionary (store_id -> store_location):")
    for k in sorted(store_map.keys()):
        print(f"{k} -> {store_map[k]}")

    # Manual loop to count Online vs In-store (no pandas groupby/value_counts)
    online_count = 0
    instore_count = 0

    for t in df["transaction_type"].tolist():
        if isinstance(t, str):
            tt = t.strip().lower()
            if tt == "online":
                online_count += 1
            elif tt in ("in-store", "instore", "in store"):
                instore_count += 1

    print("\nManual transaction counts:")
    print(f"Online: {online_count:,}")
    print(f"In-store: {instore_count:,}")

if __name__ == "__main__":
    main()
