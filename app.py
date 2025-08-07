import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from scraper import fetch_case_details

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "search_logs.db")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

def log_search(case_type, case_number, filing_year, raw_response):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT,
            case_number TEXT,
            filing_year TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT
        )
    """)
    c.execute("""
        INSERT INTO searches (case_type, case_number, filing_year, raw_response)
        VALUES (?, ?, ?, ?)
    """, (case_type, case_number, filing_year, raw_response))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    case_types = ["W.P.(C)", "Crl.M.C.", "FAO", "RSA", "CRL.A.", "CS(OS)"]  # Example types
    if request.method == "POST":
        case_type = request.form.get("case_type", "").strip()
        case_number = request.form.get("case_number", "").strip()
        filing_year = request.form.get("filing_year", "").strip()
        # Basic input validation
        if not case_type or not case_number or not filing_year:
            flash("All fields are required.", "danger")
            return render_template("index.html", case_types=case_types)
        try:
            details, raw_html = fetch_case_details(case_type, case_number, filing_year)
            if not details:
                flash("No case found or invalid details.", "warning")
                return render_template("index.html", case_types=case_types)
            log_search(case_type, case_number, filing_year, raw_html)
            return render_template("result.html", details=details)
        except Exception as e:
            flash(f"Error fetching data: {str(e)}", "danger")
            return render_template("index.html", case_types=case_types)
    return render_template("index.html", case_types=case_types)

if __name__ == "__main__":
    app.run(debug=True)
