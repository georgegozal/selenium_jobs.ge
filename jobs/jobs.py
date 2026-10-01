from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Optional

from prettytable import PrettyTable

from jobs.export import BASE_COLUMNS, OutputFormat, write_listings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from jobs.dates import days_until_deadline

logger = logging.getLogger(__name__)

BASE_URL = "https://jobs.ge/ge/ads/"

_CHROME_NAMES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "brave-browser-stable",
)
_CHROME_PATHS = (
    Path("/usr/bin/google-chrome-stable"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/brave-browser"),
    Path("/opt/brave.com/brave/brave-browser"),
    Path("/snap/bin/chromium"),
    Path("/opt/google/chrome/google-chrome"),
)

CHROME_NOT_FOUND_MSG = (
    "No Chromium-based browser was found (Chrome, Chromium, Brave, …).\n"
    "Point Selenium at your browser binary:\n"
    "  export CHROME_BIN=/usr/bin/brave-browser    # Brave on Linux\n"
    "  python run.py --chrome-binary /usr/bin/brave-browser\n"
    "See README.md for more options."
)

@dataclass(frozen=True)
class JobListing:
    id: int
    title: str
    company: str
    url: str
    published: str
    end_date: str
    days_until_deadline: Optional[int]
    description: Optional[str] = None

    def as_csv_row(self, *, include_description: bool = False) -> list:
        days = (
            ""
            if self.days_until_deadline is None
            else self.days_until_deadline
        )
        row = [
            self.id,
            self.title,
            self.company,
            self.url,
            self.published,
            self.end_date,
            days,
        ]
        if include_description:
            row.append(self.description or "")
        return row

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "published": self.published,
            "end_date": self.end_date,
            "days_until_deadline": self.days_until_deadline,
            "description": self.description,
        }


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _block_text(element) -> str:
    raw = element.get_attribute("textContent") or element.text or ""
    lines = [line.strip() for line in raw.splitlines()]
    return "\n".join(line for line in lines if line)


def title_matches(title: str, include: Iterable[str], exclude: Iterable[str]) -> bool:
    title_lower = title.lower()
    includes = [k.strip() for k in include if k.strip()]
    excludes = [k.strip() for k in exclude if k.strip()]
    if includes and not any(k.lower() in title_lower for k in includes):
        return False
    if excludes and any(k.lower() in title_lower for k in excludes):
        return False
    return True


