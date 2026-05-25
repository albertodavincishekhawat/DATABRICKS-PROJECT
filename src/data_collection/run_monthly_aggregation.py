#!/usr/bin/env python3
"""
Runner Script: Monthly Data Collection & Aggregation

Usage:
    python3 src/data_collection/run_monthly_aggregation.py

This script:
1. Initializes all 10 data collectors
2. Finds synchronized dates across all sources
3. Generates monthly CSVs for complete months only
4. Creates quality report
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_collection.monthly_aggregator import MonthlyAggregator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run monthly data aggregation."""
    try:
        aggregator = MonthlyAggregator()
        complete_count, incomplete_count = aggregator.aggregate()

        logger.info("\n" + "="*70)
        logger.info("AGGREGATION COMPLETE")
        logger.info("="*70)
        logger.info(f"✓ Complete months: {complete_count}")
        logger.info(f"✗ Incomplete months: {incomplete_count}")
        logger.info(f"\nOutput directory: {aggregator.output_dir}")
        logger.info("="*70)

        # Print next steps
        logger.info("\nNEXT STEPS:")
        logger.info("1. Check CSVs in output/monthly/")
        logger.info("2. Review data_quality_report.txt for completeness")
        logger.info("3. Algorithm will run on complete months only")

        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
