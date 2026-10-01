"""Parse Georgian job-site dates like '31 ოქტომბერი'."""

from __future__ import annotations

from datetime import date
import re
from typing import Optional

_GEORGIAN_MONTHS = {
    "იანვარი": 1,
    "თებერვალი": 2,
    "მარტი": 3,
    "აპრილი": 4,
    "მაისი": 5,
    "ივნისი": 6,
    "ივლისი": 7,
    "აგვისტო": 8,
    "სექტემბერი": 9,
    "ოქტომბერი": 10,
    "ნოემბერი": 11,
    "დეკემბერი": 12,
}

_DATE_RE = re.compile(
    r"(\d{1,2})\s+(" + "|".join(re.escape(m) for m in _GEORGIAN_MONTHS) + r")",
    re.UNICODE,
)


def parse_georgian_date(text: str, *, reference: Optional[date] = None) -> Optional[date]:
    reference = reference or date.today()
    match = _DATE_RE.search(text.strip())
    if not match:
        return None
    day = int(match.group(1))
    month = _GEORGIAN_MONTHS[match.group(2)]
    year = reference.year
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    if parsed < reference:
        try:
            parsed = date(year + 1, month, day)
        except ValueError:
            return None
    return parsed


def days_until_deadline(end_date_text: str, *, reference: Optional[date] = None) -> Optional[int]:
    reference = reference or date.today()
    parsed = parse_georgian_date(end_date_text, reference=reference)
    if parsed is None:
        return None
    return (parsed - reference).days
