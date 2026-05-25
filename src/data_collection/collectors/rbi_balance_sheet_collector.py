"""
RBI Balance Sheet Collector

Collects RBI Balance Sheet data (Total Assets, FCA, Notes Circulation).
Frequency: Weekly (usually Fridays)
Source: DBIE manual download or realistic sample data
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
from pathlib import Path
import logging
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RBIBalanceSheetCollector(BaseCollector):
    """
    Collect weekly RBI Balance Sheet data.

    Frequency: Weekly (usually Fridays)
    Aggregation: Use the last Friday of the month (closest to month-end)
    Source: User-downloaded DBIE CSV or realistic sample data
    """

    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize RBI Balance Sheet collector.

        Args:
            csv_path: Path to RBI Balance Sheet CSV from DBIE
                     If None, looks for default paths and falls back to sample data
        """
        super().__init__('RBI_Balance_Sheet', frequency='weekly')
        self.data = None
        self.csv_path = csv_path

        # Try to load real data
        self._load_data()

    def _load_data(self):
        """Load RBI Balance Sheet data from CSV."""
        # Try paths in order
        paths_to_try = [
            self.csv_path,
            'src/data_collection/input/rbi_balance_sheet_historical.csv',
            'src/data_collection/input/rbi_balance_sheet_real.csv',
            'src/data_collection/input/rbi_balance_sheet_manual.csv',
        ]

        for path in paths_to_try:
            if path is None:
                continue

            if Path(path).exists():
                try:
                    df = pd.read_csv(path)
                    df['Date'] = pd.to_datetime(df['Date'])
                    self.data = df.sort_values('Date')

                    logger.info(f"[RBI_Balance_Sheet] Loaded from {path} ({len(self.data)} records)")
                    return

                except Exception as e:
                    logger.warning(f"[RBI_Balance_Sheet] Error loading {path}: {str(e)[:50]}")

        # Fallback: Create sample data
        logger.warning("[RBI_Balance_Sheet] No real data found, using sample data")
        self._create_sample_data()

    def _create_sample_data(self):
        """Create realistic sample RBI Balance Sheet data for testing."""
        today = datetime.now()
        weeks_back = 12

        data = []
        base_assets = 615000.0
        base_fca = 289000.0
        base_notes = 78000.0

        for i in range(weeks_back):
            data.append({
                'Date': (today - timedelta(days=i*7)).strftime('%Y-%m-%d'),
                'Total_Assets': base_assets - (i*800),
                'FCA': base_fca - (i*350),
                'Notes_Circulation': base_notes - (i*250),
            })

        self.data = pd.DataFrame(data)
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        logger.info(f"[RBI_Balance_Sheet] Created sample data ({len(self.data)} records)")

    def has_data_on_date(self, date: datetime) -> bool:
        """Check if RBI Balance Sheet data exists on or before this date."""
        if self.data is None or self.data.empty:
            return False

        # Check if we have data on or before this date
        available_dates = self.data[self.data['Date'] <= date]
        return len(available_dates) > 0

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find last RBI Balance Sheet data on or before this date.

        RBI releases balance sheet weekly (usually Friday).
        Search backward for the latest available Friday.
        """
        if self.data is None or self.data.empty:
            return None

        # Find data on or before this date
        available = self.data[self.data['Date'] <= date]

        if len(available) > 0:
            return available['Date'].max()

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        """
        Get total assets for a specific date.

        Note: This returns Total_Assets. The aggregator can choose which
        balance sheet item to use (Total_Assets, FCA, or Notes_Circulation).
        """
        if self.data is None or self.data.empty:
            return None

        try:
            date_data = self.data[self.data['Date'].dt.date == data_date.date()]

            if len(date_data) > 0 and 'Total_Assets' in date_data.columns:
                return float(date_data['Total_Assets'].iloc[0])

        except Exception:
            pass

        return None

    def aggregate_to_month(
        self,
        month: str,
        sync_date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate to monthly RBI Balance Sheet values.

        Use the last available Friday of the month (closest to month-end).

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
            Note: Returns Total_Assets value and other BS items in sub-dict
        """
        if self.data is None or self.data.empty:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None,
                'total_assets': None,
                'fca': None,
                'notes_circulation': None
            }

        # Find last data on or before sync_date
        data_date = self.find_data_on_date(sync_date)

        if data_date is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None,
                'total_assets': None,
                'fca': None,
                'notes_circulation': None
            }

        # Get balance sheet values for this date
        date_data = self.data[self.data['Date'] == data_date]

        if len(date_data) == 0:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None,
                'total_assets': None,
                'fca': None,
                'notes_circulation': None
            }

        row = date_data.iloc[0]

        return {
            'value': float(row.get('Total_Assets', None)) if 'Total_Assets' in row else None,
            'data_quality': 'OK',
            'source_date': data_date.strftime('%Y-%m-%d'),
            'total_assets': float(row.get('Total_Assets', None)) if 'Total_Assets' in row else None,
            'fca': float(row.get('FCA', None)) if 'FCA' in row else None,
            'notes_circulation': float(row.get('Notes_Circulation', None)) if 'Notes_Circulation' in row else None
        }
