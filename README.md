# Delhi High Court Case Fetcher

## Chosen Court
Delhi High Court (https://delhihighcourt.nic.in/)

## Setup

1. Install dependencies:
   ```
   pip install flask python-dotenv playwright
   playwright install
   ```
2. Set up `.env` (see sample).
3. Run:
   ```
   python app.py
   ```
4. Open `http://localhost:5000`

## CAPTCHA Handling
Delhi High Court site does not use CAPTCHA for basic case search. If introduced, manual intervention or third-party solving would be needed.

## Sample `.env`
```
DB_PATH=search_logs.db
SECRET_KEY=your_random_secret_key
```

## Logging
Each search is logged with query and raw HTML response in SQLite.

## License
MIT
