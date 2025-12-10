# date_parser.py
import re
from datetime import datetime, timedelta, timezone
import dateparser

def parse_date_range(text: str, reference=None):
    if reference is None:
        reference = datetime.now(timezone.utc)

    t = text.lower()

    # Between X and Y
    m = re.search(r"between\s+(.+?)\s+and\s+(.+)", t)
    if m:
        a = dateparser.parse(m.group(1))
        b = dateparser.parse(m.group(2))
        if a and b:
            a, b = a.date(), b.date()
            return (a, b) if a <= b else (b, a)

    # On a single date
    m = re.search(r"\bon\s+([^\n,?.]+)", t)
    if m:
        d = dateparser.parse(m.group(1))
        if d:
            return d.date(), d.date()

    # YYYY-MM-DD
    m = re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", t)
    if m:
        d = dateparser.parse(m.group(0))
        return d.date(), d.date()

    # Yesterday
    if "yesterday" in t:
        d = (reference - timedelta(days=1)).date()
        return d, d

    # Today
    if "today" in t:
        d = reference.date()
        return d, d

    # Last 7 days
    m = re.search(r"last\s+(\d+)\s+days", t)
    if m:
        n = int(m.group(1))
        end = reference.date()
        start = end - timedelta(days=n - 1)
        return start, end

    return None, None
