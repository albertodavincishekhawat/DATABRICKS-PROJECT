"""
NSDL FPI Monthly Data Scraper

Fetches real monthly FPI (Foreign Portfolio Investor) net investment data
from NSDL's official ASP.NET WebForms portal using viewstate postbacks.

Source: https://www.fpi.nsdl.co.in/Reports/Yearwise.aspx?RptType=6
Coverage: 2002 - current year, monthly granularity
Columns: Equity, Debt, Debt-VRR, Hybrid, Total (all in INR Crores)
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)

URL = 'https://www.fpi.nsdl.co.in/Reports/Yearwise.aspx?RptType=6'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

MONTH_TO_NUM = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12,
}


def _extract_viewstate(soup):
    """Pull ASP.NET hidden fields needed for postback."""
    return {
        f: (soup.find('input', {'name': f}) or {}).get('value', '')
        for f in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']
    }


def fetch_year(session, year):
    """POST back to NSDL with a specific year selection and parse monthly rows."""
    # Get fresh viewstate
    r = session.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    post_data = {
        **_extract_viewstate(soup),
        '__EVENTTARGET': 'ddl',
        '__EVENTARGUMENT': '',
        'ddl': str(year),
        'ddlCurr': 'INR',
    }

    r2 = session.post(
        URL,
        data=post_data,
        headers={**HEADERS, 'Referer': URL, 'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30,
    )
    r2.raise_for_status()

    # NSDL renames the year header in the response — verify we got what we asked for
    if f'Calendar Year - {year}' not in r2.text:
        raise RuntimeError(f"NSDL did not return year {year}")

    tables = pd.read_html(StringIO(r2.text))
    if len(tables) < 2:
        raise RuntimeError(f"Expected 2 tables, got {len(tables)}")

    t = tables[1]
    # Flatten multi-level columns
    t.columns = [
        ' | '.join(str(c) for c in col if 'Unnamed' not in str(c))
        for col in t.columns
    ]

    # Identify columns by keyword (positions are stable but names are verbose)
    month_col = t.columns[0]
    equity_col = next(c for c in t.columns if 'Equity' in c and 'Total' not in c)
    debt_col = next(c for c in t.columns if c.endswith('| Debt'))
    hybrid_col = next(c for c in t.columns if 'Hybrid' in c)
    total_col = next(c for c in t.columns if 'Total' in c and 'INR Crores' in c)

    rows = []
    for _, row in t.iterrows():
        month_name = str(row[month_col]).strip().rstrip('*').strip()
        if month_name not in MONTH_TO_NUM:
            continue  # Skip Total / footer rows
        month_num = MONTH_TO_NUM[month_name]
        # Last day of month for canonical date
        last_day = pd.Period(f'{year}-{month_num:02d}', freq='M').days_in_month
        rows.append({
            'Date': f'{year}-{month_num:02d}-{last_day:02d}',
            'FPI_Equity': pd.to_numeric(row[equity_col], errors='coerce'),
            'FPI_Debt': pd.to_numeric(row[debt_col], errors='coerce'),
            'FPI_Hybrid': pd.to_numeric(row[hybrid_col], errors='coerce'),
            'FPI_Total': pd.to_numeric(row[total_col], errors='coerce'),
        })

    return pd.DataFrame(rows)


def fetch_all(start_year=2020, end_year=2026):
    """Scrape NSDL year by year, return combined DataFrame."""
    session = requests.Session()
    all_data = []

    for year in range(start_year, end_year + 1):
        logger.info(f"[NSDL] Fetching year {year}...")
        try:
            df = fetch_year(session, year)
            logger.info(f"  ✓ {len(df)} months retrieved")
            all_data.append(df)
            time.sleep(1)  # Be polite to NSDL
        except Exception as e:
            logger.error(f"  ✗ Year {year} failed: {e}")

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sort_values('Date').reset_index(drop=True)
    return combined


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    df = fetch_all(2020, 2026)
    if df is None or df.empty:
        print("FAILED: no data retrieved")
        return 1

    out = Path('src/data_collection/input/fii_nsdl_monthly.csv')
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\n✓ Saved {len(df)} months to {out}")
    print(f"  Date range: {df['Date'].iloc[0]} → {df['Date'].iloc[-1]}")
    print(f"  Equity total: ₹{df['FPI_Equity'].sum():,.0f} Cr")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
