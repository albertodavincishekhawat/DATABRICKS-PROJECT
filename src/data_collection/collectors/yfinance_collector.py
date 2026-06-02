"""
YFinance Collector

Reads daily market price data from the CSV produced by yfinance_scraper.py.
Handles 5 parameters: NIFTY50, USDINR, GOLD_INR, GOLD_USD, NIFTYBEES

Source  : src/data_collection/input/yfinance_daily.csv
Refresh : python3 -m src.data_collection.collectors.yfinance_scraper
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import logging

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

CSV_PATH = Path("src/data_collection/input/yfinance_daily.csv")

VALID_SOURCES = {"NIFTY50", "USDINR", "GOLD_INR", "GOLD_USD", "NIFTYBEES"}


class YFinanceCollector(BaseCollector):
    """
    Collect daily market price data from the YFinance CSV.

    Frequency: Daily (trading days only)
    Aggregation: Close price on or before sync_date (searches back up to 5 days for weekends/holidays)
    """

    def __init__(self, source_name: str):
        if source_name not in VALID_SOURCES:
            raise ValueError(f"Unknown source: {source_name}. Valid: {VALID_SOURCES}")

        super().__init__(source_name, frequency="daily")
        self.data: Optional[pd.DataFrame] = None
        self._load_data()

    def _load_data(self) -> None:
        if not CSV_PATH.exists():
            logger.warning(
                f"[{self.name}] CSV not found: {CSV_PATH}. "
                "Run yfinance_scraper.py to generate it."
            )
            return

        df = pd.read_csv(CSV_PATH, parse_dates=["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df = df.set_index("Date")

        if self.name not in df.columns:
            logger.error(f"[{self.name}] Column not found in {CSV_PATH}")
            return

        self.data = df[[self.name]].dropna()
        logger.info(f"[{self.name}] Loaded {len(self.data)} trading days from {CSV_PATH}")

    # ── BaseCollector abstract methods ────────────────────────────────────────

    def has_data_on_date(self, date: datetime) -> bool:
        if self.data is None or self.data.empty:
            return False
        return pd.Timestamp(date.date()) in self.data.index

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """Return most recent trading day on or before date (searches back up to 5 days)."""
        if self.data is None or self.data.empty:
            return None

        for offset in range(0, 6):
            candidate = date - timedelta(days=offset)
            if pd.Timestamp(candidate.date()) in self.data.index:
                return candidate

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        if self.data is None or self.data.empty:
            return None

        ts = pd.Timestamp(data_date.date())
        if ts in self.data.index:
            return float(self.data.loc[ts, self.name])
        return None

    def aggregate_to_month(self, month: str, sync_date: datetime) -> Dict[str, Any]:
        data_date = self.find_data_on_date(sync_date)

        if data_date is None:
            return {"value": None, "data_quality": "MISSING", "source_date": None}

        close_price = self.get_value(data_date)

        if close_price is None:
            return {"value": None, "data_quality": "MISSING", "source_date": None}

        days_shifted = (sync_date.date() - data_date.date()).days
        quality = "OK" if days_shifted == 0 else f"SHIFTED_{days_shifted}d"

        return {
            "value": close_price,
            "data_quality": quality,
            "source_date": data_date.strftime("%Y-%m-%d"),
        }
