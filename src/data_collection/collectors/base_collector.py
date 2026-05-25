"""
Base Collector Class

Abstract base for all data source collectors.
Each collector implements source-specific logic to find and aggregate data.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.

    Each collector handles one data source and implements:
    1. find_data_on_date(date): Find data on/before this date
    2. aggregate_to_month(month, sync_date): Aggregate to monthly value
    """

    def __init__(self, name: str, frequency: str):
        """
        Initialize collector.

        Args:
            name: Source name (e.g., 'CPI', 'NIFTY50')
            frequency: Data frequency ('monthly', 'weekly', 'daily')
        """
        self.name = name
        self.frequency = frequency
        self.data_cache = {}  # Cache data to avoid refetching

    @abstractmethod
    def find_data_on_date(self, date: datetime) -> Optional[datetime]:
        """
        Find if data is available on or before this date.

        Args:
            date: Target date to search from

        Returns:
            Actual date of data if found, None if not available
        """
        pass

    @abstractmethod
    def get_value(self, data_date: datetime) -> Optional[float]:
        """
        Get the value for a specific data date.

        Args:
            data_date: Date to retrieve data for

        Returns:
            Data value or None if not available
        """
        pass

    @abstractmethod
    def aggregate_to_month(self, month: str, sync_date: datetime) -> Dict[str, Any]:
        """
        Aggregate source data to a monthly value.

        Args:
            month: Month string (YYYY-MM)
            sync_date: The synchronized date for this month

        Returns:
            Dict with {value, data_quality, source_date}
        """
        pass

    def search_backward(
        self,
        date: datetime,
        max_days: int = 5
    ) -> Optional[datetime]:
        """
        Search backward from date up to max_days to find data.

        Try: date, -1, -2, -3, -4, -5 days

        Args:
            date: Starting date
            max_days: Max days to search backward

        Returns:
            First date where data found, or None
        """
        for offset in range(0, max_days + 1):
            candidate = date - timedelta(days=offset)
            if self.has_data_on_date(candidate):
                return candidate
        return None

    @abstractmethod
    def has_data_on_date(self, date: datetime) -> bool:
        """
        Check if data exists on a specific date.

        Args:
            date: Date to check

        Returns:
            True if data exists, False otherwise
        """
        pass

    def log_status(self, message: str):
        """Log collector status."""
        logger.info(f"[{self.name}] {message}")