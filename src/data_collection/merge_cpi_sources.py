"""
Merge CPI data sources into combined CSV.

Combines:
1. FRED data (Jan 2020 - Mar 2025)
2. MOSPI data (Apr 2025 - Apr 2026)
3. User-provided backfill data (optional)

Output: cpi_combined.csv with all data merged and deduplicated
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_fred_data(filepath='src/data_collection/input/cpi_fred.csv'):
    """Load FRED CPI data (baseline: Jan 2020 - Mar 2025)."""
    try:
        if Path(filepath).exists():
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            logger.info(f"[MERGE] Loaded FRED data: {len(df)} records ({df['Date'].min().date()} to {df['Date'].max().date()})")
            return df
    except Exception as e:
        logger.warning(f"[MERGE] Could not load FRED data: {str(e)[:60]}")

    # Fallback: Extract from existing cpi_combined.csv FRED portion
    try:
        filepath = 'src/data_collection/input/cpi_combined.csv'
        if Path(filepath).exists():
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[df['Source'] == 'FRED'].copy()
            if len(df) > 0:
                logger.info(f"[MERGE] Extracted FRED from combined CSV: {len(df)} records")
                return df
    except Exception as e:
        logger.warning(f"[MERGE] Could not extract FRED: {str(e)[:60]}")

    return None


def load_mospi_data(filepath='src/data_collection/input/cpi_mospi.csv'):
    """Load MOSPI CPI data (Apr 2025 - Apr 2026)."""
    try:
        if Path(filepath).exists():
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            logger.info(f"[MERGE] Loaded MOSPI data: {len(df)} records ({df['Date'].min().date()} to {df['Date'].max().date()})")
            return df
    except Exception as e:
        logger.warning(f"[MERGE] Could not load MOSPI data: {str(e)[:60]}")

    return None


def load_user_data(filepath='src/data_collection/input/cpi_user_provided.csv'):
    """Load optional user-provided CPI backfill data."""
    try:
        if Path(filepath).exists():
            df = pd.read_csv(filepath)
            df['Date'] = pd.to_datetime(df['Date'])
            logger.info(f"[MERGE] Loaded user-provided data: {len(df)} records")
            return df
    except Exception as e:
        logger.debug(f"[MERGE] No user-provided data: {str(e)[:60]}")

    return None


def merge_cpi_sources(fred_df, mospi_df, user_df=None, output_path='src/data_collection/input/cpi_combined.csv'):
    """
    Merge all CPI sources into a single combined CSV.

    Priority (when duplicates exist):
    1. User-provided data (highest priority)
    2. MOSPI data (secondary)
    3. FRED data (baseline)

    Args:
        fred_df: DataFrame with FRED CPI data
        mospi_df: DataFrame with MOSPI CPI data
        user_df: DataFrame with user-provided CPI data (optional)
        output_path: Where to save combined CSV

    Returns:
        DataFrame with merged data
    """
    logger.info("[MERGE] Starting CPI source merge...")

    data_sources = []

    # Start with FRED as baseline
    if fred_df is not None and len(fred_df) > 0:
        fred_df = fred_df[['Date', 'CPI', 'Source']].copy()
        data_sources.append(fred_df)
        logger.info(f"  ✓ FRED baseline: {len(fred_df)} records")

    # Add MOSPI (will override any overlaps)
    if mospi_df is not None and len(mospi_df) > 0:
        mospi_df = mospi_df[['Date', 'CPI', 'Source']].copy()
        data_sources.append(mospi_df)
        logger.info(f"  ✓ MOSPI supplement: {len(mospi_df)} records")

    # Add user-provided (highest priority for overwrites)
    if user_df is not None and len(user_df) > 0:
        user_df = user_df[['Date', 'CPI', 'Source']].copy()
        data_sources.append(user_df)
        logger.info(f"  ✓ User-provided backfill: {len(user_df)} records")

    if len(data_sources) == 0:
        logger.error("[MERGE] No data sources available!")
        return None

    # Combine all sources
    combined = pd.concat(data_sources, ignore_index=True)

    # Remove duplicates (keep last occurrence - user data > MOSPI > FRED)
    combined = combined.sort_values('Date')
    combined = combined.drop_duplicates(subset=['Date'], keep='last')
    combined = combined.sort_values('Date').reset_index(drop=True)

    logger.info(f"[MERGE] Merged data: {len(combined)} unique months")
    logger.info(f"  Date range: {combined['Date'].min().date()} to {combined['Date'].max().date()}")

    # Add Data_Quality column
    combined['Data_Quality'] = 'actual'

    # Save to CSV
    try:
        combined.to_csv(output_path, index=False)
        logger.info(f"✓ Saved combined CSV: {output_path} ({len(combined)} records)")
        return combined
    except Exception as e:
        logger.error(f"Error saving combined CSV: {str(e)}")
        return None


def main():
    """Execute merge operation."""
    print("\n" + "="*70)
    print("CPI Source Merge")
    print("="*70 + "\n")

    # Load data sources
    fred_df = load_fred_data()
    mospi_df = load_mospi_data()
    user_df = load_user_data()

    if fred_df is None and mospi_df is None:
        print("\n✗ No data sources available!")
        return None

    # Merge
    combined = merge_cpi_sources(
        fred_df=fred_df,
        mospi_df=mospi_df,
        user_df=user_df,
        output_path='src/data_collection/input/cpi_combined.csv'
    )

    if combined is not None:
        print(f"\n✓ Success! Merged {len(combined)} CPI records")
        print(f"\nCoverage: {combined['Date'].min().date()} to {combined['Date'].max().date()}")
        print(f"\nSource distribution:")
        print(combined['Source'].value_counts())
        return combined
    else:
        print("\n✗ Merge failed")
        return None


if __name__ == "__main__":
    main()
