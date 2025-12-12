# analytics_functions.py

import pandas as pd
from datetime import date


# -----------------------------------------
# 0️⃣ Ensure date column is valid
# -----------------------------------------
def ensure_date_column(df, col='collection_date'):
    df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


# -----------------------------------------
# 1️⃣ Filter rows by date range
# -----------------------------------------
def filter_by_date(df, start, end, date_col='collection_date'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    df["_d"] = df[date_col].dt.date
    out = df[(df["_d"] >= start) & (df["_d"] <= end)].drop(columns=["_d"])
    return out


# -----------------------------------------
# 2️⃣ Total Revenue
# -----------------------------------------
def total_revenue(df, start, end, price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)
    return float(df2[price_col].sum())


# -----------------------------------------
# 3️⃣ Top N Cities
# -----------------------------------------
def top_n_cities(df, start, end, n=5, city_col='city', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)

    g = (
        df2.groupby(city_col)[price_col]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "revenue", "count": "bookings"})
        .sort_values("revenue", ascending=False)
    )
    return g.head(n)


# -----------------------------------------
# 4️⃣ Daily Revenue Trend
# -----------------------------------------
def daily_revenue_trend(df, start, end, date_col='collection_date', price_col='price'):
    df2 = filter_by_date(df, start, end)

    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)
    df2["day"] = pd.to_datetime(df2[date_col]).dt.date

    g = df2.groupby("day")[price_col].sum().reset_index()
    return g.sort_values("day")


# -----------------------------------------
# 5️⃣ Hourly Trend (Peak Hour)
# -----------------------------------------
def hourly_trend(df, start, end, time_col='collection_time', date_col='collection_date'):
    df2 = filter_by_date(df, start, end)

    if time_col not in df2.columns:
        return pd.DataFrame()

    df2[time_col] = pd.to_datetime(df2[time_col], errors="coerce")
    df2["hour"] = df2[time_col].dt.hour

    g = df2.groupby("hour")["hour"].count().reset_index(name="bookings")
    return g.sort_values("hour")


# -----------------------------------------
# 6️⃣ Test-wise Revenue
# -----------------------------------------
def test_wise_revenue(df, start, end, test_col='test_mapped', price_col='price'):
    if test_col not in df.columns:
        return pd.DataFrame()

    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)

    g = (
        df2.groupby(test_col)[price_col]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "revenue", "count": "bookings"})
        .sort_values("revenue", ascending=False)
    )
    return g


# -----------------------------------------
# 7️⃣ Source-wise Revenue
# -----------------------------------------
def revenue_by_source(df, start, end, source_col='source', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)

    g = (
        df2.groupby(source_col)[price_col]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "revenue", "count": "bookings"})
        .sort_values("revenue", ascending=False)
    )
    return g


# -----------------------------------------
# 8️⃣ Revenue Contribution (% share city/source)
# -----------------------------------------
def revenue_contribution(df, start, end, group_col='city', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)

    total = df2[price_col].sum()

    g = (
        df2.groupby(group_col)[price_col]
        .sum()
        .reset_index(name='revenue')
    )
    g["pct_share"] = (g["revenue"] / total * 100).round(2)
    return g.sort_values("revenue", ascending=False)


# -----------------------------------------
# 9️⃣ City × Source Matrix
# -----------------------------------------
def city_source_matrix(df, start, end, city_col='city', source_col='source', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors="coerce").fillna(0)

    pivot = pd.pivot_table(
        df2,
        index=city_col,
        columns=source_col,
        values=price_col,
        aggfunc="sum",
        fill_value=0
    )
    return pivot


# -----------------------------------------
# 🔟 Growth / Decline Calculation
# -----------------------------------------
def growth_decline(df, prev_start, prev_end, curr_start, curr_end, city):
    prev = top_n_cities(df[df['city'] == city], prev_start, prev_end, n=1)
    curr = top_n_cities(df[df['city'] == city], curr_start, curr_end, n=1)

    prev_rev = float(prev["revenue"].sum() or 0)
    curr_rev = float(curr["revenue"].sum() or 0)

    if prev_rev == 0:
        decline = None
    else:
        decline = round(((curr_rev - prev_rev) / prev_rev) * 100, 2)

    return {
        "city": city,
        "previous_revenue": prev_rev,
        "current_revenue": curr_rev,
        "decline_percent": decline
    }
