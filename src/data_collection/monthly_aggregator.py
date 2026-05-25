"""
Monthly Data Aggregator

Orchestrates all 10 data collectors and generates aligned monthly CSVs.
Enforces requirement: only includes months where ALL 10 sources have data.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Tuple

from src.data_collection.date_synchronizer import DateSynchronizer
from src.data_collection.collectors.yfinance_collector import YFinanceCollector
from src.data_collection.collectors.cpi_collector import CPICollector
from src.data_collection.collectors.repo_rate_collector import RepoRateCollector
from src.data_collection.collectors.fii_dii_collector import FIIDIICollector
from src.data_collection.collectors.rbi_balance_sheet_collector import RBIBalanceSheetCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonthlyAggregator:
    """
    Aggregate all 10 data sources to monthly frequency and align to sync dates.

    Output: 11 CSVs
    - 10 parameter CSVs (one per data source)
    - 1 master_dates.csv (sync date tracking + completeness)
    """

    def __init__(self, output_dir: str = 'src/data_collection/output/monthly'):
        """Initialize aggregator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all 10 collectors
        self.collectors = self._initialize_collectors()
        self.num_sources = len(self.collectors)

        logger.info(f"Initialized {self.num_sources} data collectors")

    def _initialize_collectors(self) -> Dict:
        """Initialize all 10 data collectors."""
        collectors = {}

        # 6 YFinance sources
        yf_sources = [
            'NIFTY50', 'USDINR', 'GOLD_INR', 'GOLD_USD', 'BRENT_CRUDE', 'NIFTYBEES'
        ]

        for source in yf_sources:
            try:
                collectors[source] = YFinanceCollector(source)
            except Exception as e:
                logger.error(f"Failed to initialize {source}: {str(e)[:50]}")

        # CPI (FRED)
        try:
            collectors['CPI'] = CPICollector()
        except Exception as e:
            logger.error(f"Failed to initialize CPI: {str(e)[:50]}")

        # Repo Rate (MPC)
        try:
            collectors['Repo_Rate'] = RepoRateCollector()
        except Exception as e:
            logger.error(f"Failed to initialize Repo_Rate: {str(e)[:50]}")

        # FII/DII (NSE)
        try:
            collectors['FII_DII'] = FIIDIICollector()
        except Exception as e:
            logger.error(f"Failed to initialize FII_DII: {str(e)[:50]}")

        # RBI Balance Sheet
        try:
            collectors['RBI_Balance_Sheet'] = RBIBalanceSheetCollector()
        except Exception as e:
            logger.error(f"Failed to initialize RBI_Balance_Sheet: {str(e)[:50]}")

        return collectors

    def aggregate(self) -> Tuple[int, int]:
        """
        Aggregate all sources to monthly frequency and generate CSVs.

        Returns:
            Tuple of (complete_months, incomplete_months)
        """
        logger.info("\n" + "="*70)
        logger.info("MONTHLY DATA AGGREGATION")
        logger.info("="*70)

        # Initialize DateSynchronizer
        sync = DateSynchronizer()
        logger.info(f"Synchronizing {len(sync.month_ends)} months...")

        # Find sync dates for all months
        results_df = sync.synchronize(self.collectors)

        # Separate complete and incomplete months
        complete_data = {}
        incomplete_data = {}

        for _, row in results_df.iterrows():
            month = row['Month']

            if row['Status'] == 'COMPLETE':
                complete_data[month] = row
            else:
                incomplete_data[month] = row

        logger.info(f"\nComplete months: {len(complete_data)}")
        logger.info(f"Incomplete months: {len(incomplete_data)}")

        # Generate CSVs for complete months only
        self._generate_csvs(complete_data)

        # Generate master dates CSV
        self._generate_master_dates_csv(results_df, complete_data)

        # Generate quality report
        self._generate_quality_report(sync, complete_data, incomplete_data)

        return len(complete_data), len(incomplete_data)

    def _generate_csvs(self, complete_data: Dict):
        """
        Generate one CSV per data source.

        Only includes complete months (all 10 sources available).
        """
        logger.info("\n" + "="*70)
        logger.info("GENERATING PARAMETER CSVs")
        logger.info("="*70)

        # For each source, create a CSV with one row per complete month
        for source_name, collector in self.collectors.items():
            rows = []

            # Process in chronological order
            for month in sorted(complete_data.keys()):
                month_result = complete_data[month]
                sync_date = datetime.strptime(month_result['SyncDate'], '%Y-%m-%d')

                # Aggregate to monthly value
                agg_result = collector.aggregate_to_month(month, sync_date)

                rows.append({
                    'Date': month_result['SyncDate'],
                    'Value': agg_result.get('value'),
                    'Data_Quality': agg_result.get('data_quality', 'UNKNOWN'),
                    'Source_Date': agg_result.get('source_date')
                })

            # Create DataFrame and save
            df = pd.DataFrame(rows)
            csv_path = self.output_dir / f"{source_name.lower()}_monthly.csv"
            df.to_csv(csv_path, index=False)

            logger.info(f"✓ {source_name}: {len(df)} rows → {csv_path.name}")

    def _generate_master_dates_csv(self, sync_results: pd.DataFrame, complete_data: Dict):
        """
        Generate master_dates.csv with sync information.

        Tracks sync dates and completeness for all 76 months.
        """
        csv_path = self.output_dir / 'master_dates.csv'

        # Select relevant columns and save
        master_df = sync_results[[
            'Month', 'MonthEnd', 'SyncDate', 'Status', 'SourcesAvailable'
        ]].copy()

        master_df.to_csv(csv_path, index=False)

        logger.info(f"✓ master_dates.csv: {len(master_df)} rows → {csv_path.name}")

    def _generate_quality_report(
        self,
        sync: DateSynchronizer,
        complete_data: Dict,
        incomplete_data: Dict
    ):
        """Generate human-readable quality report."""
        report_path = self.output_dir / 'data_quality_report.txt'

        with open(report_path, 'w') as f:
            f.write(sync.generate_quality_report())

            f.write("\nCOMPLETE MONTHS (Algorithm can run on these):\n")
            for month in sorted(complete_data.keys()):
                f.write(f"  ✓ {month}\n")

            if incomplete_data:
                f.write("\nINCOMPLETE MONTHS (Missing ≥1 source):\n")
                for month in sorted(incomplete_data.keys()):
                    f.write(f"  ✗ {month}\n")

        logger.info(f"✓ Quality report: {report_path.name}")


def main():
    """Run monthly data aggregation."""
    logger.info("#"*70)
    logger.info("# MONTHLY DATA COLLECTION & AGGREGATION")
    logger.info("# Jan 2020 - Apr 2026 (76 months)")
    logger.info("#"*70)

    aggregator = MonthlyAggregator()
    complete_count, incomplete_count = aggregator.aggregate()

    logger.info("\n" + "="*70)
    logger.info("AGGREGATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Complete months: {complete_count}")
    logger.info(f"Incomplete months: {incomplete_count}")
    logger.info(f"Output directory: {aggregator.output_dir}")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()
