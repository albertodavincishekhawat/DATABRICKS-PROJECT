"""
CPI Collector

Fetches India CPI from FRED API (Federal Reserve Economic Data).
Series: INDCPIALLMINMEI (India Consumer Price Index)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import logging
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from pandas_datareader import data as web
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False


class CPICollector(BaseCollector):
    """
    Collect monthly India CPI from FRED.

    Frequency: Monthly (published mid-month for prior month)
    Source: INDCPIALLMINMEI (Federal Reserve Economic Data)
    Aggregation: Use month's published CPI value
    """

    FRED_SERIES = 'INDCPIALLMINMEI'

    def __init__(self):
        """Initialize CPI collector."""
        super().__init__('CPI', frequency='monthly')
        self.data = None
        self._fetch_data()

    def _fetch_data(self):
        """Fetch CPI data from FRED."""
        if not FRED_AVAILABLE:
            logger.warning("[CPI] pandas-datareader not installed")
            return

        try:
            self.log_status("Fetching from FRED...")
            df = web.DataReader(
                self.FRED_SERIES,
                'fred',
                start='2020-01-01',
                end='2026-04-30'
            )

            # Convert to DataFrame with Date column
            df = df.reset_index()
            df.columns = ['Date', 'CPI']
            df['Date'] = pd.to_datetime(df['Date'])

            # Index by year-month for quick lookup
            df['YearMonth'] = df['Date'].dt.to_period('M')
            self.data = df.set_index('YearMonth')

            logger.info(f"[CPI] Loaded {len(self.data)} data points ({self.data.index[0]} to {self.data.index[-1]})")

        except Exception as e:
            logger.error(f"[CPI] Error fetching from FRED: {str(e)[:100]}")
            self.data = None

    def has_data_on_date(self, date: datetime) -> bool:
        """
        Check if CPI data exists for this month.

        CPI is published monthly, so check if we have data for that month.
        """
        if self.data is None or self.data.empty:
            return False

        year_month = pd.Period(date, freq='M')
        return year_month in self.data.index

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find CPI data for this month.

        Returns the last day of the month if data exists.
        """
        if self.data is None or self.data.empty:
            return None

        year_month = pd.Period(date, freq='M')

        # CPI for a month is available after ~15th of next month
        # So we search current month and up to 2 months back
        for months_back in range(0, 3):
            search_period = year_month - months_back

            if search_period in self.data.index:
                # Return last day of the search month
                return datetime(search_period.year, search_period.month, 1) + timedelta(days=32)
                # Note: Adding 32 days and taking month-end works for any month

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        """Get CPI value for a specific date."""
        if self.data is None or self.data.empty:
            return None

        year_month = pd.Period(data_date, freq='M')

        try:
            if year_month in self.data.index:
                return float(self.data.loc[year_month, 'CPI'].values[0])
        except (KeyError, IndexError, Exception):
            return None

        return None

    def aggregate_to_month(
        self,
        month: str,
        sync_date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate to monthly CPI value.

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
        """
        # Parse month string
        year, month_num = map(int, month.split('-'))
        date = datetime(year, month_num, 1)

        # Find if CPI data exists for this month
        data_date = self.find_data_on_date(date)

        if data_date is None:
            # Try previous months (CPI sometimes published late)
            for months_back in range(1, 4):
                prev_month = date - timedelta(days=32)
                data_date = self.find_data_on_date(prev_month)
                if data_date is not None:
                    break

        if data_date is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        cpi_value = self.get_value(data_date)

        if cpi_value is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        return {
            'value': cpi_value,
            'data_quality': 'OK',
            'source_date': data_date.strftime('%Y-%m-%d')
        }
