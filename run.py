#!/usr/bin/env python3
"""CLI entry point for the jobs.ge Selenium scraper."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from jobs.config import (
    DEFAULT_EXCLUDE,
    DEFAULT_INCLUDE,
    DEFAULT_OUTPUT_FORMAT,
    load_dotenv_file,
    resolve_base_url,
    resolve_category_id,
    resolve_chrome_binary,
    resolve_exclude,
    resolve_fetch_details,
    resolve_headless,
    resolve_include,
    resolve_output,
    resolve_output_format,
    resolve_verbose,
)
from jobs.jobs import Jobs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filter jobs.ge listings with Selenium and export to CSV or JSON.",
        epilog="Settings load from `.env` (copy from `env.example`). "
        "Command-line flags override `.env` values.",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="append",
        default=[],
        metavar="WORD",
        help="Title must contain this keyword (repeat or comma-separate). "
        f"Default: env JOBS_INCLUDE or {', '.join(DEFAULT_INCLUDE)}",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        default=[],
        metavar="WORD",
        help="Skip titles containing this keyword (repeat or comma-separate). "
        f"Default: env JOBS_EXCLUDE or {', '.join(DEFAULT_EXCLUDE)}",
    )
    parser.add_argument(
        "-c",
        "--category-id",
        metavar="ID",
        default=None,
        help="Category id from select[name=cid]; skip interactive prompt "
        "(env: JOBS_CATEGORY_ID).",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="Print category ids and exit (opens browser briefly).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Override output path (default: jobs_list_<timestamp>.csv or .json).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("csv", "json"),
        default=None,
        help=f"Output format (env: JOBS_OUTPUT_FORMAT, default: {DEFAULT_OUTPUT_FORMAT}).",
    )
    parser.add_argument(
        "-d",
        "--fetch-details",
        action="store_true",
        help="Open each job page and scrape the description (env: JOBS_FETCH_DETAILS).",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show the browser window (overrides JOBS_HEADLESS).",
    )
    parser.add_argument(
        "--chrome-binary",
        type=Path,
        default=None,
        help="Browser binary path (env: CHROME_BIN).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging (env: JOBS_VERBOSE).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv_file()
    args = build_parser().parse_args(argv)

    include = resolve_include(args.include)
    exclude = resolve_exclude(args.exclude)
    category_id = resolve_category_id(args.category_id)
    try:
        output_format = resolve_output_format(args.format)
    except ValueError as err:
        logging.error("%s", err)
        return 2
    output = resolve_output(args.output, output_format)
    fetch_details = resolve_fetch_details(args.fetch_details)
    chrome_binary = resolve_chrome_binary(args.chrome_binary)
    headless = resolve_headless(args.no_headless)
    verbose = resolve_verbose(args.verbose)
    base_url = resolve_base_url()

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        with Jobs(
            headless=headless,
            chrome_binary=chrome_binary,
            base_url=base_url,
        ) as bot:
            bot.land_first_page()

            if args.list_categories:
                for cid, label in bot.get_categories().items():
                    print(f"{cid:>3}  {label}")
                return 0

            bot.change_category(category_id)
            bot.report(
                include,
                exclude,
                output=output,
                output_format=output_format,
                fetch_details=fetch_details,
            )
    except KeyboardInterrupt:
        print("\nStopped (Ctrl+C). If you quit during “Scanning…”, it had not finished yet.")
        logging.warning("Interrupted")
        return 130
    except FileNotFoundError as err:
        logging.error("%s", err)
        return 1
    except Exception:
        logging.exception("Scraper failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
