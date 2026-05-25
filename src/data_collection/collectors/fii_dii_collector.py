"""
FII/DII Collector

Collects Foreign Institutional Investor (FII) and Domestic Institutional Investor (DII)
daily flows from NSE and aggregates to monthly net flows.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
import logging
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import nsefin
    NSEFIN_AVAILABLE = True
except ImportError:
    NSEFIN_AVAILABLE = False


class FIIDIICollector(BaseCollector):
    """
    Collect daily FII/DII flows from NSE.

    Frequency: Daily (trading days)
    Aggregation: Sum all daily flows for the month (net FII/DII)
    Source: NSE via nsefin library
    """

    def __init__(self):
        """Initialize FII/DII collector."""
        super().__init__('FII_DII', frequency='daily')
        self.data = None
        self._fetch_data()

    def _fetch_data(self):
        """Fetch FII/DII data from CSV, NSE, or fallback."""
        from pathlib import Path

        # Try CSV first (monthly aggregated data)
        csv_path = 'src/data_collection/input/fii_dii_monthly.csv'
        if Path(csv_path).exists():
            try:
                self.log_status(f"Loading from CSV...")
                df = pd.read_csv(csv_path)
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
                self.data = df
                logger.info(f"[FII_DII] Loaded {len(self.data)} monthly records from CSV")
                return
            except Exception as e:
                logger.warning(f"[FII_DII] Error loading CSV: {str(e)[:80]}")

        # Fall back to NSE
        if not NSEFIN_AVAILABLE:
            logger.warning("[FII_DII] nsefin not installed")
            return

        try:
            self.log_status("Fetching from NSE...")
            nse = nsefin.NSEClient()
            df = nse.get_fii_dii_activity()

            if df is not None and len(df) > 0:
                # Ensure Date column is datetime
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.sort_values('Date')

                    self.data = df
                    logger.info(f"[FII_DII] Loaded {len(self.data)} daily records")
                else:
                    logger.warning("[FII_DII] Date column not found in NSE data")

        except Exception as e:
            logger.error(f"[FII_DII] Error fetching from NSE: {str(e)[:100]}")
            self.data = None

    def has_data_on_date(self, date: datetime) -> bool:
        """Check if FII/DII data exists on a specific date."""
        if self.data is None or self.data.empty:
            return False

        # Check if we have any data for this month
        year_month = pd.Period(date, freq='M')
        month_data = self.data[
            (pd.to_datetime(self.data['Date']).dt.to_period('M') == year_month)
        ]
        return len(month_data) > 0

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find last trading day of this month with FII/DII data.

        For monthly aggregation, we search backward to find the last day
        of the month that has data.
        """
        if self.data is None or self.data.empty:
            return None

        # Get year-month
        year_month = pd.Period(date, freq='M')

        # Find all data for this month
        month_data = self.data[
            (pd.to_datetime(self.data['Date']).dt.to_period('M') == year_month)
        ]

        if len(month_data) > 0:
            # Return last date in the month
            last_date = month_data['Date'].max()
            return last_date if pd.notna(last_date) else None

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        """
        Get net FII flow for a specific date.

        This is not typically used for monthly aggregation (which sums).
        """
        if self.data is None or self.data.empty:
            return None

        try:
            date_data = self.data[
                pd.to_datetime(self.data['Date']).dt.date == data_date.date()
            ]

            if len(date_data) > 0:
                # Try to find net flow column
                for col in ['FII Net', 'FII_Net', 'DII Net', 'DII_Net']:
                    if col in date_data.columns:
                        return float(date_data[col].iloc[0])

        except Exception:
            pass

        return None

    def aggregate_to_month(
        self,
        month: str,
        sync_date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate to monthly net FII/DII flows.

        Sum all daily flows for the month.

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
        """
        if self.data is None or self.data.empty:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        # Parse month
        year, month_num = map(int, month.split('-'))
        year_month = pd.Period(f'{year}-{month_num:02d}', freq='M')

        # Get all data for this month
        month_data = self.data[
            (pd.to_datetime(self.data['Date']).dt.to_period('M') == year_month)
        ]

        if len(month_data) == 0:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        # Sum all daily flows
        total_fii = 0
        total_dii = 0
        last_date = None

        for _, row in month_data.iterrows():
            try:
                # Try to find FII net column
                for col in ['FII Net', 'FII_Net', 'FII Equity']:
                    if col in row and pd.notna(row[col]):
                        total_fii += float(row[col])
                        break

                # Try to find DII net column
                for col in ['DII Net', 'DII_Net']:
                    if col in row and pd.notna(row[col]):
                        total_dii += float(row[col])
                        break

                last_date = row['Date']

            except Exception:
                continue

        # Use total FII as the primary value
        return {
            'value': total_fii,
            'data_quality': 'OK' if last_date else 'PARTIAL',
            'source_date': last_date.strftime('%Y-%m-%d') if last_date else None
        }
