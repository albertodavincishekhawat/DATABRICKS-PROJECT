"""
Repo Rate Collector

Reads RBI policy repo rate from the CSV produced by rbi_mmo_scraper.py.
Repo rate is derived daily as (MSF + SDF) / 2 from the RBI Money Market
Operations page — the corridor is always ±25bps from the policy repo rate.

Source  : src/data_collection/input/repo_rate_daily.csv
Refresh : python3 -m src.data_collection.collectors.rbi_mmo_scraper
Backfill: python3 -m src.data_collection.collectors.rbi_mmo_backfill
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import logging

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

DATA_PATH = Path("src/data_collection/input/repo_rate_daily.csv")


class RepoRateCollector(BaseCollector):
    """
    Collect RBI policy repo rate from the MMO-derived CSV.

    Forward-fills between dates since the rate only changes at MPC meetings
    (~6 times per year) but the CSV is refreshed daily.
    """

    def __init__(self):
        super().__init__("Repo_Rate", frequency="monthly")
        self.rate_timeline: List[Tuple[datetime, float]] = []
        self._date_index: Dict[datetime, float] = {}
        self._load_rates()

    def _load_rates(self) -> None:
        if not DATA_PATH.exists():
            logger.warning(
                f"[Repo_Rate] Data file not found: {DATA_PATH}. "
                "Run rbi_mmo_backfill.py then rbi_mmo_scraper.py."
            )
            return

        df = pd.read_csv(DATA_PATH, parse_dates=["date"])
        df = df.dropna(subset=["repo_rate"]).sort_values("date").reset_index(drop=True)

        for _, row in df.iterrows():
            dt = row["date"].to_pydatetime()
            rate = float(row["repo_rate"])
            self.rate_timeline.append((dt, rate))
            self._date_index[dt] = rate

        logger.info(f"[Repo_Rate] Loaded {len(self.rate_timeline)} entries from {DATA_PATH}")

    # ── BaseCollector abstract methods ────────────────────────────────────────

    def has_data_on_date(self, date: datetime) -> bool:
        if not self.rate_timeline:
            return False
        return self.rate_timeline[0][0] <= date

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """Return the date of the most recent entry on or before the given date."""
        result = None
        for entry_date, _ in self.rate_timeline:
            if entry_date <= date:
                result = entry_date
            else:
                break
        return result

    def get_value(self, data_date: datetime) -> Optional[float]:
        """Return the repo rate for an exact CSV entry date."""
        return self._date_index.get(data_date)

    def aggregate_to_month(self, month: str, sync_date: datetime) -> Dict[str, Any]:
        source_date = self.find_data_on_date(sync_date)

        if source_date is None:
            return {"value": None, "data_quality": "MISSING", "source_date": None}

        rate = self.get_value(source_date)
        quality = "ACTUAL" if source_date.date() == sync_date.date() else "FORWARD_FILL"

        return {
            "value": rate,
            "data_quality": quality,
            "source_date": source_date.strftime("%Y-%m-%d"),
        }
