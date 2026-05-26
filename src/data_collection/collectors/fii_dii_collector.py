"""
FII Collector

Loads monthly FPI Equity net flows from the NSDL scraper output CSV.
Data is already aggregated to monthly totals — no daily summing needed.

Source : src/data_collection/input/fii_nsdl_monthly.csv
         (produced by nsdl_fpi_scraper.py)
Columns: Date (YYYY-MM-DD, last day of month), FPI_Equity (Rs. Crore, signed)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import logging
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

NSDL_CSV = Path('src/data_collection/input/fii_nsdl_monthly.csv')


class FIIDIICollector(BaseCollector):
    """
    Loads monthly FII (FPI Equity) net flows from NSDL CSV.

    Frequency : Monthly
    Source    : fii_nsdl_monthly.csv (NSDL FPI Yearwise report)
    Value     : FPI_Equity — net equity investment in Rs. Crore (signed)
    """

    def __init__(self):
        super().__init__('FII', frequency='monthly')
        self.data: Optional[pd.DataFrame] = None
        self._load()

    def _load(self):
        if not NSDL_CSV.exists():
            logger.error(f"[FII] CSV not found: {NSDL_CSV} — run nsdl_fpi_scraper.py first")
            return
        try:
            df = pd.read_csv(NSDL_CSV, parse_dates=['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            self.data = df
            logger.info(f"[FII] Loaded {len(df)} months from {NSDL_CSV.name} "
                        f"({df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()})")
        except Exception as e:
            logger.error(f"[FII] Failed to load {NSDL_CSV}: {e}")

    def has_data_on_date(self, date: datetime) -> bool:
        if self.data is None or self.data.empty:
            return False
        period = pd.Period(date, freq='M')
        return (self.data['Date'].dt.to_period('M') == period).any()

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        if self.data is None or self.data.empty:
            return None
        period = pd.Period(date, freq='M')
        row = self.data[self.data['Date'].dt.to_period('M') == period]
        if row.empty:
            return None
        return row['Date'].iloc[0].to_pydatetime()

    def get_value(self, data_date: datetime) -> Optional[float]:
        if self.data is None or self.data.empty:
            return None
        period = pd.Period(data_date, freq='M')
        row = self.data[self.data['Date'].dt.to_period('M') == period]
        if row.empty:
            return None
        val = row['FPI_Equity'].iloc[0]
        return float(val) if pd.notna(val) else None

    def aggregate_to_month(self, month: str, sync_date: datetime) -> Dict[str, Any]:
        """
        Return the NSDL monthly FPI Equity net flow for the given month.

        Args:
            month     : 'YYYY-MM'
            sync_date : synchronized date for this month (unused — data is pre-aggregated)
        """
        if self.data is None or self.data.empty:
            return {'value': None, 'data_quality': 'MISSING', 'source_date': None}

        year, month_num = map(int, month.split('-'))
        period = pd.Period(f'{year}-{month_num:02d}', freq='M')
        row = self.data[self.data['Date'].dt.to_period('M') == period]

        if row.empty:
            return {'value': None, 'data_quality': 'MISSING', 'source_date': None}

        val = row['FPI_Equity'].iloc[0]
        source_date = row['Date'].iloc[0].strftime('%Y-%m-%d')

        return {
            'value': float(val) if pd.notna(val) else None,
            'data_quality': 'OK' if pd.notna(val) else 'PARTIAL',
            'source_date': source_date,
        }
