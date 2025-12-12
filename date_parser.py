# date_parser.py

import re
import dateparser
from datetime import datetime, timedelta, timezone


def parse_date_range(text: str, reference: datetime = None):
    """
    Convert natural-language date queries into (start_date, end_date).

    Examples handled:
    - "yesterday"
    - "today"
    - "last 7 days"
    - "between 2024-01-01 and 2024-01-10"
    - "on 2024-01-05"
    - "Dec 2024"
    - "this month", "last month"
    """

    if reference is None:
        reference = datetime.now(timezone.utc)

    txt = text.lower().strip()

    # -------------------------------
    # 1) Between X and Y
    # -------------------------------
    m = re.search(r"between\s+(.+?)\s+and\s+(.+)", txt)
    if m:
        d1 = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        d2 = dateparser.parse(m.group(2), settings={'RELATIVE_BASE': reference})
        if d1 and d2:
            a, b = d1.date(), d2.date()
            return (a, b) if a <= b else (b, a)

    # -------------------------------
    # 2) "on DATE"
    # -------------------------------
    m = re.search(r"\bon\s+([^\n,?.]+)", txt)
    if m:
        d = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        if d:
            return d.date(), d.date()

    # -------------------------------
    # 3) Standalone DATE token (YYYY-MM-DD / DD-MM-YYYY)
    # -------------------------------
    m = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})", txt)
    if m:
        d = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        if d:
            return d.date(), d.date()

    # -------------------------------
    # 4) Relative Dates
    # -------------------------------
    if "yesterday" in txt:
        d = (reference - timedelta(days=1)).date()
        return d, d

    if "today" in txt:
        d = reference.date()
        return d, d

    if "tomorrow" in txt:
        d = (reference + timedelta(days=1)).date()
        return d, d

    # -------------------------------
    # 5) last N days
    # -------------------------------
    m = re.search(r"last\s+(\d{1,3})\s+days?", txt)
    if m:
        n = int(m.group(1))
        end = reference.date()
        start = end - timedelta(days=n - 1)
        return start, end

    # -------------------------------
    # 6) This week / Last week
    # -------------------------------
    if "this week" in txt:
        ref = reference.date()
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
        return start, end

    if "last week" in txt:
        ref = reference.date()
        start = ref - timedelta(days=ref.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end

    # -------------------------------
    # 7) Month ranges
    # -------------------------------
    if "this month" in txt:
        first = reference.replace(day=1).date()
        next_month = (reference.replace(day=28) + timedelta(days=4)).replace(day=1).date()
        last = next_month - timedelta(days=1)
        return first, last

    if "last month" in txt:
        prev_month_last_day = (reference.replace(day=1) - timedelta(days=1)).date()
        first = prev_month_last_day.replace(day=1)
        last = prev_month_last_day
        return first, last

    # -------------------------------
    # 8) "Dec 2025", "January 2024"
    # -------------------------------
    m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}", txt)
    if m:
        d = dateparser.parse(m.group(0))
        if d:
            start = d.replace(day=1).date()
            next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1).date()
            end = next_month - timedelta(days=1)
            return start, end

    # -------------------------------
    # Nothing detected → return None
    # -------------------------------
    return None, None
