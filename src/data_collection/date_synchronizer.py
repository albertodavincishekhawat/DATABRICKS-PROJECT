"""
Date Synchronization Engine

Finds synchronized dates across all 10 data sources despite different frequencies.
Uses progressive date shifting: search backward from month-end until ALL 10 sources have data.
"""

import pandas as pd
from datetime import datetime, timedelta
import calendar
from typing import Dict, Tuple, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateSynchronizer:
    """
    Find synchronized dates across all 10 data sources.

    Strategy: For each month, search backward from month-end until all 10 sources
    have data available. First date where all 10 have data = sync_date for that month.
    """

    def __init__(self, start_year=2020, start_month=1, end_year=2026, end_month=4):
        """
        Initialize DateSynchronizer for 76-month period.

        Args:
            start_year: Start year (2020)
            start_month: Start month (1)
            end_year: End year (2026)
            end_month: End month (4)
        """
        self.start_year = start_year
        self.start_month = start_month
        self.end_year = end_year
        self.end_month = end_month

        # Generate 76 month-end dates
        self.month_ends = self._generate_month_ends()
        logger.info(f"Generated {len(self.month_ends)} month-end dates")

        # Results
        self.sync_dates = {}  # date -> {sync_date, data_dates per source}
        self.complete_months = []  # Months where all 10 sources have data
        self.incomplete_months = []  # Months missing ≥1 source

    def _generate_month_ends(self) -> List[datetime]:
        """Generate month-end dates, adjusted for weekends."""
        dates = []

        for year in range(self.start_year, self.end_year + 1):
            month_limit = 13 if year < self.end_year else self.end_month + 1
            start = self.start_month if year == self.start_year else 1

            for month in range(start, month_limit):
                # Get last day of month
                last_day = calendar.monthrange(year, month)[1]
                date = datetime(year, month, last_day)

                # Adjust for weekends (Sat→Fri, Sun→Fri)
                if date.weekday() == 5:  # Saturday
                    date = date - timedelta(days=1)
                elif date.weekday() == 6:  # Sunday
                    date = date - timedelta(days=2)

                dates.append(date)

        return dates

    def find_sync_date(
        self,
        month_date: datetime,
        collectors: Dict,
        max_search_days: int = 10
    ) -> Tuple[Optional[datetime], Dict]:
        """
        Find sync date for a given month.

        Search backward from month_date up to max_search_days.
        Stop when ALL 10 sources have data available.

        Args:
            month_date: Month-end date to search from
            collectors: Dict of {source_name: collector_instance}
            max_search_days: Max days to search backward

        Returns:
            Tuple of (sync_date, data_dates_per_source) or (None, {}) if incomplete
        """

        for search_offset in range(0, max_search_days + 1):
            candidate_date = month_date - timedelta(days=search_offset)

            # Try to get data from all sources for this candidate date
            data_available = {}

            for source_name, collector in collectors.items():
                data_date = collector.find_data_on_date(candidate_date)
                if data_date is not None:
                    data_available[source_name] = data_date

            # Check if all 10 sources have data
            if len(data_available) == 10:
                logger.info(
                    f"Month {month_date.strftime('%Y-%m')}: "
                    f"COMPLETE - sync_date={candidate_date.strftime('%Y-%m-%d')}"
                )
                return candidate_date, data_available

        # No sync date found within search window
        logger.warning(
            f"Month {month_date.strftime('%Y-%m')}: "
            f"INCOMPLETE - only {len(data_available)}/10 sources available"
        )
        return None, {}

    def synchronize(self, collectors: Dict) -> pd.DataFrame:
        """
        Synchronize all 76 months across all 10 sources.

        Args:
            collectors: Dict of {source_name: collector_instance}

        Returns:
            DataFrame with sync results for all months
        """

        results = []

        for month_end in self.month_ends:
            month_str = month_end.strftime('%Y-%m')

            sync_date, data_dates = self.find_sync_date(month_end, collectors)

            if sync_date is not None:
                # Complete month
                self.complete_months.append(month_str)
                results.append({
                    'Month': month_str,
                    'MonthEnd': month_end.strftime('%Y-%m-%d'),
                    'SyncDate': sync_date.strftime('%Y-%m-%d'),
                    'Status': 'COMPLETE',
                    'SourcesAvailable': len(data_dates),
                    'DataDates': data_dates
                })
            else:
                # Incomplete month
                self.incomplete_months.append(month_str)
                results.append({
                    'Month': month_str,
                    'MonthEnd': month_end.strftime('%Y-%m-%d'),
                    'SyncDate': None,
                    'Status': 'INCOMPLETE',
                    'SourcesAvailable': len(data_dates),
                    'DataDates': data_dates
                })

        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Log summary
        logger.info("\n" + "="*70)
        logger.info("SYNCHRONIZATION SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Months: {len(self.month_ends)}")
        logger.info(f"Complete Months: {len(self.complete_months)} ({100*len(self.complete_months)/len(self.month_ends):.1f}%)")
        logger.info(f"Incomplete Months: {len(self.incomplete_months)} ({100*len(self.incomplete_months)/len(self.month_ends):.1f}%)")
        logger.info("="*70)

        return results_df

    def get_complete_sync_dates(self) -> Dict[str, Dict]:
        """
        Get sync dates only for COMPLETE months (all 10 sources available).

        Returns:
            Dict of {month: {sync_date, data_dates_per_source}}
        """
        return {
            month: self.sync_dates[month]
            for month in self.complete_months
            if month in self.sync_dates
        }

    def generate_quality_report(self) -> str:
        """Generate human-readable quality report."""
        report = []
        report.append("\n" + "="*70)
        report.append("DATA SYNCHRONIZATION QUALITY REPORT")
        report.append("="*70)
        report.append(f"\nTotal Months (Jan 2020 - Apr 2026): {len(self.month_ends)}")
        report.append(f"✓ COMPLETE Months (All 10 sources): {len(self.complete_months)}")
        report.append(f"✗ INCOMPLETE Months (Missing ≥1 source): {len(self.incomplete_months)}")
        report.append(f"\nCompleteness: {100*len(self.complete_months)/len(self.month_ends):.1f}%")
        report.append("\nAlgorithm will run on: COMPLETE months only")
        report.append("="*70 + "\n")

        return "\n".join(report)
