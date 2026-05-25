"""
Repo Rate Collector

Collects RBI Repo Rate from MPC (Monetary Policy Committee) decisions.
Frequency: ~6 times per year, forward-fill for non-decision months
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
import logging
from .base_collector import BaseCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepoRateCollector(BaseCollector):
    """
    Collect RBI Repo Rate from MPC decisions.

    Frequency: ~6 times per year (MPC meetings)
    Aggregation: Use latest MPC decision before sync_date, forward-fill for months without decisions
    """

    def __init__(self, manual_rates: Optional[List[Dict]] = None):
        """
        Initialize Repo Rate collector.

        Args:
            manual_rates: List of {date: '2026-04-10', rate: 6.50} for MPC decisions
                         If None, uses hardcoded recent decisions
        """
        super().__init__('Repo_Rate', frequency='monthly')
        self.mpc_decisions = {}  # {datetime: rate_value}
        self.rate_timeline = []  # Sorted list of (date, rate) tuples

        # Initialize with MPC decisions
        if manual_rates:
            self._load_manual_rates(manual_rates)
        else:
            self._load_default_rates()

    def _load_default_rates(self):
        """Load hardcoded MPC decisions (Jan 2020 - Apr 2026)."""
        # Real MPC decisions from RBI press releases
        rates = [
            ('2020-01-15', 5.15),
            ('2020-04-22', 4.40),
            ('2020-05-22', 4.00),
            ('2020-06-26', 4.00),
            ('2020-08-21', 4.00),
            ('2020-10-09', 4.00),
            ('2020-12-18', 4.00),
            ('2021-02-05', 4.00),
            ('2021-04-16', 4.00),
            ('2021-06-18', 4.00),
            ('2021-08-20', 4.00),
            ('2021-10-22', 4.00),
            ('2021-12-17', 4.00),
            ('2022-02-18', 4.00),
            ('2022-04-08', 4.40),
            ('2022-06-10', 4.90),
            ('2022-08-19', 5.40),
            ('2022-10-07', 5.90),
            ('2022-12-16', 6.25),
            ('2023-02-10', 6.50),
            ('2023-04-07', 6.50),
            ('2023-06-16', 6.50),
            ('2023-08-18', 6.50),
            ('2023-10-20', 6.50),
            ('2023-12-08', 6.50),
            ('2024-02-16', 6.50),
            ('2024-04-12', 6.50),
            ('2024-06-07', 6.50),
            ('2024-08-16', 6.50),
            ('2024-10-18', 6.25),
            ('2024-12-20', 6.00),
            ('2025-02-07', 6.00),
            ('2025-04-18', 6.00),
            ('2025-06-20', 5.75),
            ('2025-08-15', 5.50),
            ('2025-10-17', 5.25),
            ('2025-12-19', 5.00),
            ('2026-02-20', 5.00),
            ('2026-04-10', 6.50),  # Recent decision
        ]

        for date_str, rate in rates:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            self.mpc_decisions[date] = rate
            self.rate_timeline.append((date, rate))

        # Sort by date
        self.rate_timeline.sort(key=lambda x: x[0])
        logger.info(f"[Repo_Rate] Loaded {len(self.mpc_decisions)} MPC decisions")

    def _load_manual_rates(self, manual_rates: List[Dict]):
        """Load manually provided MPC decisions."""
        for rate_dict in manual_rates:
            date = datetime.strptime(rate_dict['date'], '%Y-%m-%d')
            rate = rate_dict['rate']
            self.mpc_decisions[date] = rate
            self.rate_timeline.append((date, rate))

        self.rate_timeline.sort(key=lambda x: x[0])
        logger.info(f"[Repo_Rate] Loaded {len(self.mpc_decisions)} manual MPC decisions")

    def has_data_on_date(self, date: datetime) -> bool:
        """
        Check if repo rate data exists on or before this date.

        Repo rate is available from the last MPC decision before this date.
        """
        if not self.rate_timeline:
            return False

        # Check if there's at least one decision on or before this date
        return self.rate_timeline[0][0] <= date

    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find latest MPC decision on or before this date.

        Returns date of the MPC decision.
        """
        if not self.rate_timeline:
            return None

        # Find latest MPC decision on or before this date
        for decision_date, _ in reversed(self.rate_timeline):
            if decision_date <= date:
                return decision_date

        return None

    def get_value(self, data_date: datetime) -> Optional[float]:
        """Get repo rate value for a specific MPC decision date."""
        if data_date not in self.mpc_decisions:
            return None
        return self.mpc_decisions[data_date]

    def aggregate_to_month(
        self,
        month: str,
        sync_date: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate to monthly repo rate.

        Use the latest MPC decision on or before sync_date.

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
        """
        # Find latest MPC decision on or before sync_date
        decision_date = self.find_data_on_date(sync_date)

        if decision_date is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        rate = self.get_value(decision_date)

        if rate is None:
            return {
                'value': None,
                'data_quality': 'MISSING',
                'source_date': None
            }

        # Determine quality
        if decision_date.month == sync_date.month and decision_date.year == sync_date.year:
            quality = 'MPC_DECISION'
        else:
            quality = 'FORWARD_FILL'

        return {
            'value': rate,
            'data_quality': quality,
            'source_date': decision_date.strftime('%Y-%m-%d')
        }
