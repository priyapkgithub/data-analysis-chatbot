# analysis_engine.py
import pandas as pd
import re
from datetime import datetime, timezone
from date_parser import parse_date_range
from analytics_functions import (
    total_revenue,
    top_n_cities,
    growth_decline,
    revenue_by_source
)

def interpret_and_run(q, df):
    q_low = q.lower()

    # 1️⃣ Determine date range
    start, end = parse_date_range(q, reference=datetime.now(timezone.utc))
    if start is None:
        end = datetime.now(timezone.utc).date()
        start = end - pd.Timedelta(days=6)

    # 2️⃣ Top N cities
    m = re.search(r"top\s+(\d+)\s+cities", q_low)
    if m:
        n = int(m.group(1))
        return f"Top {n} cities by revenue", top_n_cities(df, start, end, n=n), {"type": "table"}

    if "top cities" in q_low:
        return "Top 5 cities by revenue", top_n_cities(df, start, end), {"type": "table"}

    # 3️⃣ Source-wise revenue
    if "source wise" in q_low or "sourcewise" in q_low:
        return "Revenue by Source", revenue_by_source(df, start, end), {"type": "table"}

    # 4️⃣ Degrowth or decline
    if "degrow" in q_low or "decline" in q_low:
        cities = df["city"].dropna().unique()
        out = []
        prev_start = start - pd.Timedelta(days=(end - start).days + 1)
        prev_end = start - pd.Timedelta(days=1)

        for city in cities:
            out.append(growth_decline(df, prev_start, prev_end, start, end, city))

        out_df = pd.DataFrame(out)
        return "City Degrowth Report", out_df.sort_values("decline_percent", ascending=False), {"type": "table"}

    # 5️⃣ Revenue
    if "revenue" in q_low:
        return "Total Revenue", total_revenue(df, start, end), {"type": "value"}

    # Default
    return "Not Recognized", {"query": q}, {"type": "text"}
