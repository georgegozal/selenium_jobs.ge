# jobs.ge Selenium scraper

Small practice project: use Selenium to open [jobs.ge](https://jobs.ge/ge/ads/), pick a category, filter job titles by keywords, print a table, and save `jobs_list.csv`.

## Requirements

- Python 3.9+
- A **Chromium-based browser** (Google Chrome, Chromium, **Brave**, etc.) — not just chromedriver
- Chromedriver is downloaded automatically via `webdriver-manager` and works with Brave when you set the browser path

### Install Chrome / Chromium (Linux)

```bash
# Debian, MX Linux, Ubuntu — pick one package name that exists on your system
sudo apt update
sudo apt install chromium
# or: sudo apt install google-chrome-stable   # if you use Google’s repo
```

Check where the binary is:

```bash
which chromium || which chromium-browser || which google-chrome-stable
```

If it is not on your `PATH`:

```bash
export CHROME_BIN=/usr/bin/chromium
python run.py
```

Or pass it once:

```bash
python run.py --chrome-binary /usr/bin/chromium
```

**Brave** (typical on Linux):

```bash
export CHROME_BIN=/usr/bin/brave-browser
python run.py --no-headless
```

Auto-discovery also checks for `brave-browser` on your `PATH` if you install/update this repo.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# edit .env with your real paths and keywords
```

## Configuration

- **`env.example`** — committed template with placeholder values
- **`.env`** — your local config (listed in `.gitignore`, never committed)

Copy the template once: `cp env.example .env`. All values are optional; CLI flags override `.env`.

| Variable | Purpose |
|----------|---------|
| `CHROME_BIN` | Path to Brave / Chrome / Chromium |
| `JOBS_INCLUDE` | Comma-separated title keywords (OR) |
| `JOBS_EXCLUDE` | Comma-separated words to skip |
| `JOBS_CATEGORY_ID` | Category id; empty = interactive prompt |
| `JOBS_OUTPUT_FORMAT` | `csv` or `json` → writes `jobs_list_<timestamp>.<ext>` |
| `JOBS_FETCH_DETAILS` | `true` to open each job and scrape description |
| `JOBS_HEADLESS` | `true` / `false` (use `false` to see the browser) |
| `JOBS_VERBOSE` | `true` for debug logs |
| `JOBS_BASE_URL` | Optional listing URL override |

Example `.env` (your file, not committed):

```env
CHROME_BIN=/usr/bin/brave-browser
JOBS_INCLUDE=Python,Back,odoo
JOBS_EXCLUDE=Java,PHP
JOBS_CATEGORY_ID=6
JOBS_HEADLESS=false
```

Then run:

```bash
python run.py
```

## Usage

Interactive category selection (default keywords):

```bash
python run.py
```

IT category without prompts, custom keywords:

```bash
python run.py --category-id 6 -i Python -i scraping -e Java -e PHP
```

List category ids:

```bash
python run.py --list-categories
```

Watch the browser while debugging:

```bash
python run.py --no-headless --category-id 6 -v
```

### Options

| Flag | Description |
|------|-------------|
| `-i`, `--include` | Title must match at least one keyword (OR). Repeat or use commas. |
| `-e`, `--exclude` | Skip if any keyword appears in the title. |
| `-c`, `--category-id` | Category `cid` from the site form. |
| `--list-categories` | Print ids and labels, then exit. |
| `-o`, `--output` | Override auto path (`jobs_list_YYYY-MM-DD_HH-MM-SS.csv/json`). |
| `-f`, `--format` | `csv` or `json` (env: `JOBS_OUTPUT_FORMAT`). |
| `-d`, `--fetch-details` | Visit each job URL and save the description. |
| `--no-headless` | Run Chrome with a visible window. |
| `-v`, `--verbose` | Debug logging. |

Export includes **Days Until Deadline** (Georgian dates, e.g. `31 ოქტომბერი`). With `--fetch-details`, descriptions are added (CSV column or JSON field).

```bash
python run.py -f json -d
```

## Project layout

- `run.py` — CLI
- `jobs/jobs.py` — Selenium scraper (`Jobs` owns a `WebDriver`)
- `jobs/dates.py` — Georgian date parsing for deadline countdown
- `jobs/config.py` — `.env` loading and setting resolution
- `jobs/export.py` — CSV / JSON writers

## Notes

- Category changes use `Select` on `select[name=cid]`; the site submits the form on change.
- Job rows are detected by links containing `view=jobs`, not by skipping a fixed number of table rows.
