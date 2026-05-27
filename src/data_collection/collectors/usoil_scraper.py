"""
USOIL (WTI Crude Oil) Daily Price Scraper

Fetches daily WTI crude oil prices via YFinance (ticker: CL=F).
Updates to the previous trading day — same latency as all other
YFinance sources in this project.

Source  : YFinance CL=F (NYMEX WTI Crude Oil Futures front-month)
Coverage: Jan 2020 – present (daily trading days)
Output  : src/data_collection/input/usoil_daily.csv
Columns : Date (YYYY-MM-DD), WTI_USD (USD/barrel, closing price)
"""

import logging
import pandas as pd
import yfinance as yf
from pathlib import Path

logger = logging.getLogger(__name__)

TICKER = 'CL=F'
START_DATE = '2020-01-01'
OUTPUT_PATH = Path('src/data_collection/input/usoil_daily.csv')


def fetch() -> pd.DataFrame | None:
    logger.info(f"[USOIL] Downloading {TICKER} from YFinance…")
    try:
        raw = yf.download(TICKER, start=START_DATE, auto_adjust=True, progress=False)
    except Exception as e:
        logger.error(f"[USOIL] YFinance download failed: {e}")
        return None

    if raw.empty:
        logger.error("[USOIL] YFinance returned empty DataFrame")
        return None

    raw.columns = raw.columns.get_level_values(0)
    df = raw[['Close']].copy()
    df.index.name = 'Date'
    df = df.reset_index()
    df = df.rename(columns={'Close': 'WTI_USD'})
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.normalize()
    df = df.dropna(subset=['WTI_USD']).sort_values('Date').reset_index(drop=True)

    logger.info(
        f"[USOIL] {len(df)} daily rows  "
        f"({df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()})"
    )
    return df


def run(output_path: str | Path = OUTPUT_PATH) -> pd.DataFrame | None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = fetch()
    if df is None or df.empty:
        logger.error("[USOIL] No data retrieved")
        return None

    df.to_csv(output_path, index=False)
    logger.info(f"[USOIL] Saved {len(df)} rows → {output_path}")
    return df


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(levelname)-7s  %(message)s',
        datefmt='%H:%M:%S',
    )

    print("\n" + "=" * 60)
    print("USOIL (WTI) Scraper  —  YFinance CL=F")
    print("=" * 60 + "\n")

    df = run()

    if df is not None and not df.empty:
        print(f"\n✓ {len(df)} daily records")
        print(f"  Range  : {df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()}")
        print(f"  Latest : ${df['WTI_USD'].iloc[-1]:.2f}/bbl  ({df['Date'].iloc[-1].date()})")
        print(f"  Output : {OUTPUT_PATH}\n")
        print(df.tail(5).to_string(index=False))
    else:
        print("\n✗ No data retrieved")
