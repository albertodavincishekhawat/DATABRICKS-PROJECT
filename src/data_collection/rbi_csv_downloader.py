"""
Simple RBI Balance Sheet CSV Downloader
No Lambda, just download and save the file locally
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime


def download_rbi_csv(output_path='src/data_collection/input/rbi_balance_sheet_manual.csv'):
    """
    Download RBI Balance Sheet CSV from DBIE or RBI pages

    Methods:
    1. Try extracting from RBI WSS (Weekly Statistical Supplement)
    2. Try RBI Statistics page
    3. Fallback: User manual download from DBIE

    Args:
        output_path: Where to save the CSV file

    Returns:
        DataFrame if successful, None otherwise
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Method 1: Try RBI WSS page (Balance Sheet specific)
    print("Method 1: Trying RBI WSS (Weekly Statistical Supplement)...")
    try:
        url = "https://www.rbi.org.in/scripts/WSSView.aspx"
        print(f"  Fetching from {url}")
        tables = pd.read_html(url)

        if tables:
            # Look for balance sheet specific table
            for idx, table in enumerate(tables):
                cols_lower = [str(c).lower() for c in table.columns]
                if any(kw in ' '.join(cols_lower) for kw in ['assets', 'liabilities', 'balance']):
                    df = table
                    print(f"✓ Found balance sheet table at index {idx}")
                    print(f"  Rows: {len(df)}, Columns: {list(df.columns)[:3]}...")
                    df.to_csv(output_path, index=False)
                    print(f"✓ Saved to: {output_path}")
                    return df
    except Exception as e:
        print(f"  Not available: {str(e)[:50]}")

    # Method 2: Try RBI Statistics page
    print("\nMethod 2: Trying RBI Statistics page...")
    try:
        url = "https://www.rbi.org.in/Scripts/Statistics.aspx"
        print(f"  Fetching from {url}")
        tables = pd.read_html(url)

        if tables:
            # Use largest table likely to be balance sheet
            df = max(tables, key=len)
            print(f"✓ Found {len(df)} rows in RBI Statistics")
            print(f"  Columns: {list(df.columns)}")
            df.to_csv(output_path, index=False)
            print(f"✓ Saved to: {output_path}")
            return df
    except Exception as e:
        print(f"  Not available: {str(e)[:50]}")

    # Fallback: Manual download instructions
    print("\nMethod 3: Manual download from DBIE (recommended for accurate data)...")
    print("""
Steps to manually download RBI Balance Sheet:
  1. Go to: https://data.rbi.org.in/DBIE/
  2. Navigate to: Money, Banking & Financial System
  3. Find: "RBI Balance Sheet" or "Weekly Statistical Supplement"
  4. Select latest date
  5. Download as CSV
  6. Save as: src/data_collection/input/rbi_balance_sheet_manual.csv
  7. Run this script again to load it

This ensures you get the correct balance sheet data with proper columns:
  - Date, Total Assets, FCA, Notes in Circulation, etc.
    """)

    return None


def load_rbi_csv(csv_path='src/data_collection/input/rbi_balance_sheet_manual.csv'):
    """
    Load RBI Balance Sheet CSV from local file

    Args:
        csv_path: Path to CSV file

    Returns:
        DataFrame if file exists, None otherwise
    """
    csv_path = Path(csv_path)

    if csv_path.exists():
        print(f"Loading from: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        return df
    else:
        print(f"✗ File not found: {csv_path}")
        return None


def get_sample_data():
    """Return sample RBI data for testing"""
    return pd.DataFrame([
        {
            'Date': '2026-05-23',
            'Total_Assets': 615234.56,
            'FCA': 289123.45,
            'Notes_Circulation': 78456.78
        },
        {
            'Date': '2026-05-16',
            'Total_Assets': 614123.45,
            'FCA': 287234.56,
            'Notes_Circulation': 77345.67
        },
        {
            'Date': '2026-05-09',
            'Total_Assets': 613012.34,
            'FCA': 285345.67,
            'Notes_Circulation': 76234.56
        },
        {
            'Date': '2026-05-02',
            'Total_Assets': 611901.23,
            'FCA': 283456.78,
            'Notes_Circulation': 75123.45
        },
    ])


if __name__ == "__main__":
    print("="*70)
    print("RBI BALANCE SHEET CSV DOWNLOADER")
    print("="*70)

    # Try to download
    df = download_rbi_csv()

    # If download failed, try to load existing file
    if df is None:
        print("\nChecking for existing CSV file...")
        df = load_rbi_csv()

    # If still nothing, show sample
    if df is None:
        print("\nUsing sample data (for testing only)")
        df = get_sample_data()

    # Display results
    if df is not None:
        print(f"\n✓ Data loaded successfully!")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nSample data:")
        print(df.head())
