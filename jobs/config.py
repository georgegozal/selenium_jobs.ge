"""Load scraper settings from environment and optional `.env` file."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from jobs.export import OutputFormat

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_BASENAME = "jobs_list"

DEFAULT_INCLUDE = ["Python", "Back", "ბექი", "odoo", "scraping"]
DEFAULT_EXCLUDE = ["Java", "PHP"]

# Env var names (documented in `env.example`; live values go in `.env`)
ENV_CHROME_BIN = "CHROME_BIN"
ENV_INCLUDE = "JOBS_INCLUDE"
ENV_EXCLUDE = "JOBS_EXCLUDE"
ENV_CATEGORY_ID = "JOBS_CATEGORY_ID"
ENV_HEADLESS = "JOBS_HEADLESS"
ENV_VERBOSE = "JOBS_VERBOSE"
ENV_BASE_URL = "JOBS_BASE_URL"
ENV_OUTPUT_FORMAT = "JOBS_OUTPUT_FORMAT"
ENV_FETCH_DETAILS = "JOBS_FETCH_DETAILS"
DEFAULT_OUTPUT_FORMAT: OutputFormat = "csv"


def load_dotenv_file() -> None:
    """Load `.env` from project root if present."""
    load_dotenv(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def split_keyword_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    if not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def resolve_include(cli_values: list[str]) -> list[str]:
    if cli_values:
        return _split_cli_keywords(cli_values)
    from_env = split_keyword_env(ENV_INCLUDE)
    return from_env if from_env else list(DEFAULT_INCLUDE)


def resolve_exclude(cli_values: list[str]) -> list[str]:
    if cli_values:
        return _split_cli_keywords(cli_values)
    from_env = split_keyword_env(ENV_EXCLUDE)
    return from_env if from_env else list(DEFAULT_EXCLUDE)


def resolve_category_id(cli_value: Optional[str]) -> Optional[str]:
    if cli_value is not None:
        value = cli_value.strip()
        return value or None
    from_env = os.getenv(ENV_CATEGORY_ID)
    if from_env is None:
        return None
    value = from_env.strip()
    return value or None


def resolve_output_format(cli_value: Optional[str]) -> OutputFormat:
    if cli_value is not None:
        return _parse_output_format(cli_value)
    from_env = os.getenv(ENV_OUTPUT_FORMAT)
    if from_env and from_env.strip():
        return _parse_output_format(from_env)
    return DEFAULT_OUTPUT_FORMAT


def build_timestamped_output(
    output_format: OutputFormat,
    *,
    directory: Path | None = None,
) -> Path:
    folder = directory or PROJECT_ROOT
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extension = "json" if output_format == "json" else "csv"
    return folder / f"{OUTPUT_BASENAME}_{stamp}.{extension}"


def resolve_output(
    cli_value: Optional[Path],
    output_format: OutputFormat,
) -> Path:
    if cli_value is not None:
        return cli_value
    return build_timestamped_output(output_format)


def resolve_fetch_details(cli_flag: bool) -> bool:
    if cli_flag:
        return True
    return env_bool(ENV_FETCH_DETAILS, default=False)


def _parse_output_format(raw: str) -> OutputFormat:
    value = raw.strip().lower()
    if value in ("csv", "json"):
        return value  # type: ignore[return-value]
    raise ValueError(f"Invalid output format {raw!r}; use csv or json")


def resolve_chrome_binary(cli_value: Optional[Path]) -> Optional[Path]:
    if cli_value is not None:
        return cli_value
    from_env = os.getenv(ENV_CHROME_BIN)
    if from_env and from_env.strip():
        return Path(from_env.strip())
    return None


def resolve_headless(cli_no_headless: bool) -> bool:
    if cli_no_headless:
        return False
    return env_bool(ENV_HEADLESS, default=True)


def resolve_verbose(cli_verbose: bool) -> bool:
    if cli_verbose:
        return True
    return env_bool(ENV_VERBOSE, default=False)


def resolve_base_url() -> Optional[str]:
    raw = os.getenv(ENV_BASE_URL)
    if raw and raw.strip():
        return raw.strip()
    return None


def _split_cli_keywords(raw: list[str]) -> list[str]:
    keywords: list[str] = []
    for item in raw:
        for part in item.split(","):
            word = part.strip()
            if word:
                keywords.append(word)
    return keywords
