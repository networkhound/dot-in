#!/usr/bin/env python3

import pdfplumber
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

BASE_URL = "https://registry.in/system/files/domain-creates_{date}.pdf"

def download_pdf(date_str, output_path):
    url = BASE_URL.format(date=date_str)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

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

    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(domains))

    print(f"Extracted {len(domains)} domains to {output_txt}")
    return True

def process_date(date_str=None):
    if date_str:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    else:
        date_obj = datetime.now()

    date_formatted = date_obj.strftime("%d-%m-%Y")
    year = date_obj.strftime("%Y")
    month = date_obj.strftime("%m")

    output_dir = Path(year) / month
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"domain-creates_{date_formatted}.pdf"
    txt_filename = f"domains_{date_formatted}.txt"

    pdf_path = output_dir / pdf_filename
    txt_path = output_dir / txt_filename

    try:
        download_pdf(date_formatted, pdf_path)
        extract_domains_from_pdf(pdf_path, txt_path)
        pdf_path.unlink()
        print(f"Success! Files saved in {output_dir}/")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"Error downloading PDF: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    process_date(date_arg)
