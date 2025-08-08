import logging
import os
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def fetch_case_details(case_type: str, case_number: str, filing_year: str, return_html: bool = False, headless: bool = True):
    """
    Robustly fetches case details from the Delhi High Court website using Playwright.
    Adds random delays, longer timeouts, and logs all steps and errors.

    Args:
        case_type (str): The case type (e.g., "W.P.(C)").
        case_number (str): The case number.
        filing_year (str): The filing year.
        return_html (bool): If True, also return the raw HTML of the result page.
        headless (bool): Whether to run the browser in headless mode.

    Returns:
        dict: Dictionary with case details (petitioner, respondent, filing_date, next_hearing, pdf_url).
        str (optional): Raw HTML if return_html is True.
    """
    url = "https://delhihighcourt.nic.in/app/get-case-type-status"
    details = {}
    html = ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            logging.info(f"Navigating to {url}")
            page.goto(url)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(random.uniform(1000, 4000))

            page.wait_for_selector("select[name='CaseType']", timeout=20000)
            page.wait_for_selector("input[name='CaseNo']", timeout=20000)
            page.wait_for_selector("input[name='CaseYear']", timeout=20000)
            page.wait_for_selector("input[type='submit']", timeout=20000)

            page.wait_for_timeout(random.uniform(1000, 2000))
            page.select_option("select[name='CaseType']", label=case_type)
            page.wait_for_timeout(random.uniform(1000, 2000))
            page.fill("input[name='CaseNo']", case_number)
            page.fill("input[name='CaseYear']", filing_year)
            page.wait_for_timeout(random.uniform(1000, 2000))
            page.click("input[type='submit']")

            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)

            page.wait_for_selector("iframe[name='frmCaseStatus']", timeout=20000)
            frame = page.frame(name="frmCaseStatus")
            if not frame:
                raise Exception("Results iframe not found.")

            frame.wait_for_selector("table", timeout=20000)
            html = frame.content()

            # Extract details
            try:
                petitioner_elem = frame.query_selector("td:has-text('Petitioner')")
                respondent_elem = frame.query_selector("td:has-text('Respondent')")
                petitioner = petitioner_elem.evaluate("el => el.nextElementSibling.innerText") if petitioner_elem else "Not found"
                respondent = respondent_elem.evaluate("el => el.nextElementSibling.innerText") if respondent_elem else "Not found"
            except Exception as e:
                logging.warning(f"Error extracting parties: {e}")
                petitioner = respondent = "Error"

            try:
                filing_elem = frame.query_selector("td:has-text('Filing Date')")
                filing_date = filing_elem.evaluate("el => el.nextElementSibling.innerText") if filing_elem else "Not found"
            except Exception as e:
                logging.warning(f"Error extracting filing date: {e}")
                filing_date = "Error"

            try:
                next_elem = frame.query_selector("td:has-text('Next Date')")
                next_hearing = next_elem.evaluate("el => el.nextElementSibling.innerText") if next_elem else "Not found"
            except Exception as e:
                logging.warning(f"Error extracting next hearing: {e}")
                next_hearing = "Error"

            try:
                pdf_link_elem = frame.query_selector("a[href$='.pdf']")
                pdf_url = pdf_link_elem.get_attribute("href") if pdf_link_elem else None
            except Exception as e:
                logging.warning(f"Error extracting PDF link: {e}")
                pdf_url = None

            details = {
                "petitioner": petitioner,
                "respondent": respondent,
                "filing_date": filing_date,
                "next_hearing": next_hearing,
                "pdf_url": pdf_url
            }
            logging.info(f"Extracted details: {details}")
            if details["petitioner"] == "Error":
                logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
                if not os.path.exists(logs_dir):
                    os.makedirs(logs_dir)
                with open(os.path.join(logs_dir, "last_failed_html.html"), "w", encoding="utf-8") as f:
                    f.write(html)
            browser.close()
            if return_html:
                return details, html
            return details
    except Exception as e:
        logging.error(f"Scraper error: {e}")
        # Ensure logs directory exists and save last html if available
        if html:
            logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            with open(os.path.join(logs_dir, "last_failed_html.html"), "w", encoding="utf-8") as f:
                f.write(html)
        return {
            "petitioner": "Error",
            "respondent": "Error",
            "filing_date": "Error",
            "next_hearing": "Error",
            "pdf_url": None,
            "status": "Scraping failed."
        }