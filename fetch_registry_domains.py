#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pdfplumber
import requests

BASE_URL = "https://registry.in/system/files/domain-creates_{date}.pdf"
TIMEZONE = ZoneInfo("Asia/Kolkata")


class FetchError(Exception):
    pass


def download_pdf(date_str, output_path):
    url = BASE_URL.format(date=date_str)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # registry.in answers missing files with HTTP 200 and an HTML error page
    if not response.content.startswith(b"%PDF"):
        content_type = response.headers.get("Content-Type", "unknown")
        raise FetchError(
            f"{url} is not a PDF ({content_type}, {len(response.content)} bytes)"
        )

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"Downloaded: {url}")
    return True


def extract_domains_from_pdf(pdf_path, output_txt):
    domains = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()

            if table:
                for row in table[1:]:
                    if row and row[0]:
                        domain = row[0].strip()

                        if domain and domain != 'Domain User Form':
                            domains.append(domain)

    if not domains:
        raise FetchError(f"No domains found in {pdf_path}")

    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(domains))

    print(f"Extracted {len(domains)} domains to {output_txt}")
    return True


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return datetime.strptime(date_str, "%d-%m-%Y")


def output_dir_for(date_obj):
    return Path(date_obj.strftime("%Y")) / date_obj.strftime("%m")


def has_data(date_obj):
    # Files before late April 2026 use the legacy DD-MM-YYYY naming
    output_dir = output_dir_for(date_obj)
    return any(
        (output_dir / f"domains_{date_obj.strftime(fmt)}.txt").exists()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y")
    )


def process_date(date_obj):
    """Fetch one date. Returns None on success, or the failure reason."""
    date_formatted = date_obj.strftime("%Y-%m-%d")

    output_dir = output_dir_for(date_obj)
    txt_path = output_dir / f"domains_{date_formatted}.txt"

    # The PDF never touches the repo, so a failed run can't leave it behind
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / f"domain-creates_{date_formatted}.pdf"
        try:
            download_pdf(date_formatted, pdf_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            extract_domains_from_pdf(pdf_path, txt_path)
            print(f"Success! Files saved in {output_dir}/")
            return None
        except requests.exceptions.RequestException as e:
            reason = f"Error downloading PDF: {e}"
        except Exception as e:
            reason = f"Error: {e}"

    print(reason)
    return reason


def catch_up_dates(days):
    yesterday = datetime.now(TIMEZONE).replace(tzinfo=None) - timedelta(days=1)
    dates = [yesterday - timedelta(days=i) for i in range(days - 1, -1, -1)]
    return [d for d in dates if not has_data(d)]


def write_github_output(succeeded, failures):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return

    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"succeeded={' '.join(succeeded)}\n")
        f.write(f"failed={' '.join(failures)}\n")
        f.write("reasons<<EOF_REASONS\n")
        for date_str, reason in failures.items():
            f.write(f"{date_str}: {reason}\n")
        f.write("EOF_REASONS\n")


def main():
    parser = argparse.ArgumentParser(description="Fetch .IN newly registered domains")
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD or DD-MM-YYYY (default: today)")
    parser.add_argument("--catch-up", type=int, metavar="N",
                        help="fetch any missing dates from the N days ending yesterday (IST)")
    args = parser.parse_args()

    if args.catch_up:
        dates = catch_up_dates(args.catch_up)
        if not dates:
            print(f"No missing dates in the last {args.catch_up} days")
    elif args.date:
        dates = [parse_date(args.date)]
    else:
        dates = [datetime.now(TIMEZONE).replace(tzinfo=None)]

    succeeded = []
    failures = {}
    for date_obj in dates:
        date_str = date_obj.strftime("%Y-%m-%d")
        print(f"Processing domains for date: {date_str}")
        reason = process_date(date_obj)
        if reason:
            failures[date_str] = reason
        else:
            succeeded.append(date_str)

    write_github_output(succeeded, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
