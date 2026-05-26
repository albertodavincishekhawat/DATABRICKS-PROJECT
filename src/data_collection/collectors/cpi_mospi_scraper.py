"""
India CPI Scraper - rateinflation.com

Fetches India Consumer Price Index (All Items, Combined) monthly data
from rateinflation.com, which sources directly from MOSPI/PIB.

Base year: 2024 = 100
Coverage:  2013 → current month (updated 12th of each month)
Verified:  Apr 2026 Combined = 105.12 matches PIB press release exactly.

No API key required. Simple HTML table scrape.
"""

from curl_cffi import requests as cr
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

URL = 'https://www.rateinflation.com/consumer-price-index/india-historical-cpi/'
MONTH_COLS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


def fetch() -> pd.DataFrame:
    """Scrape and return monthly CPI DataFrame with columns: Date, CPI, Source."""
    s = cr.Session(impersonate='chrome120')
    r = s.get(URL, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        raise RuntimeError('No table found on rateinflation.com CPI page')

    raw = pd.read_html(StringIO(str(tables[0])))[0]
    # Normalise column names to lowercase
    raw.columns = [str(c).lower() for c in raw.columns]

    rows = []
    for _, row in raw.iterrows():
        year = int(row['year'])
        for month_idx, col in enumerate(MONTH_COLS, start=1):
            val = row.get(col)
            if pd.isna(val):
                continue
            rows.append({
                'Date': pd.Timestamp(year, month_idx, 1),
                'CPI': float(val),
                'Source': 'MOSPI',
            })

    df = pd.DataFrame(rows).sort_values('Date').reset_index(drop=True)
    logger.info(f"[CPI] {len(df)} months scraped: {df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()}")
    return df


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    df = fetch()
    if df.empty:
        print('FAILED: no data')
        return 1

    out = Path('src/data_collection/input/cpi_combined.csv')
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f'\n✓ Saved {len(df)} months to {out}')
    print(f'  Range: {df["Date"].iloc[0].date()} → {df["Date"].iloc[-1].date()}')
    print(f'  Base year: 2024 = 100  |  Source: MOSPI via rateinflation.com')
    print(f'\nLatest 6 months:')
    print(df.tail(6).to_string(index=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
