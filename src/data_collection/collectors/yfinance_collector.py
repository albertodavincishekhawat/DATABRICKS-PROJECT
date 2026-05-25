"""
YFinance Collector

Fetches daily data from YFinance and provides monthly aggregation.
Handles 6 sources: NIFTY50, USDINR, GOLD_INR, GOLD_USD, BRENT_CRUDE, NIFTYBEES
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import logging
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class YFinanceCollector(BaseCollector):
    """
    Collect daily price data from YFinance.

    Frequency: Daily trading days
    Aggregation: Month-end close price (or last trading day if month-end is weekend)
    """

    TICKERS = {
        'NIFTY50': '^NSEI',
        'USDINR': 'USDINR=X',
        'GOLD_INR': 'GOLD',
        'GOLD_USD': 'GC=F',
        'BRENT_CRUDE': 'BZ=F',
        'NIFTYBEES': 'NIFTYBEES.NS',
    }

    def __init__(self, source_name: str):
        """
        Initialize YFinance collector.

        Args:
            source_name: One of NIFTY50, USDINR, GOLD_INR, GOLD_USD, BRENT_CRUDE, NIFTYBEES
        """
        if source_name not in self.TICKERS:
            raise ValueError(f"Unknown source: {source_name}")

        super().__init__(source_name, frequency='daily')
        self.ticker = self.TICKERS[source_name]
        self.data = None

        # Fetch data on initialization
        self._fetch_data()

    def _fetch_data(self):
        """Fetch historical data from YFinance."""
        if not YFINANCE_AVAILABLE:
            logger.warning(f"[{self.name}] YFinance not installed")
            return

        try:
            self.log_status(f"Fetching data for {self.ticker}...")
            self.data = yf.download(
                self.ticker,
                start='2020-01-01',
                end='2026-04-30',
                progress=False
            )

            if self.data.empty:
                logger.warning(f"[{self.name}] No data returned for {self.ticker}")
            else:
                logger.info(f"[{self.name}] Loaded {len(self.data)} trading days")

        except Exception as e:
            logger.error(f"[{self.name}] Error fetching {self.ticker}: {str(e)[:100]}")
            self.data = None

    def has_data_on_date(self, date: datetime) -> bool:
        """Check if data exists on a specific date."""
        if self.data is None or self.data.empty:
            return False
        import pandas as pd
        return pd.Timestamp(date.date()) in self.data.index

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find data on or before this date.

        YFinance only has trading days, so search backward for last trading day.
        """
        if self.data is None or self.data.empty:
            return None

        import pandas as pd
        # Search backward up to 5 days for last trading day
        for offset in range(0, 6):
            candidate = date - timedelta(days=offset)
            ts = pd.Timestamp(candidate.date())
            if ts in self.data.index:
                return candidate

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        """Get close price for a specific date."""
        if self.data is None or self.data.empty:
            return None

        try:
            import pandas as pd
            ts = pd.Timestamp(data_date.date())
            if ts in self.data.index:
                return float(self.data.loc[ts, 'Close'])
        except (KeyError, Exception):
            return None

        return None

    def aggregate_to_month(
        self,
        month: str,
        sync_date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate to monthly value (month-end close price).

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
        """
        # Find last trading day on or before sync_date
        data_date = self.find_data_on_date(sync_date)

        if data_date is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        # Get close price
        close_price = self.get_value(data_date)

        if close_price is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        # Determine quality based on how much we had to shift
        days_shifted = (sync_date.date() - data_date.date()).days
        if days_shifted == 0:
            quality = 'OK'
        elif days_shifted <= 2:
            quality = f'SHIFTED_{days_shifted}d'
        else:
            quality = f'SHIFTED_{days_shifted}d'

        return {
            'value': close_price,
            'data_quality': quality,
            'source_date': data_date.strftime('%Y-%m-%d')
        }
