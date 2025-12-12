import re
import pandas as pd
from datetime import datetime, timezone, timedelta

from date_parser import parse_date_range
from analytics_functions import (
    total_revenue,
    top_n_cities,
    daily_revenue_trend,
    hourly_trend,
    test_wise_revenue,
    revenue_by_source,
    revenue_contribution,
    city_source_matrix,
    growth_decline,
)


def _previous_period(start: datetime.date, end: datetime.date):
    """
    Return previous contiguous period (same length) immediately before `start`.
    """
    length_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length_days - 1)
    return prev_start, prev_end


def _safe_date_parse(nl_query: str):
    """
    Use parse_date_range; fallback to last 7 days.
    Returns (start_date, end_date)
    """
    start, end = parse_date_range(nl_query, reference=datetime.now(timezone.utc))
    if start is None or end is None:
        end = datetime.now(timezone.utc).date()
        start = end - pd.Timedelta(days=6)
    return start, end


def interpret_and_run(nl_query: str, df: pd.DataFrame):
    """
    Interpret natural-language query and dispatch to analytics functions.

    Returns (title, result, meta) where meta is a dict containing {'type': 'table'|'value'|'text', ...}
    """
    q = (nl_query or "").strip().lower()

    # normalize dataframe (ensure expected cols)
    df = df.copy()
    # ensure collection_date is datetime dtype (analytics_functions assume this)
    if "collection_date" in df.columns:
        df["collection_date"] = pd.to_datetime(df["collection_date"], errors="coerce")

    start, end = _safe_date_parse(q)

    # QUICK DETECT: explicit compare phrase "vs" or "compare"
    comp_m = re.search(r'compare\s+(.+?)\s+vs\.?\s+(.+)', q)
    if comp_m:
        # attempt to interpret as two date ranges or two tokens (e.g. city vs city)
        left = comp_m.group(1).strip()
        right = comp_m.group(2).strip()
        # if left/right look like dates or periods -> fallback complexity; for now return not implemented
        return ("Compare", f"Comparison requested between '{left}' and '{right}' — complex compare currently supports date ranges and city v city via specific queries.", {"type": "text"})

    # 1) Direct degrowth / decline request
    if any(w in q for w in ["degrow", "decline", "drop", "decrease", "de-growing", "dropped"]):
        prev_start, prev_end = _previous_period(start, end)
        cities = sorted([c for c in df["city"].dropna().unique()]) if "city" in df.columns else []
        rows = []
        for city in cities:
            rows.append(growth_decline(df, prev_start, prev_end, start, end, city))
        out = pd.DataFrame(rows)
        # sort by absolute decline percent (descending)
        if "decline_percent" in out.columns:
            out = out.sort_values("decline_percent", ascending=False, na_position="last")
        return ("City Degrowth Report", out, {"type": "table", "start": str(start), "end": str(end), "prev_start": str(prev_start), "prev_end": str(prev_end)})

    # 2) City-specific auto-analysis: if user mentions a city name present in data, return quick KPIs + top sources
    if "city" in df.columns:
        cities = [str(x).lower() for x in df["city"].dropna().unique()]
        for city in cities:
            if city and city in q:
                prev_start, prev_end = _previous_period(start, end)
                city_mask = df["city"].str.lower() == city
                current_revenue = total_revenue(df[city_mask], start, end)
                prev_revenue = total_revenue(df[city_mask], prev_start, prev_end)
                pct_change = None
                if prev_revenue > 0:
                    pct_change = round(((current_revenue - prev_revenue) / prev_revenue) * 100, 2)
                top_sources = revenue_by_source(df[city_mask], start, end)
                top_tests = test_wise_revenue(df[city_mask], start, end).head(5) if "test_mapped" in df.columns else None
                result = {
                    "city": city.title(),
                    "current_revenue": current_revenue,
                    "previous_revenue": prev_revenue,
                    "pct_change": pct_change,
                    "top_sources": top_sources.to_dict(orient="records") if top_sources is not None else [],
                    "top_tests": top_tests.to_dict(orient="records") if top_tests is not None else [],
                }
                return (f"Performance Summary — {city.title()}", result, {"type": "value", "start": str(start), "end": str(end)})

    # 3) Top N cities
    m = re.search(r'top\s+(\d+)\s+cities', q)
    if m:
        n = int(m.group(1))
        table = top_n_cities(df, start, end, n=n)
        return (f"Top {n} cities by revenue", table, {"type": "table", "start": str(start), "end": str(end)})

    if "top cities" in q or "top city" in q:
        table = top_n_cities(df, start, end, n=5)
        return ("Top 5 cities by revenue", table, {"type": "table", "start": str(start), "end": str(end)})

    # 4) Daily trend / time trend
    if any(w in q for w in ["daily", "day wise", "day-wise", "trend", "daily trend"]):
        table = daily_revenue_trend(df, start, end)
        return (f"Daily revenue trend ({start} → {end})", table, {"type": "table", "start": str(start), "end": str(end)})

    # hourly / peak hour
    if any(w in q for w in ["hour", "peak hour", "peak booking", "peak bookings", "booking hour"]):
        # require collection_time column to exist
        if "collection_time" in df.columns:
            table = hourly_trend(df, start, end, time_col="collection_time")
            # compute peak hour
            peak = table.loc[table["bookings"].idxmax()] if not table.empty else None
            meta = {"type": "table", "start": str(start), "end": str(end)}
            return ("Hourly bookings distribution", table, meta)
        else:
            return ("Hourly data unavailable", "No 'collection_time' column present in dataset.", {"type": "text"})

    # 5) Test-wise insights
    if any(w in q for w in ["test", "tests", "test_mapped"]):
        if "test_mapped" in df.columns:
            table = test_wise_revenue(df, start, end)
            return (f"Test-wise revenue ({start} → {end})", table, {"type": "table", "start": str(start), "end": str(end)})
        else:
            return ("No test data", "Dataset does not contain 'test_mapped' column.", {"type": "text"})

    # 6) Source-wise revenue
    if any(w in q for w in ["source", "sources", "channel", "utm", "traffic source"]):
        table = revenue_by_source(df, start, end)
        return (f"Revenue by source ({start} → {end})", table, {"type": "table", "start": str(start), "end": str(end)})

    # 7) Contribution analysis (city / source percent)
    if any(w in q for w in ["contribution", "share", "percent", "% of revenue", "contributes"]):
        # prefer group by city if user mentions city, else source if mentions source
        if "city" in q:
            contrib = revenue_contribution(df, start, end, group_col="city")
            return (f"City revenue contribution ({start} → {end})", contrib, {"type": "table", "start": str(start), "end": str(end)})
        elif "source" in q:
            contrib = revenue_contribution(df, start, end, group_col="source")
            return (f"Source revenue contribution ({start} → {end})", contrib, {"type": "table", "start": str(start), "end": str(end)})
        else:
            contrib = revenue_contribution(df, start, end, group_col="city")
            return (f"Revenue contribution by city ({start} → {end})", contrib, {"type": "table", "start": str(start), "end": str(end)})

    # 8) City x Source matrix
    if "matrix" in q or ("city" in q and "source" in q) or ("city x source" in q) or ("city by source" in q):
        matrix = city_source_matrix(df, start, end)
        return (f"City × Source revenue matrix ({start} → {end})", matrix, {"type": "table", "start": str(start), "end": str(end)})

    # 9) Revenue / KPI summary
    if any(w in q for w in ["revenue", "sales", "total revenue", "kpi", "summary", "overview", "metrics"]):
        val = total_revenue(df, start, end)
        # basic KPIs could be added here (bookings, avg order value)
        bookings = len(filter_by_date := df)  # placeholder: not ideal if date filter required
        # safer basic KPIs:
        try:
            filtered = df.copy()
            filtered["_d"] = filtered["collection_date"].dt.date
            filtered = filtered[(filtered["_d"] >= start) & (filtered["_d"] <= end)]
            bookings = len(filtered)
            aov = None
            if bookings > 0:
                aov = round(filtered["price"].astype(float).sum() / bookings, 2)
        except Exception:
            aov = None
        summary = {"total_revenue": val, "bookings": bookings, "avg_order_value": aov}
        return ("KPI Summary", summary, {"type": "value", "start": str(start), "end": str(end)})

    # 10) Peak / max day
    if any(w in q for w in ["max", "maximum", "highest", "peak day", "peak revenue"]):
        table = daily_revenue_trend(df, start, end)
        if not table.empty:
            row = table.loc[table["price"].idxmax()]
            return ("Peak day", {"day": str(row["day"]), "revenue": float(row["price"])}, {"type": "value", "start": str(start), "end": str(end)})
        else:
            return ("No data", "No revenue data in the requested range.", {"type": "text"})

    # Final fallback: return KPIs (safe fallback)
    val = total_revenue(df, start, end)
    s = {"total_revenue": val}
    return ("KPIs summary (fallback)", s, {"type": "value", "start": str(start), "end": str(end)})
