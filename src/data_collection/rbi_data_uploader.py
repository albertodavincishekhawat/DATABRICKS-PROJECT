"""
RBI Balance Sheet Data Uploader

Helper script to upload real RBI Balance Sheet data from manual DBIE downloads.

Steps to get real RBI Balance Sheet data:
1. Go to: https://data.rbi.org.in/DBIE/
2. Login (free account required)
3. Navigate to: Money, Banking & Financial System
4. Find: "RBI Balance Sheet" or "Weekly Statistical Supplement"
5. Select date range and download as CSV
6. Run this script to format and use the data

Expected columns in downloaded CSV:
- Date (or Reporting_Date)
- Total_Assets (or Total Assets)
- FCA (Foreign Currency Assets)
- Notes_Circulation (or Notes in Circulation)
"""

import pandas as pd
from pathlib import Path


def validate_rbi_csv(csv_path):
    """Validate that CSV has required RBI Balance Sheet columns"""
    required_cols = ['Total_Assets', 'FCA', 'Notes_Circulation']
    df = pd.read_csv(csv_path)

    # Normalize column names
    df.columns = [
        col.strip().lower().replace(' ', '_')
        for col in df.columns
    ]

    # Check for date column
    date_cols = [col for col in df.columns if 'date' in col]
    if not date_cols:
        raise ValueError(f"No date column found. Columns: {df.columns.tolist()}")

    # Check for balance sheet columns
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {df.columns.tolist()}")

    return True


def upload_rbi_csv(csv_path, output_path='src/data_collection/input/rbi_balance_sheet_manual.csv'):
    """
    Upload and format RBI CSV for use in scrapers

    Args:
        csv_path: Path to downloaded RBI CSV from DBIE
        output_path: Where to save for scrapers to use

    Returns:
        True if successful
    """
    try:
        print(f"Reading RBI CSV from: {csv_path}")
        df = pd.read_csv(csv_path)

        # Normalize columns
        df.columns = [
            col.strip().lower().replace(' ', '_')
            for col in df.columns
        ]

        # Validate
        validate_rbi_csv(csv_path)

        # Save to expected location
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        print(f"✓ Uploaded {len(df)} rows")
        print(f"✓ Saved to: {output_path}")
        print(f"  Columns: {df.columns.tolist()}")
        print(f"  Date range: {df.iloc[0, 0]} to {df.iloc[-1, 0]}")

        return True

    except Exception as e:
        print(f"✗ Upload failed: {str(e)}")
        return False


def show_instructions():
    """Show instructions for downloading real RBI data"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   RBI BALANCE SHEET DATA UPLOADER                          ║
╚════════════════════════════════════════════════════════════════════════════╝

Currently using: Sample data (12 weeks, for testing)
To use REAL RBI Balance Sheet data:

1. Download from DBIE:
   - Go to: https://data.rbi.org.in/DBIE/
   - Login with free account
   - Navigate to: Money, Banking & Financial System
   - Find: "RBI Balance Sheet" or "Weekly Statistical Supplement"
   - Select date range
   - Download as CSV

2. Run upload script:
   python3 src/data_collection/rbi_data_uploader.py \\
       --csv /path/to/downloaded/rbi_balance_sheet.csv

3. Script will:
   - Validate CSV structure
   - Normalize column names
   - Save to: src/data_collection/input/rbi_balance_sheet_manual.csv
   - Scraper will auto-detect and use it

Expected columns in CSV:
  - Date (any date column name)
  - Total_Assets
  - FCA (Foreign Currency Assets)
  - Notes_Circulation (Notes in Circulation)

After upload, run scrapers again to use real data:
  python3 src/data_collection/scrapers.py

Any other columns from DBIE will be preserved and passed through.
    """)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--csv" and len(sys.argv) > 2:
            csv_file = sys.argv[2]
            upload_rbi_csv(csv_file)
        else:
            print(f"Usage: python3 {sys.argv[0]} --csv <path_to_csv>")
    else:
        show_instructions()
