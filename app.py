# app.py
import os
import pandas as pd
import streamlit as st
import altair as alt

from generate_urbanmart_sales import generate_urbanmart_sales

st.set_page_config(page_title="UrbanMart Dashboard", layout="wide")

DATA_PATH = "urbanmart_sales.csv"

# -----------------------
# Load (or generate) data
# -----------------------
@st.cache_data
def get_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        generate_urbanmart_sales(out_path=path, n_transactions=25000, seed=42)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sales_amount"] = pd.to_numeric(df["sales_amount"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    return df.dropna(subset=["date", "sales_amount"])

df = get_data(DATA_PATH)

# Derived time fields
df["day"] = df["date"].dt.date
df["weekday"] = df["date"].dt.day_name()
df["month"] = df["date"].dt.to_period("M").astype(str)

# -----------------------
# Sidebar filters
# -----------------------
st.sidebar.title("UrbanMart Filters")

min_d = df["date"].min().date()
max_d = df["date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
start_date, end_date = date_range

stores = sorted(df["store_id"].unique().tolist())
store_sel = st.sidebar.multiselect("Store(s)", stores, default=stores)

cats = sorted(df["product_category"].unique().tolist())
cat_sel = st.sidebar.multiselect("Category(s)", cats, default=cats)

channels = sorted(df["transaction_type"].unique().tolist())
channel_sel = st.sidebar.multiselect("Channel(s)", channels, default=channels)

fdf = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date) &
    (df["store_id"].isin(store_sel)) &
    (df["product_category"].isin(cat_sel)) &
    (df["transaction_type"].isin(channel_sel))
].copy()

# -----------------------
# Header KPIs
# -----------------------
st.title("UrbanMart — Sales Insights Dashboard")

total_sales = float(fdf["sales_amount"].sum())
orders = int(fdf["transaction_id"].nunique())
customers = int(fdf["customer_id"].nunique())
aov = total_sales / orders if orders else 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sales", f"{total_sales:,.2f}")
k2.metric("Orders", f"{orders:,}")
k3.metric("Customers", f"{customers:,}")
k4.metric("Avg Order Value", f"{aov:,.2f}")

st.divider()

# ============================================================
# 1) Which product categories are performing well
# ============================================================
st.subheader("1) Product Categories Performance")

cat_perf = fdf.groupby("product_category", as_index=False).agg(
    revenue=("sales_amount", "sum"),
    orders=("transaction_id", "nunique"),
    customers=("customer_id", "nunique"),
    units=("quantity", "sum"),
)
cat_perf["aov"] = cat_perf["revenue"] / cat_perf["orders"]

c1, c2 = st.columns([1.15, 1])

with c1:
    st.caption("Revenue by category")
    chart = alt.Chart(cat_perf).mark_bar().encode(
        x=alt.X("revenue:Q", title="Revenue"),
        y=alt.Y("product_category:N", sort="-x", title="Category"),
        tooltip=["product_category", "revenue", "orders", "customers", "units", "aov"]
    ).properties(height=360)
    st.altair_chart(chart, use_container_width=True)

with c2:
    st.caption("Category details")
    st.dataframe(cat_perf.sort_values("revenue", ascending=False), hide_index=True, use_container_width=True)

st.divider()

# ============================================================
# 2) How sales vary across stores and days
# ============================================================
st.subheader("2) Sales Variation Across Stores & Days")

left, right = st.columns(2)

daily = fdf.groupby("day", as_index=False).agg(revenue=("sales_amount", "sum"))
with left:
    st.caption("Daily sales trend")
    line = alt.Chart(daily).mark_line(point=True).encode(
        x=alt.X("day:T", title="Day"),
        y=alt.Y("revenue:Q", title="Revenue"),
        tooltip=["day", "revenue"]
    ).properties(height=300)
    st.altair_chart(line, use_container_width=True)

store_perf = fdf.groupby(["store_id", "store_location"], as_index=False).agg(
    revenue=("sales_amount", "sum"),
    orders=("transaction_id", "nunique"),
)
with right:
    st.caption("Revenue by store")
    bars = alt.Chart(store_perf).mark_bar().encode(
        x=alt.X("revenue:Q", title="Revenue"),
        y=alt.Y("store_id:N", sort="-x", title="Store"),
        tooltip=["store_id", "store_location", "revenue", "orders"]
    ).properties(height=300)
    st.altair_chart(bars, use_container_width=True)

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_perf = fdf.groupby("weekday", as_index=False).agg(revenue=("sales_amount", "sum"))
weekday_perf["weekday"] = pd.Categorical(weekday_perf["weekday"], categories=weekday_order, ordered=True)
weekday_perf = weekday_perf.sort_values("weekday")

st.caption("Weekday pattern")
wd = alt.Chart(weekday_perf).mark_bar().encode(
    x=alt.X("weekday:N", sort=weekday_order, title="Weekday"),
    y=alt.Y("revenue:Q", title="Revenue"),
    tooltip=["weekday", "revenue"]
).properties(height=240)
st.altair_chart(wd, use_container_width=True)

st.divider()

# ============================================================
# 3) Which customers are most valuable
# ============================================================
st.subheader("3) Most Valuable Customers")

cust = fdf.groupby(["customer_id", "customer_segment"], as_index=False).agg(
    total_spend=("sales_amount", "sum"),
    orders=("transaction_id", "nunique"),
    last_purchase=("date", "max"),
)
cust["avg_order_value"] = cust["total_spend"] / cust["orders"]
cust = cust.sort_values("total_spend", ascending=False)

top_n = st.slider("Top N customers", min_value=5, max_value=50, value=10, step=5)
top = cust.head(top_n)

c1, c2 = st.columns([1.1, 1])

with c1:
    st.caption("Top customers by total spend")
    top_chart = alt.Chart(top).mark_bar().encode(
        x=alt.X("total_spend:Q", title="Total Spend"),
        y=alt.Y("customer_id:N", sort="-x", title="Customer"),
        color=alt.Color("customer_segment:N", title="Segment"),
        tooltip=["customer_id", "customer_segment", "total_spend", "orders", "avg_order_value", "last_purchase"]
    ).properties(height=360)
    st.altair_chart(top_chart, use_container_width=True)

with c2:
    st.caption("Customer details")
    st.dataframe(top, hide_index=True, use_container_width=True)

with st.expander("Show raw filtered data"):
    st.dataframe(fdf.head(200), use_container_width=True)

st.caption("Dataset is synthetic and auto-generated for demo/deployment.")
