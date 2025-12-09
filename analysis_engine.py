# analysis_engine.py
from date_parser import parse_date_range
from analytics_functions import (
    total_revenue, top_n_cities, daily_trend, kpis_summary
)
import pandas as pd
from datetime import datetime, timezone
import re


def interpret_and_run(nl_query: str, df: pd.DataFrame):
    """
    Interpret a user's natural-language query and run the appropriate analytics function.
    """

    q = nl_query.lower().strip()

    # --- 1) Parse dates safely ---
    start, end = parse_date_range(q, reference=datetime.now(timezone.utc))

    if start is None or end is None:
        # default: last 7 days
        end = datetime.now(timezone.utc).date()
        start = end - pd.Timedelta(days=6)

    # --- 2) Revenue questions ---
    if any(word in q for word in ['revenue', 'sales', 'amount']):
        value = total_revenue(df, start, end)
        return ("Total revenue", value,
                {'type': 'value', 'start': str(start), 'end': str(end)})

    # --- 3) Top N cities ---
    m = re.search(r'top\s+(\d+)\s+cities', q)
    if m:
        n = int(m.group(1))
        table = top_n_cities(df, start, end, n=n)
        return (f"Top {n} cities by revenue", table,
                {'type': 'table', 'start': str(start), 'end': str(end)})

    # --- 4) Default top cities ---
    if 'top cities' in q or 'top city' in q:
        table = top_n_cities(df, start, end, n=5)
        return ("Top 5 cities by revenue", table,
                {'type': 'table', 'start': str(start), 'end': str(end)})

    # --- 5) Daily trend ---
    if any(word in q for word in ['trend', 'daily', 'day wise', 'day-wise']):
        table = daily_trend(df, start, end)
        return (f"Daily revenue trend ({start} → {end})", table,
                {'type': 'table', 'start': str(start), 'end': str(end)})

    # --- 6) KPIs summary ---
    if any(word in q for word in ['kpi', 'summary', 'overview', 'metrics']):
        s = kpis_summary(df, start, end)
        return ("KPIs summary", s,
                {'type': 'value', 'start': str(start), 'end': str(end)})

    # --- 7️⃣ Fallback: Find max revenue day ---
    if any(word in q for word in ['max', 'maximum', 'highest']):
        dt = daily_trend(df, start, end)

        if not dt.empty:
            # Safely locate peak revenue column
            revenue_col = dt.columns[1]   # always second col after 'day'
            max_idx = dt[revenue_col].idxmax()
            row = dt.loc[max_idx]

            return ("Peak day",
                    {'day': str(row['day']), 'revenue': float(row[revenue_col])},
                    {'type': 'value', 'start': str(start), 'end': str(end)})

    # --- 8️⃣ Final fallback ---
    s = kpis_summary(df, start, end)
    return ("KPIs summary (fallback)", s,
            {'type': 'value', 'start': str(start), 'end': str(end)})
