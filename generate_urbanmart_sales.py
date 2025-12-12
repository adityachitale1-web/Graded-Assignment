# generate_urbanmart_sales.py
import numpy as np
import pandas as pd
from datetime import datetime

def generate_urbanmart_sales(
    out_path: str = "urbanmart_sales.csv",
    n_transactions: int = 25000,
    seed: int = 42,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31"
) -> pd.DataFrame:
    """
    Generate a synthetic UrbanMart transactional dataset and save as CSV.

    Columns:
    - transaction_id
    - date
    - store_id
    - store_location
    - channel (Online/In-store)
    - customer_id
    - customer_segment
    - product_category
    - product_name
    - unit_price
    - quantity
    - discount_pct
    - sales_amount (net)
    - payment_method
    """
    rng = np.random.default_rng(seed)

    # Stores (mid-sized chain in a metro)
    stores = [
        ("S001", "Downtown"),
        ("S002", "Uptown"),
        ("S003", "Midtown"),
        ("S004", "Riverside"),
        ("S005", "Tech Park"),
        ("S006", "Old Town"),
    ]
    store_ids = np.array([s[0] for s in stores])
    store_locs = {sid: loc for sid, loc in stores}

    # Categories and products
    catalog = {
        "Groceries": [
            ("Rice 5kg", 18.0), ("Pasta Pack", 2.5), ("Olive Oil 1L", 10.0),
            ("Breakfast Cereal", 4.5), ("Coffee 250g", 6.0),
        ],
        "Beverages": [
            ("Sparkling Water 6-pack", 4.0), ("Orange Juice", 3.5),
            ("Soda 12-pack", 7.5), ("Green Tea Box", 3.0),
        ],
        "Household": [
            ("Laundry Detergent", 9.0), ("Dish Soap", 3.0),
            ("Paper Towels", 6.5), ("Trash Bags", 5.0),
        ],
        "Personal Care": [
            ("Shampoo", 6.0), ("Toothpaste", 2.5),
            ("Body Wash", 5.5), ("Deodorant", 4.0),
        ],
        "Electronics": [
            ("Wireless Earbuds", 45.0), ("Phone Charger", 15.0),
            ("Smart Speaker", 60.0), ("Power Bank", 25.0),
        ],
        "Clothing": [
            ("T-Shirt", 12.0), ("Jeans", 35.0),
            ("Sneakers", 55.0), ("Jacket", 70.0),
        ],
    }

    categories = np.array(list(catalog.keys()))

    # Customer base
    n_customers = 5000
    customer_ids = np.array([f"C{str(i).zfill(5)}" for i in range(1, n_customers + 1)])

    segments = np.array(["Budget", "Regular", "Premium"])
    segment_probs = np.array([0.35, 0.5, 0.15])

    customer_segment = rng.choice(segments, size=n_customers, p=segment_probs)
    customer_map = dict(zip(customer_ids, customer_segment))

    # Date generation
    start = np.datetime64(start_date)
    end = np.datetime64(end_date)
    days = (end - start).astype(int) + 1
    random_days = rng.integers(0, days, size=n_transactions)
    dates = start + random_days.astype("timedelta64[D]")

    # Seasonality / weekday effects (optional)
    # We'll apply a mild weekend uplift by biasing channel and quantity later.

    # Store assignment (slight differences)
    store_probs = np.array([0.22, 0.18, 0.20, 0.14, 0.16, 0.10])
    txn_store_ids = rng.choice(store_ids, size=n_transactions, p=store_probs)

    # Channel assignment
    channels = np.array(["Online", "In-store"])
    channel_probs = np.array([0.35, 0.65])
    txn_channels = rng.choice(channels, size=n_transactions, p=channel_probs)

    # Category assignment influenced by channel (electronics a bit more online)
    base_cat_probs = np.array([0.32, 0.14, 0.16, 0.14, 0.12, 0.12])  # sum=1
    # Small tweak: online shifts towards electronics
    cat_probs_online = base_cat_probs.copy()
    cat_probs_online[categories.tolist().index("Electronics")] += 0.05
    cat_probs_online[categories.tolist().index("Groceries")] -= 0.03
    cat_probs_online[categories.tolist().index("Household")] -= 0.02
    cat_probs_online = cat_probs_online / cat_probs_online.sum()

    txn_categories = []
    for ch in txn_channels:
        p = cat_probs_online if ch == "Online" else base_cat_probs
        txn_categories.append(rng.choice(categories, p=p))
    txn_categories = np.array(txn_categories)

    # Product selection + pricing
    product_names = []
    unit_prices = []
    for cat in txn_categories:
        items = catalog[cat]
        idx = rng.integers(0, len(items))
        name, price = items[idx]
        # small price noise
        price = float(np.round(price * rng.uniform(0.95, 1.10), 2))
        product_names.append(name)
        unit_prices.append(price)

    product_names = np.array(product_names)
    unit_prices = np.array(unit_prices, dtype=float)

    # Quantity (higher for groceries/household, lower for electronics)
    qty = np.ones(n_transactions, dtype=int)
    for i, cat in enumerate(txn_categories):
        if cat in ["Groceries", "Beverages", "Household", "Personal Care"]:
            qty[i] = int(rng.integers(1, 6))  # 1-5
        elif cat == "Clothing":
            qty[i] = int(rng.integers(1, 4))  # 1-3
        else:  # Electronics
            qty[i] = int(rng.integers(1, 3))  # 1-2

    # Discount %
    # More discount on clothing/electronics, less on groceries
    discount_pct = np.zeros(n_transactions, dtype=float)
    for i, cat in enumerate(txn_categories):
        if cat == "Groceries":
            discount_pct[i] = float(rng.choice([0, 0.05, 0.10], p=[0.75, 0.18, 0.07]))
        elif cat in ["Beverages", "Household", "Personal Care"]:
            discount_pct[i] = float(rng.choice([0, 0.05, 0.10, 0.15], p=[0.55, 0.25, 0.15, 0.05]))
        elif cat == "Clothing":
            discount_pct[i] = float(rng.choice([0, 0.10, 0.20, 0.30], p=[0.35, 0.35, 0.20, 0.10]))
        else:  # Electronics
            discount_pct[i] = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20], p=[0.40, 0.25, 0.20, 0.10, 0.05]))

    # Customer assignment (premium customers slightly more likely to buy electronics)
    txn_customers = rng.choice(customer_ids, size=n_transactions, replace=True)
    txn_segments = np.array([customer_map[c] for c in txn_customers])

    # Payment methods
    pm = np.array(["Card", "Cash", "Wallet", "UPI"])
    pm_probs_instore = np.array([0.45, 0.25, 0.15, 0.15])
    pm_probs_online = np.array([0.55, 0.00, 0.25, 0.20])

    payment_methods = []
    for ch in txn_channels:
        probs = pm_probs_online if ch == "Online" else pm_probs_instore
        payment_methods.append(rng.choice(pm, p=probs))
    payment_methods = np.array(payment_methods)

    # Sales amount (net)
    gross = unit_prices * qty
    net = np.round(gross * (1 - discount_pct), 2)

    # Transaction IDs
    txn_ids = np.array([f"T{str(i).zfill(7)}" for i in range(1, n_transactions + 1)])

    df = pd.DataFrame({
        "transaction_id": txn_ids,
        "date": pd.to_datetime(dates),
        "store_id": txn_store_ids,
        "store_location": [store_locs[s] for s in txn_store_ids],
        "transaction_type": txn_channels,  # Online / In-store
        "customer_id": txn_customers,
        "customer_segment": txn_segments,
        "product_category": txn_categories,
        "product_name": product_names,
        "unit_price": unit_prices,
        "quantity": qty,
        "discount_pct": discount_pct,
        "sales_amount": net,
        "payment_method": payment_methods,
    }).sort_values("date")

    df.to_csv(out_path, index=False)
    return df


if __name__ == "__main__":
    df = generate_urbanmart_sales()
    print("Generated:", df.shape, "-> urbanmart_sales.csv")
    print(df.head())
