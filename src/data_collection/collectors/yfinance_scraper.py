"""
YFinance Daily Price Scraper

Fetches daily closing prices for 5 market data parameters via YFinance
and saves to a single combined CSV. Run this to refresh or backfill.

Source  : Yahoo Finance (yfinance library)
Output  : src/data_collection/input/yfinance_daily.csv
Columns : Date, NIFTY50, USDINR, GOLD_INR, GOLD_USD, NIFTYBEES
Coverage: 2020-01-01 to previous trading day

Note: BRENT_CRUDE (BZ=F) is excluded — R3 uses USOIL (CL=F) via usoil_scraper.py

Run:
    python3 -m src.data_collection.collectors.yfinance_scraper
"""

import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

START_DATE = "2020-01-01"
OUTPUT_PATH = Path("src/data_collection/input/yfinance_daily.csv")

TICKERS = {
    "NIFTY50":   "^NSEI",
    "USDINR":    "USDINR=X",
    "GOLD_INR":  "GOLD",
    "GOLD_USD":  "GC=F",
    "NIFTYBEES": "NIFTYBEES.NS",
}


def fetch() -> pd.DataFrame | None:
    logger.info(f"[YFinance] Downloading {len(TICKERS)} tickers from {START_DATE}…")
    try:
        raw = yf.download(
            list(TICKERS.values()),
            start=START_DATE,
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"[YFinance] Download failed: {e}")
        return None

    if raw.empty:
        logger.error("[YFinance] No data returned")
        return None

    close = raw["Close"].copy()
    ticker_to_name = {v: k for k, v in TICKERS.items()}
    close = close.rename(columns=ticker_to_name)
    close.index.name = "Date"
    close = close.reset_index()
    close["Date"] = pd.to_datetime(close["Date"]).dt.date.astype(str)

    col_order = ["Date"] + list(TICKERS.keys())
    close = close[[c for c in col_order if c in close.columns]]

    logger.info(f"[YFinance] Fetched {len(close)} rows, {len(close.columns)-1} parameters")
    return close


def save(df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)
        combined = (
            pd.concat([existing, df])
            .drop_duplicates(subset=["Date"], keep="last")
            .sort_values("Date")
            .reset_index(drop=True)
        )
    else:
        combined = df.sort_values("Date").reset_index(drop=True)

    combined.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"[YFinance] Saved {len(combined)} rows → {OUTPUT_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = fetch()
    if result is not None:
        save(result)
        print(f"\nSample (last 3 rows):")
        print(result.tail(3).to_string(index=False))
