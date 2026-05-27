"""
Brent Crude Oil Daily Price Scraper

Fetches daily Brent crude spot prices from the frictionless/datasets
oil-prices repository, which mirrors EIA Europe Brent Spot Price FOB data.

Source : https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-daily.csv
         (EIA data, updated daily, no API key required)
Coverage: May 1987 – present
Output  : src/data_collection/input/brent_daily.csv
Columns : Date (YYYY-MM-DD), Price (USD/barrel)
"""

import logging
import requests
import pandas as pd
from pathlib import Path
from io import StringIO

logger = logging.getLogger(__name__)

SOURCE_URL = (
    'https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-daily.csv'
)
OUTPUT_PATH = Path('src/data_collection/input/brent_daily.csv')


def fetch() -> pd.DataFrame | None:
    logger.info("[Brent] Downloading from datasets/oil-prices…")
    try:
        r = requests.get(SOURCE_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"[Brent] Download failed: {e}")
        return None

    df = pd.read_csv(StringIO(r.text), parse_dates=['Date'])
    df = df.rename(columns={'Price': 'Brent_USD'})
    df = df.dropna(subset=['Brent_USD'])
    df = df.sort_values('Date').reset_index(drop=True)

    logger.info(
        f"[Brent] {len(df)} daily rows  "
        f"({df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()})"
    )
    return df


def run(output_path: str | Path = OUTPUT_PATH) -> pd.DataFrame | None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = fetch()
    if df is None or df.empty:
        logger.error("[Brent] No data retrieved")
        return None

    df.to_csv(output_path, index=False)
    logger.info(f"[Brent] Saved {len(df)} rows → {output_path}")
    return df


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-7s  %(message)s',
        datefmt='%H:%M:%S',
    )

    print("\n" + "=" * 60)
    print("Brent Crude Oil Daily Price Scraper")
    print("=" * 60 + "\n")

    df = run()

    if df is not None and not df.empty:
        print(f"\n✓ Success — {len(df)} daily records")
        print(f"  Date range : {df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()}")
        print(f"  Latest     : ${df['Brent_USD'].iloc[-1]:.2f}/bbl  ({df['Date'].iloc[-1].date()})")
        print(f"  Output     : {OUTPUT_PATH}\n")
        print("Latest 5 rows:")
        print(df.tail(5).to_string(index=False))
    else:
        print("\n✗ Scraper returned no data")
