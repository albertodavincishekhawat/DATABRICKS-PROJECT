"""
USOIL (WTI Crude Oil) Collector

Loads daily WTI spot prices from the local CSV produced by usoil_scraper.py
and provides R3-specific calculations: 12-month trailing average and ratio.

R3 trigger : ratio = usoil_today / usoil_12m_avg  >= 1.80
R3 yellow  : ratio >= 1.40 and < 1.80
usoil_12m_avg is the mean of all available trading days in the trailing
365 calendar days, recalculated on the 1st of each month.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import logging
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

USOIL_CSV = Path('src/data_collection/input/usoil_daily.csv')


class USOILCollector(BaseCollector):
    """
    Daily WTI crude oil prices for R3 rule evaluation.

    Frequency : Daily (trading days only)
    Source    : usoil_daily.csv (YFinance CL=F)
    Value     : Closing spot price in USD/barrel
    """

    def __init__(self):
        super().__init__('USOIL', frequency='daily')
        self.data: Optional[pd.DataFrame] = None
        self._load()

    def _load(self):
        if not USOIL_CSV.exists():
            logger.error(f"[USOIL] CSV not found: {USOIL_CSV} — run usoil_scraper.py first")
            return
        try:
            df = pd.read_csv(USOIL_CSV, parse_dates=['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            self.data = df
            logger.info(
                f"[USOIL] Loaded {len(df)} daily rows "
                f"({df['Date'].iloc[0].date()} → {df['Date'].iloc[-1].date()})"
            )
        except Exception as e:
            logger.error(f"[USOIL] Failed to load {USOIL_CSV}: {e}")

    # ── BaseCollector interface ───────────────────────────────────────────

    def has_data_on_date(self, date: datetime) -> bool:
        if self.data is None or self.data.empty:
            return False
        return (self.data['Date'].dt.date == date.date()).any()

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """Return the most recent trading day on or before date."""
        if self.data is None or self.data.empty:
            return None
        subset = self.data[self.data['Date'].dt.date <= date.date()]
        if subset.empty:
            return None
        return subset['Date'].iloc[-1].to_pydatetime()

    def get_value(self, data_date: datetime) -> Optional[float]:
        if self.data is None or self.data.empty:
            return None
        row = self.data[self.data['Date'].dt.date == data_date.date()]
        if row.empty:
            return None
        val = row['WTI_USD'].iloc[0]
        return float(val) if pd.notna(val) else None

    def aggregate_to_month(self, month: str, sync_date: datetime) -> Dict[str, Any]:
        """Return the last available WTI price for the given month."""
        if self.data is None or self.data.empty:
            return {'value': None, 'data_quality': 'MISSING', 'source_date': None}

        year, month_num = map(int, month.split('-'))
        period = pd.Period(f'{year}-{month_num:02d}', freq='M')
        month_data = self.data[self.data['Date'].dt.to_period('M') == period]

        if month_data.empty:
            return {'value': None, 'data_quality': 'MISSING', 'source_date': None}

        last_row = month_data.iloc[-1]
        return {
            'value': round(float(last_row['WTI_USD']), 2),
            'data_quality': 'OK',
            'source_date': last_row['Date'].strftime('%Y-%m-%d'),
        }

    # ── R3-specific helpers ───────────────────────────────────────────────

    def get_latest_price(self, as_of: datetime | None = None) -> Optional[float]:
        """Most recent available price on or before as_of (default: today)."""
        if as_of is None:
            as_of = datetime.today()
        data_date = self.find_data_on_date(as_of)
        if data_date is None:
            return None
        return self.get_value(data_date)

    def get_12m_avg(self, as_of: datetime | None = None) -> Optional[float]:
        """
        Mean daily WTI price over the trailing 365 calendar days ending on as_of.
        Recalculated monthly per the R3 spec.
        """
        if self.data is None or self.data.empty:
            return None
        if as_of is None:
            as_of = datetime.today()

        window_start = as_of - timedelta(days=365)
        window = self.data[
            (self.data['Date'] >= pd.Timestamp(window_start)) &
            (self.data['Date'] <= pd.Timestamp(as_of))
        ]
        if window.empty:
            return None
        return float(window['WTI_USD'].mean())

    def get_ratio(self, as_of: datetime | None = None) -> Optional[float]:
        """R3 ratio: usoil_today / usoil_12m_avg."""
        today_price = self.get_latest_price(as_of)
        avg_12m = self.get_12m_avg(as_of)
        if today_price is None or avg_12m is None or avg_12m == 0:
            return None
        return round(today_price / avg_12m, 4)

    def get_r3_status(self, as_of: datetime | None = None) -> Dict[str, Any]:
        """
        Full R3 evaluation as of a given date.

        Returns:
            {
                usoil_today   : float,
                usoil_12m_avg : float,
                ratio         : float,
                status        : 'TRIGGERED' | 'YELLOW' | 'CLEAR',
                trigger_price : float  (price at which TRIGGERED fires),
            }
        """
        if as_of is None:
            as_of = datetime.today()

        today_price = self.get_latest_price(as_of)
        avg_12m = self.get_12m_avg(as_of)

        if today_price is None or avg_12m is None:
            return {'status': 'MISSING', 'usoil_today': today_price, 'usoil_12m_avg': avg_12m}

        ratio = today_price / avg_12m
        trigger_price = round(avg_12m * 1.80, 2)

        if ratio >= 1.80:
            status = 'TRIGGERED'
        elif ratio >= 1.40:
            status = 'YELLOW'
        else:
            status = 'CLEAR'

        return {
            'usoil_today': round(today_price, 2),
            'usoil_12m_avg': round(avg_12m, 2),
            'ratio': round(ratio, 4),
            'status': status,
            'trigger_price': trigger_price,
        }
