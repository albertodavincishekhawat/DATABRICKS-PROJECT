"""
RBI Weekly Statistical Supplement (WSS) Scraper

Fetches real weekly RBI Balance Sheet (Table 1: Liabilities and Assets)
from rbi.org.in by listing 1T_*.XLSX files via the WSS portal POST,
downloading each, parsing, and aggregating to monthly granularity.

Source listing: https://www.rbi.org.in/Scripts/BS_ViewWss.aspx
Source files:   https://rbidocs.rbi.org.in/rdocs/Wss/DOCs/1T_DDMMYYYY{hash}.XLSX

Coverage: 2020-01 to current (every Friday)
Output columns: Date, Total_Liabilities, FCA, Notes_Circulation, Deposits, Source

F5 bot-detection on the POST is bypassed via curl_cffi Chrome TLS impersonation.
Direct XLSX downloads succeed with plain requests + Referer.
"""

from curl_cffi import requests as cr
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import time
import logging
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)

LIST_URL = 'https://www.rbi.org.in/Scripts/BS_ViewWss.aspx'
DOC_REFERER = 'https://www.rbi.org.in/'

# Rows in the 1T_ XLSX (0-indexed, after pandas reads with header=None)
ROW_NOTES_IN_CIRCULATION = 7
ROW_DEPOSITS_FIRST = 10  # 2.1 Central Government
ROW_DEPOSITS_LAST = 16   # 2.7 Others (inclusive)
ROW_TOTAL_LIAB = 18      # "Total Liabilities/Assets"
ROW_FCA = 19             # "Foreign Currency Assets"
COL_CURRENT_WEEK = 3     # 0-indexed; column 4 in the sheet


def _viewstate(soup):
    return {
        name: (soup.find('input', {'name': name}) or {}).get('value', '')
        for name in ('__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION')
    }


def list_1t_urls():
    """Return list of all 1T_ XLSX URLs available on the WSS portal."""
    s = cr.Session(impersonate='chrome120')
    r = s.get(LIST_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    # POST with any valid year/month/section — server returns the full historical listing
    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        **_viewstate(soup),
        'ddlYear': '2026',
        'ddlMonth': '5',
        'ddlSection': '1',
        'UsrFontCntr$btn': '',
        'btnGo': 'Go',
    }
    r2 = s.post(
        LIST_URL,
        data=data,
        headers={'Referer': LIST_URL, 'Origin': 'https://www.rbi.org.in'},
        timeout=60,
    )
    r2.raise_for_status()

    urls = re.findall(r'https://rbidocs\.rbi\.org\.in/[^\s"\'<>]+\.XLSX', r2.text)
    urls = [u for u in dict.fromkeys(urls) if '/1T_' in u]
    return urls


def parse_url_date(url):
    """Extract the DDMMYYYY publication date from a 1T_ URL.

    Returns None for older legacy filenames (DDMMYY) or any value that
    doesn't yield a plausible publication year (2000–2030).
    """
    m = re.search(r'/1T_(\d{8})', url)
    if not m:
        return None
    s = m.group(1)
    try:
        d = pd.to_datetime(f'{s[4:8]}-{s[2:4]}-{s[0:2]}')
    except (ValueError, TypeError):
        return None
    if not (2000 <= d.year <= 2030):
        return None
    return d


def parse_xlsx(content):
    """Parse a 1T_ XLSX byte payload into a dict of balance-sheet values."""
    df = pd.read_excel(BytesIO(content), sheet_name=0, header=None)
    if df.shape[0] <= ROW_FCA or df.shape[1] <= COL_CURRENT_WEEK:
        raise ValueError(f"unexpected sheet shape {df.shape}")

    def cell(row):
        v = df.iat[row, COL_CURRENT_WEEK]
        return pd.to_numeric(v, errors='coerce')

    # Sub-rows like "Market Stabilisation Scheme" are sometimes blank — skip NaN
    deposits = pd.Series(
        [cell(r) for r in range(ROW_DEPOSITS_FIRST, ROW_DEPOSITS_LAST + 1)]
    ).sum(skipna=True)
    return {
        'Total_Liabilities': cell(ROW_TOTAL_LIAB),
        'FCA': cell(ROW_FCA),
        'Notes_Circulation': cell(ROW_NOTES_IN_CIRCULATION),
        'Deposits': deposits,
    }


def download_xlsx(url, session=None, retries=3, sleep=1.0):
    """Download a single 1T_ XLSX with Referer; retries on transient errors."""
    sess = session or requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Referer': DOC_REFERER,
    }
    last_err = None
    for attempt in range(retries):
        try:
            r = sess.get(url, headers=headers, timeout=60)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content
            last_err = f"status={r.status_code} len={len(r.content)}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"download failed after {retries} attempts: {last_err}")


def scrape_weekly(start_date='2020-01-01', end_date=None, sleep_between=0.4):
    """Download and parse all 1T_ XLSX files in the date range."""
    end = pd.to_datetime(end_date) if end_date else pd.Timestamp.today()
    start = pd.to_datetime(start_date)

    logger.info("[RBI WSS] listing XLSX URLs...")
    urls = list_1t_urls()
    logger.info(f"[RBI WSS] {len(urls)} 1T_ URLs total")

    items = []
    for u in urls:
        d = parse_url_date(u)
        if d is not None and start <= d <= end:
            items.append((d, u))
    items.sort()
    logger.info(f"[RBI WSS] {len(items)} URLs in date range {start.date()}..{end.date()}")

    sess = requests.Session()
    rows = []
    for i, (d, u) in enumerate(items, 1):
        try:
            content = download_xlsx(u, session=sess)
            parsed = parse_xlsx(content)
            rows.append({'Date': d, **parsed, 'Source': 'RBI_WSS'})
            if i % 25 == 0 or i == len(items):
                logger.info(f"  [{i}/{len(items)}] {d.date()} ok")
        except Exception as e:
            logger.warning(f"  [{i}/{len(items)}] {d.date()} FAILED: {e}")
        time.sleep(sleep_between)

    if not rows:
        return None
    return pd.DataFrame(rows).sort_values('Date').reset_index(drop=True)


def aggregate_monthly(weekly_df):
    """Aggregate weekly readings to monthly (use last available week per month)."""
    if weekly_df is None or weekly_df.empty:
        return None
    df = weekly_df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['_ym'] = df['Date'].dt.to_period('M')
    monthly = df.groupby('_ym').tail(1).copy()
    monthly['Date'] = monthly['_ym'].dt.to_timestamp(how='end').dt.normalize()
    monthly = monthly.drop(columns=['_ym']).reset_index(drop=True)
    return monthly


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    weekly = scrape_weekly(start_date='2020-01-01')
    if weekly is None or weekly.empty:
        print("FAILED: no data")
        return 1

    out_dir = Path('src/data_collection/input')
    out_dir.mkdir(parents=True, exist_ok=True)

    weekly_path = out_dir / 'rbi_wss_weekly.csv'
    weekly.to_csv(weekly_path, index=False)
    print(f"\nweekly: {len(weekly)} rows -> {weekly_path}")
    print(f"  {weekly['Date'].iloc[0].date()} .. {weekly['Date'].iloc[-1].date()}")

    monthly = aggregate_monthly(weekly)
    monthly_path = out_dir / 'rbi_wss_monthly.csv'
    monthly.to_csv(monthly_path, index=False)
    print(f"monthly: {len(monthly)} rows -> {monthly_path}")
    print(monthly.tail(5).to_string(index=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())