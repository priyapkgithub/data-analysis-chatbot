# analytics_functions.py
import pandas as pd
from datetime import date   # Only 'date' is needed


def ensure_date_column(df: pd.DataFrame, colname: str = 'collection_date') -> pd.DataFrame:
    """
    Ensure df[colname] is datetime64 and valid for date filtering.
    Converts in-place and returns the DataFrame.
    """
    if colname not in df.columns:
        raise ValueError(f"Date column '{colname}' not in dataframe.")

    df[colname] = pd.to_datetime(df[colname], errors='coerce')

    if df[colname].isna().all():
        raise ValueError(f"All values in '{colname}' failed date conversion.")

    return df


def filter_by_date_range(
    df: pd.DataFrame,
    start: date,
    end: date,
    date_col: str = 'collection_date'
) -> pd.DataFrame:
    """
    Filter dataframe rows by date range on the given date column.
    """
    df = df.copy()
    df = ensure_date_column(df, date_col)

    df['_date'] = df[date_col].dt.date
    mask = (df['_date'] >= start) & (df['_date'] <= end)

    return df.loc[mask].drop(columns=['_date'])


def total_revenue(
    df: pd.DataFrame,
    start: date,
    end: date,
    price_col: str = 'price'
) -> float:
    """
    Calculate total revenue inside the date range.
    """
    df2 = filter_by_date_range(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    return float(df2[price_col].sum())


def top_n_cities(
    df: pd.DataFrame,
    start: date,
    end: date,
    n: int = 5,
    city_col: str = 'city',
    price_col: str = 'price'
) -> pd.DataFrame:
    """
    Get top N cities by revenue and booking count.
    """
    df2 = filter_by_date_range(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    agg = (
        df2.groupby(city_col)[price_col]
        .agg(['sum', 'count'])
        .reset_index()
        .sort_values('sum', ascending=False)
    )

    agg = agg.rename(columns={'sum': 'revenue', 'count': 'bookings'})
    return agg.head(n)


def daily_trend(
    df: pd.DataFrame,
    start: date,
    end: date,
    price_col: str = 'price',
    date_col: str = 'collection_date'
) -> pd.DataFrame:
    """
    Daily revenue trend between dates.
    """
    df2 = filter_by_date_range(df, start, end, date_col)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    df2['day'] = df2[date_col].dt.date
    agg = df2.groupby('day')[price_col].sum().reset_index().sort_values('day')

    return agg


def kpis_summary(
    df: pd.DataFrame,
    start: date,
    end: date,
    price_col: str = 'price'
) -> dict:
    """
    Returns summary KPIs: revenue, bookings count, avg order value.
    """
    df2 = filter_by_date_range(df, start, end)
    df2[price_col] = pd.to_numeric(df2[price_col], errors='coerce').fillna(0)

    total_rev = float(df2[price_col].sum())
    total_bookings = int(len(df2))
    avg_price = float(df2[price_col].mean()) if total_bookings > 0 else 0.0

    return {
        "total_revenue": total_rev,
        "total_bookings": total_bookings,
        "avg_price": avg_price
    }
