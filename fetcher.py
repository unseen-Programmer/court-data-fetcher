"""
Court Data Batch Fetcher using Playwright

Reads a list of case numbers from a text file, fetches court data for each,
and saves the results to output.json or output.csv.

Usage:
    python fetcher.py case_numbers.txt
"""

import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict
from scraper import fetch_case_details

# --- Configuration ---
OUTPUT_JSON = "output.json"
OUTPUT_CSV = "output.csv"
LOG_FILE = "fetcher.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def read_case_numbers(filename: str) -> List[Dict]:
    """
    Reads case numbers from a text file.
    Each line should be: <CaseType>,<CaseNumber>,<FilingYear>
    Returns a list of dicts.
    """
    cases = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            parts = [x.strip() for x in line.strip().split(",")]
            if len(parts) == 3:
                cases.append({
                    "case_type": parts[0],
                    "case_number": parts[1],
                    "filing_year": parts[2]
                })
    return cases

def save_to_json(data: List[Dict], filename: str):
    """Saves the list of dicts to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_to_csv(data: List[Dict], filename: str):
    """Saves the list of dicts to a CSV file."""
    if not data:
        return
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetcher.py case_numbers.txt")
        sys.exit(1)
    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Input file {input_file} not found.")
        sys.exit(1)
    cases = read_case_numbers(input_file)
    results = []
    for case in cases:
        logging.info(f"Fetching: {case['case_type']}-{case['case_number']}-{case['filing_year']}")
        result = fetch_case_details(
            case["case_type"],
            case["case_number"],
            case["filing_year"]
        )
        results.append(result)
    save_to_json(results, OUTPUT_JSON)
    save_to_csv(results, OUTPUT_CSV)
    print(f"Done. Results saved to {OUTPUT_JSON} and {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
