import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def fetch_case_details(case_type: str, case_number: str, filing_year: str):
    url = "https://delhihighcourt.nic.in/case.asp"
    details = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True in production
        page = browser.new_page()
        try:
            page.goto(url)
            # 2. Wait for the case search form to load
            page.wait_for_selector("select[name='CaseType']", timeout=10000)
            page.wait_for_selector("input[name='CaseNo']", timeout=10000)
            page.wait_for_selector("input[name='CaseYear']", timeout=10000)
            page.wait_for_selector("input[type='submit']", timeout=10000)

            # 3. Select the given case type by label
            page.select_option("select[name='CaseType']", label=case_type)

            # 4. Enter the given case number and filing year
            page.fill("input[name='CaseNo']", case_number)
            page.fill("input[name='CaseYear']", filing_year)

            # 5. Click the submit button to search
            page.click("input[type='submit']")

            # 6. Wait for the results iframe named "frmCaseStatus" to appear
            page.wait_for_selector("iframe[name='frmCaseStatus']", timeout=20000)

            # 7. Switch context to that iframe
            frame = page.frame(name="frmCaseStatus")
            if not frame:
                raise Exception("Results iframe not found.")

            # 8. Wait for the case details table to load inside the iframe
            frame.wait_for_selector("table", timeout=20000)

            # 9. Extract details
            # Petitioner and Respondent names
            petitioner = None
            respondent = None
            try:
                petitioner_elem = frame.query_selector("td:has-text('Petitioner')")
                respondent_elem = frame.query_selector("td:has-text('Respondent')")
                petitioner = petitioner_elem.evaluate("el => el.nextElementSibling.innerText") if petitioner_elem else "Not found"
                respondent = respondent_elem.evaluate("el => el.nextElementSibling.innerText") if respondent_elem else "Not found"
            except Exception:
                petitioner = "Not found"
                respondent = "Not found"

            # Filing Date
            try:
                filing_elem = frame.query_selector("td:has-text('Filing Date')")
                filing_date = filing_elem.evaluate("el => el.nextElementSibling.innerText") if filing_elem else "Not found"
            except Exception:
                filing_date = "Not found"

            # Next Hearing Date
            try:
                next_elem = frame.query_selector("td:has-text('Next Date')")
                next_hearing = next_elem.evaluate("el => el.nextElementSibling.innerText") if next_elem else "Not found"
            except Exception:
                next_hearing = "Not found"

            # Most recent PDF order/judgment link
            try:
                pdf_link_elem = frame.query_selector("a[href$='.pdf']")
                pdf_url = pdf_link_elem.get_attribute("href") if pdf_link_elem else None
            except Exception:
                pdf_url = None

            details = {
                "petitioner": petitioner,
                "respondent": respondent,
                "filing_date": filing_date,
                "next_hearing": next_hearing,
                "pdf_url": pdf_url
            }

        except PlaywrightTimeoutError as e:
            print("Timeout error:", e)
            details = {
                "petitioner": "Timeout",
                "respondent": "Timeout",
                "filing_date": "Timeout",
                "next_hearing": "Timeout",
                "pdf_url": None
            }
        except Exception as e:
            print("Error:", e)
            details = {
                "petitioner": "Error",
                "respondent": "Error",
                "filing_date": "Error",
                "next_hearing": "Error",
                "pdf_url": None
            }
        finally:
            browser.close()
    return details
