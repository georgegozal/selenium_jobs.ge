"""Write scraped job listings to CSV or JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from jobs.jobs import JobListing

OutputFormat = Literal["csv", "json"]

BASE_COLUMNS = [
    "ID",
    "Job Title",
    "Company",
    "URL",
    "Publish Date",
    "End Date",
    "Days Until Deadline",
]


def csv_columns(*, include_description: bool) -> list[str]:
    cols = list(BASE_COLUMNS)
    if include_description:
        cols.append("Description")
    return cols


def write_listings(
    listings: list[JobListing],
    path: Path,
    fmt: OutputFormat,
    *,
    include_description: bool,
) -> None:
    path = Path(path)
    if fmt == "json":
        _write_json(listings, path)
    else:
        _write_csv(listings, path, include_description=include_description)


def _write_csv(
    listings: list[JobListing],
    path: Path,
    *,
    include_description: bool,
) -> None:
    columns = csv_columns(include_description=include_description)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for job in listings:
            writer.writerow(job.as_csv_row(include_description=include_description))


def _write_json(listings: list[JobListing], path: Path) -> None:
    payload = [job.to_dict() for job in listings]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
