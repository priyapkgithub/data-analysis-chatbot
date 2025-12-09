# date_parser.py
from datetime import datetime, timedelta, timezone
import re
import dateparser

def parse_date_range(text: str, reference: datetime = None):
    """
    Parse natural-language date range requests into (start_date, end_date).
    """
    if reference is None:
        reference = datetime.now(timezone.utc)   # ← FIXED

    text_low = text.lower().strip()

    # explicit between X and Y
    m = re.search(r'between\s+(.+?)\s+and\s+(.+)', text_low)
    if m:
        a = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        b = dateparser.parse(m.group(2), settings={'RELATIVE_BASE': reference})
        if a and b:
            start = a.date()
            end = b.date()
            if start > end:
                start, end = end, start
            return start, end

    # single "on" date
    m = re.search(r'\bon\s+([^\n,?.]+)', text_low)
    if m:
        d = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        if d:
            return d.date(), d.date()

    # standalone date token
    m = re.search(r'(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})', text_low)
    if m:
        d = dateparser.parse(m.group(1), settings={'RELATIVE_BASE': reference})
        if d:
            return d.date(), d.date()

    # yesterday / today / tomorrow
    if 'yesterday' in text_low:
        dt = (reference - timedelta(days=1)).date()
        return dt, dt

    if 'today' in text_low:
        dt = reference.date()
        return dt, dt

    if 'tomorrow' in text_low:
        dt = (reference + timedelta(days=1)).date()
        return dt, dt

    # last N days
    m = re.search(r'last\s+(\d{1,3})\s+days?', text_low)
    if m:
        n = int(m.group(1))
        end = reference.date()
        start = (reference - timedelta(days=n-1)).date()
        return start, end

    # last/this week
    if 'last week' in text_low:
        ref = reference.date()
        start = ref - timedelta(days=ref.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end

    if 'this week' in text_low:
        ref = reference.date()
        start = ref - timedelta(days=ref.weekday())
        end = start + timedelta(days=6)
        return start, end

    # last/this month
    if 'last month' in text_low:
        first = (reference.replace(day=1) - timedelta(days=1))
        start = first.replace(day=1).date()
        end = first.date()
        return start, end

    if 'this month' in text_low:
        first = reference.replace(day=1).date()
        next_month = (reference.replace(day=28) + timedelta(days=4)).replace(day=1).date()
        last_day = next_month - timedelta(days=1)
        return first, last_day

    # month-year phrases
    m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}', text_low)
    if m:
        d = dateparser.parse(m.group(0))
        if d:
            start = d.replace(day=1).date()
            next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1).date()
            end = next_month - timedelta(days=1)
            return start, end

    return None, None
