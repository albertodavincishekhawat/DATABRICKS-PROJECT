"""
Quick Test - Fetch 10 most recent values from FRED for key series
Use this to quickly verify API connectivity and data availability
"""

import requests
import pandas as pd
from datetime import datetime
import json

FRED_API_KEY = "ae3adb3c2a3d380c98e1fff8847d2471"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Key series to test
TEST_SERIES = {
    "Brent_Crude": "DCOILBRENTD",
    "Gold_Price_USD": "GOLDAMND",
    "US_CPI": "CPIAUCSL",
    "Federal_Funds_Rate": "FEDFUNDS",
    "USD_EUR_Rate": "DEXUSEU"
}


def fetch_latest_values(series_id: str, limit: int = 10):
    """Fetch latest values from FRED"""
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": limit,
            "sort_order": "desc"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'observations' not in data:
            return None

        # Convert to DataFrame and reverse for chronological order
        obs = data['observations']
        obs.reverse()

        df = pd.DataFrame(obs)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        return df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def main():
    print("=" * 100)
    print("QUICK FRED API TEST - Fetching Latest 10 Values")
    print(f"Time: {datetime.now()}")
    print("=" * 100)

    results = {}

    for data_name, series_id in TEST_SERIES.items():
        print(f"\n{data_name} ({series_id})")
        print("-" * 100)

        df = fetch_latest_values(series_id, limit=10)

        if df is not None and len(df) > 0:
            print(f"✓ SUCCESS - Retrieved {len(df)} values\n")

            # Display data
            display_df = df[['date', 'value']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            print(display_df.to_string(index=False))

            # Save to CSV
            csv_filename = f"src/fred_testing/output/{data_name}_latest_10.csv"
            df[['date', 'value']].to_csv(csv_filename, index=False)
            print(f"\n✓ Saved to: {csv_filename}")

            results[data_name] = {
                "status": "SUCCESS",
                "rows": len(df),
                "latest_date": str(df.iloc[-1]['date'].date()),
                "latest_value": float(df.iloc[-1]['value']),
                "csv_file": csv_filename
            }
        else:
            print(f"✗ FAILED - Could not retrieve data\n")
            results[data_name] = {
                "status": "FAILED",
                "error": "No data returned"
            }

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    summary_df = pd.DataFrame(results).T
    print("\n" + summary_df.to_string())

    # Save summary
    summary_csv = "src/fred_testing/output/quick_test_summary.csv"
    summary_df.to_csv(summary_csv)
    print(f"\n✓ Summary saved to: {summary_csv}")

    # Summary JSON
    summary_json = "src/fred_testing/output/quick_test_summary.json"
    with open(summary_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"✓ JSON summary saved to: {summary_json}")

    print("\n" + "=" * 100)
    print("✓ Quick test complete!")
    print("=" * 100)


if __name__ == "__main__":
    import os
    os.makedirs("src/fred_testing/output", exist_ok=True)
    main()