class Jobs:
    """jobs.ge scraper built on Selenium (composition, not Chrome subclass)."""

    def __init__(
        self,
        *,
        headless: bool = True,
        chrome_binary: Optional[str | Path] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self._base_url = (base_url or BASE_URL).rstrip("/") + "/"
        self._driver = _create_driver(
            headless=headless,
            chrome_binary=chrome_binary,
        )
        # Use explicit waits only; implicit wait makes per-row find_elements very slow.
        self._driver.implicitly_wait(0)
        self._wait = WebDriverWait(self._driver, 20)
        logger.info("jobs.ge bot ready (headless=%s)", headless)

    def __enter__(self) -> Jobs:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.quit()

    def quit(self) -> None:
        try:
            self._driver.quit()
        except Exception:
            logger.debug("Browser already closed", exc_info=True)

    def land_first_page(self) -> None:
        self._driver.get(self._base_url)
        self._wait_for_job_table()

    def get_categories(self) -> dict[str, str]:
        select = self._category_select()
        categories: dict[str, str] = {}
        for option in select.options:
            value = (option.get_attribute("value") or "").strip()
            if not value:
                continue
            label = _normalize(option.text)
            categories[value] = label
        return categories

    def change_category(self, category_id: Optional[str] = None) -> str:
        categories = self.get_categories()
        if not categories:
            raise RuntimeError("No categories found on the page")

        chosen = category_id
        if chosen is None:
            print("id  category")
            for key, label in categories.items():
                print(f"{key:>3}  {label}")
            while True:
                chosen = input("Choose category by id: ").strip()
                if chosen in categories:
                    break
                chosen = input("Invalid id. Choose category by id: ").strip()
        elif chosen not in categories:
            raise ValueError(
                f"Unknown category id {chosen!r}. "
                f"Valid ids: {', '.join(sorted(categories, key=int))}"
            )

        label = categories[chosen]
        logger.info("Category selected: %s (%s)", label, chosen)
        print(f"\nარჩეულია {label}\n")

        select_el = self._driver.find_element(By.CSS_SELECTOR, "select[name=cid]")
        Select(select_el).select_by_value(chosen)
        self._wait_for_job_table()
        logger.info("Category page loaded")
        return chosen

    def collect_listings(
        self,
        include: Iterable[str],
        exclude: Iterable[str],
        *,
        fetch_details: bool = False,
    ) -> list[JobListing]:
        listings: list[JobListing] = []
        next_id = 1
        rows = list(self._job_rows())
        logger.info("Scanning %d job rows on this page…", len(rows))
        print(f"Scanning {len(rows)} job rows…")
        for row in rows:
            try:
                title_link = row.find_element(
                    By.CSS_SELECTOR,
                    "td:nth-child(2) a[href*='view=jobs']",
                )
            except Exception:
                continue

            title = _normalize(title_link.text)
            if not title or not title_matches(title, include, exclude):
                continue

            url = title_link.get_attribute("href") or ""
            company = _extract_company(row)
            published = _normalize(
                row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
            )
            end_date = _normalize(
                row.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
            )

            listings.append(
                JobListing(
                    id=next_id,
                    title=title,
                    company=company,
                    url=url,
                    published=published,
                    end_date=end_date,
                    days_until_deadline=days_until_deadline(end_date),
                )
            )
            next_id += 1

        logger.info("Matched %d jobs after keyword filter", len(listings))
        print(f"Matched {len(listings)} jobs after keyword filter")

        if fetch_details and listings:
            listings = self._attach_descriptions(listings)

        return listings

    def report(
        self,
        include: Iterable[str],
        exclude: Iterable[str],
        *,
        output: Path,
        output_format: OutputFormat = "csv",
        fetch_details: bool = False,
    ) -> list[JobListing]:
        print("Collecting listings…")
        listings = self.collect_listings(
            include,
            exclude,
            fetch_details=fetch_details,
        )

        table = PrettyTable(field_names=BASE_COLUMNS)
        table.add_rows([job.as_csv_row() for job in listings])
        print(table)
        if fetch_details:
            print("(Full descriptions are in the output file, not in the table above.)")

        output = Path(output)
        logger.info(
            "Writing %s (%d rows, format=%s, details=%s)",
            output,
            len(listings),
            output_format,
            fetch_details,
        )
        write_listings(
            listings,
            output,
            output_format,
            include_description=fetch_details,
        )

        print(f"Saved {len(listings)} jobs to {output.resolve()} ({output_format})")
        return listings

    def _attach_descriptions(self, listings: list[JobListing]) -> list[JobListing]:
        total = len(listings)
        enriched: list[JobListing] = []
        for index, job in enumerate(listings, start=1):
            print(f"Fetching details {index}/{total}: {job.title}")
            description = self._fetch_job_description(job.url)
            enriched.append(replace(job, description=description))
        return enriched

    def _fetch_job_description(self, url: str) -> str:
        if not url.startswith("http"):
            url = f"https://jobs.ge{url}"
        self._driver.get(url)
        cell = self._wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#job table.dtable tr:last-child td")
            )
        )
        return _block_text(cell)

    def _category_select(self) -> Select:
        el = self._wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "select[name=cid]")
            )
        )
        return Select(el)

    def _wait_for_job_table(self) -> None:
        self._wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#job_list_table tr td a[href*='view=jobs']")
            )
        )

    def _job_rows(self):
        links = self._driver.find_elements(
            By.CSS_SELECTOR,
            "#job_list_table td:nth-child(2) a[href*='view=jobs']",
        )
        seen: set[str] = set()
        for link in links:
            row = link.find_element(By.XPATH, "./ancestor::tr[1]")
            row_id = row.id
            if row_id in seen:
                continue
            seen.add(row_id)
            yield row


def _extract_company(row) -> str:
    try:
        return _normalize(
            row.find_element(
                By.CSS_SELECTOR,
                "td:nth-child(4) a",
            ).text
        )
    except Exception:
        return _normalize(row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text)


def resolve_chrome_binary(explicit: Optional[str | Path] = None) -> str:
    """Return path to Chrome/Chromium, or raise FileNotFoundError with hints."""
    if explicit is not None:
        path = Path(explicit).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise FileNotFoundError(f"Chrome binary not found: {path}")

    from_env = os.environ.get("CHROME_BIN")
    if from_env:
        path = Path(from_env).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise FileNotFoundError(f"CHROME_BIN points to missing file: {path}")

    for name in _CHROME_NAMES:
        found = shutil.which(name)
        if found:
            return found

    for path in _CHROME_PATHS:
        if path.is_file():
            return str(path)

    raise FileNotFoundError(CHROME_NOT_FOUND_MSG)


def _create_driver(
    *,
    headless: bool,
    chrome_binary: Optional[str | Path] = None,
) -> WebDriver:
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options = Options()
    options.binary_location = resolve_chrome_binary(chrome_binary)
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
