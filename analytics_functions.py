# analytics_functions.py
import pandas as pd
from datetime import date

def ensure_date_column(df, col='collection_date'):
    df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


# 1️⃣ Total Revenue
def total_revenue(df, start, end, price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)
    return float(df2[price_col].sum())


# 2️⃣ Filter rows by date
def filter_by_date(df, start, end, date_col='collection_date'):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['_d'] = df[date_col].dt.date
    return df[(df['_d'] >= start) & (df['_d'] <= end)].drop(columns=['_d'])


# 3️⃣ Top N cities
def top_n_cities(df, start, end, n=5, city_col='city', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    g = df2.groupby(city_col)[price_col].agg(['sum', 'count']).reset_index()
    g = g.rename(columns={'sum': 'revenue', 'count': 'bookings'})
    return g.sort_values('revenue', ascending=False).head(n)


# 4️⃣ Growth/Decline Calculator
def growth_decline(df, prev_start, prev_end, curr_start, curr_end, city):
    prev = top_n_cities(df[df['city'] == city], prev_start, prev_end, n=1)
    curr = top_n_cities(df[df['city'] == city], curr_start, curr_end, n=1)

    prev_rev = float(prev['revenue'].sum() or 0)
    curr_rev = float(curr['revenue'].sum() or 0)

    if prev_rev == 0:
        decline = None
    else:
        decline = round(((prev_rev - curr_rev) / prev_rev) * 100, 2)

    return {
        "city": city,
        "previous_revenue": prev_rev,
        "current_revenue": curr_rev,
        "decline_percent": decline
    }


# 5️⃣ Source-wise revenue
def revenue_by_source(df, start, end, source_col='source', price_col='price'):
    df2 = filter_by_date(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    g = df2.groupby(source_col)[price_col].agg(['sum', 'count']).reset_index()
    g = g.rename(columns={'sum': 'revenue', 'count': 'bookings'})
    return g.sort_values('revenue', ascending=False)
