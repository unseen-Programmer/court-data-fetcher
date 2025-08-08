import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from utils.google_sheet import read_case_ids, write_results
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Load environment variables
load_dotenv()

# Logging setup
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "main.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

INPUT_FILE = DATA_DIR / "case_ids.txt"
OUTPUT_FILE = DATA_DIR / "output.json"

RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", 2))
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", 3))

async def fetch_case_details(playwright, case_id: str) -> Dict:
    """
    Scrape court details for a given case_id using Playwright.
    Returns a dict with extracted fields.
    """
    url = "https://delhihighcourt.nic.in/case.asp"
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    details = {"case_id": case_id, "status": "error"}
    try:
        await page.goto(url)
        await page.wait_for_selector("select[name='CaseType']", timeout=10000)
        await page.wait_for_selector("input[name='CaseNo']", timeout=10000)
        await page.wait_for_selector("input[name='CaseYear']", timeout=10000)
        # Assume case_id format: <CaseType>,<CaseNumber>,<FilingYear>
        parts = [x.strip() for x in case_id.split(",")]
        if len(parts) != 3:
            details["status"] = "invalid_format"
            return details
        case_type, case_number, filing_year = parts
        await page.select_option("select[name='CaseType']", label=case_type)
        await page.fill("input[name='CaseNo']", case_number)
        await page.fill("input[name='CaseYear']", filing_year)
        await page.click("input[type='submit']")
        await page.wait_for_selector("iframe[name='frmCaseStatus']", timeout=20000)
        frame = page.frame(name="frmCaseStatus")
        if not frame:
            details["status"] = "iframe_not_found"
            return details
        await frame.wait_for_selector("table", timeout=20000)
        # Extract details
        def get_text(sel):
            elem = frame.query_selector(sel)
            return asyncio.run(elem.inner_text()) if elem else ""
        details["petitioner"] = await (await frame.query_selector("td:has-text('Petitioner')")).evaluate("el => el.nextElementSibling.innerText") if await frame.query_selector("td:has-text('Petitioner')") else ""
        details["respondent"] = await (await frame.query_selector("td:has-text('Respondent')")).evaluate("el => el.nextElementSibling.innerText") if await frame.query_selector("td:has-text('Respondent')") else ""
        details["filing_date"] = await (await frame.query_selector("td:has-text('Filing Date')")).evaluate("el => el.nextElementSibling.innerText") if await frame.query_selector("td:has-text('Filing Date')") else ""
        details["next_hearing"] = await (await frame.query_selector("td:has-text('Next Date')")).evaluate("el => el.nextElementSibling.innerText") if await frame.query_selector("td:has-text('Next Date')") else ""
        pdf_elem = await frame.query_selector("a[href$='.pdf']")
        details["pdf_url"] = await pdf_elem.get_attribute("href") if pdf_elem else ""
        details["status"] = "success"
    except PlaywrightTimeoutError as e:
        details["status"] = f"timeout: {e}"
        logging.warning(f"Timeout for {case_id}: {e}")
    except Exception as e:
        details["status"] = f"error: {e}"
        logging.error(f"Error for {case_id}: {e}")
    finally:
        await browser.close()
    return details

async def main():
    # Read case IDs from Google Sheet if possible, else from file
    try:
        case_ids = read_case_ids()
        logging.info("Loaded case IDs from Google Sheet.")
    except Exception:
        if INPUT_FILE.exists():
            with open(INPUT_FILE, "r", encoding="utf-8") as f:
                case_ids = [line.strip() for line in f if line.strip()]
            logging.info("Loaded case IDs from file.")
        else:
            print("No input source found.")
            return
    results = []
    async with async_playwright() as playwright:
        for case_id in case_ids:
            for attempt in range(RETRY_LIMIT):
                result = await fetch_case_details(playwright, case_id)
                if result.get("status") == "success":
                    break
                await asyncio.sleep(1)
            results.append(result)
            print(result)
            logging.info(f"Fetched: {result}")
            await asyncio.sleep(RATE_LIMIT_SECONDS)
    # Save to file
    import json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    # Write to Google Sheet if possible
    try:
        write_results(results)
        logging.info("Results written to Google Sheet.")
    except Exception as e:
        logging.error(f"Failed to write to Google Sheet: {e}")

if __name__ == "__main__":
    asyncio.run(main())
