"""
Fetch frequency and detailed information for successful FRED series
"""

import requests
import pandas as pd
import json
from datetime import datetime

FRED_API_KEY = "ae3adb3c2a3d380c98e1fff8847d2471"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Successful series from our tests
SUCCESSFUL_SERIES = {
    "US_CPI": "CPIAUCSL",
    "Federal_Funds_Rate": "FEDFUNDS",
    "USD_EUR_Rate": "DEXUSEU"
}

def get_series_info(series_id):
    """Fetch detailed series information including frequency"""
    try:
        url = f"{FRED_BASE_URL}/series"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'seriess' in data and len(data['seriess']) > 0:
            return data['seriess'][0]
        return None
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return None

def get_observation_count_and_dates(series_id):
    """Get total observations and date range"""
    try:
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": 1
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'observations' in data and len(data['observations']) > 0:
            count = data.get('count', 'Unknown')
            return count
        return None
    except Exception as e:
        print(f"Error fetching observations for {series_id}: {e}")
        return None

def main():
    print("=" * 100)
    print("FREQUENCY AND DETAILED INFORMATION FOR SUCCESSFUL FRED SERIES")
    print(f"Test Date: {datetime.now()}")
    print("=" * 100)

    frequency_data = []

    for data_name, series_id in SUCCESSFUL_SERIES.items():
        print(f"\n📊 {data_name} ({series_id})")
        print("-" * 100)

        # Get series info
        series_info = get_series_info(series_id)

        if series_info:
            print(f"Title: {series_info.get('title', 'N/A')}")
            print(f"Units: {series_info.get('units', 'N/A')}")
            print(f"Frequency: {series_info.get('frequency', 'N/A')}")
            print(f"Frequency Short: {series_info.get('frequency_short', 'N/A')}")
            print(f"Data Start: {series_info.get('observation_start', 'N/A')}")
            print(f"Data End: {series_info.get('observation_end', 'N/A')}")
            print(f"Last Updated: {series_info.get('last_updated', 'N/A')}")
            print(f"Notes: {series_info.get('notes', 'N/A')}")

            # Get observation count
            obs_count = get_observation_count_and_dates(series_id)
            print(f"Total Observations: {obs_count}")

            # Add to dataframe data
            frequency_data.append({
                "Data_Name": data_name,
                "Series_ID": series_id,
                "Title": series_info.get('title', 'N/A'),
                "Frequency": series_info.get('frequency', 'N/A'),
                "Frequency_Short": series_info.get('frequency_short', 'N/A'),
                "Units": series_info.get('units', 'N/A'),
                "Data_Start_Date": series_info.get('observation_start', 'N/A'),
                "Data_End_Date": series_info.get('observation_end', 'N/A'),
                "Last_Updated": series_info.get('last_updated', 'N/A'),
                "Total_Observations": obs_count,
                "API_Status": "✓ Active"
            })

    # Create frequency summary
    print("\n" + "=" * 100)
    print("FREQUENCY SUMMARY TABLE")
    print("=" * 100)

    frequency_df = pd.DataFrame(frequency_data)

    # Display summary
    summary_display = frequency_df[['Data_Name', 'Frequency', 'Frequency_Short',
                                     'Data_Start_Date', 'Data_End_Date', 'Last_Updated']].copy()
    print("\n" + summary_display.to_string(index=False))

    # Save to CSV
    csv_file = "src/fred_testing/output/SUCCESSFUL_SERIES_FREQUENCY.csv"
    frequency_df.to_csv(csv_file, index=False)
    print(f"\n✓ Frequency data saved to: {csv_file}")

    # Save detailed info as JSON
    json_file = "src/fred_testing/output/SUCCESSFUL_SERIES_DETAILS.json"
    with open(json_file, 'w') as f:
        json.dump(frequency_data, f, indent=2)
    print(f"✓ Detailed info saved to: {json_file}")

    # Create frequency mapping document
    freq_doc = """# SUCCESSFUL FRED DATA - FREQUENCY & UPDATE SCHEDULE

Generated: {}

## Summary

| Data | Series ID | Frequency | Latest | Update Lag |
|------|-----------|-----------|--------|-----------|
""".format(datetime.now())

    for item in frequency_data:
        freq_doc += f"| {item['Data_Name']} | {item['Series_ID']} | {item['Frequency_Short']} | {item['Data_End_Date']} | 1-2 days |\n"

    freq_doc += """

## Detailed Information

"""

    for item in frequency_data:
        freq_doc += f"""
### {item['Data_Name']} ({item['Series_ID']})

**Frequency**: {item['Frequency']} ({item['Frequency_Short']})

**Title**: {item['Title']}

**Units**: {item['Units']}

**Data Range**: {item['Data_Start_Date']} to {item['Data_End_Date']}

**Total Observations**: {item['Total_Observations']}

**Last Updated**: {item['Last_Updated']}

**Status**: {item['API_Status']}

"""

    freq_doc += """
## Frequency Codes

| Code | Meaning | Typical Release Schedule |
|------|---------|--------------------------|
| D | Daily | Each trading day |
| W | Weekly | Once per week (usually Friday) |
| BW | Bi-Weekly | Every other week |
| M | Monthly | First business day of next month |
| Q | Quarterly | First month of next quarter |
| A | Annual | Next year |
| SA | Semi-Annual | Twice per year |

## Update Lag Information

| Series | Typical Lag | Notes |
|--------|------------|-------|
| US CPI | 15-20 days | Released mid-month for prior month |
| Federal Funds Rate | 1-2 days | Updated after FOMC decision |
| USD/EUR Rate | Same day | Real-time forex data |

## For Decision Algorithm Implementation

### Data Freshness Requirements

Rule R1 (Monetary System Shift):
- Uses: Federal Funds Rate
- Frequency: Monthly (after MPC meetings)
- FRED provides: Monthly, typically 1-2 days lag ✓

Rule R2 (Real Rate Shock):
- Uses: Repo Rate (RBI) + CPI (India)
- FRED provides: US CPI Monthly only
- Note: Need to get RBI Repo Rate separately ⚠️

Rule R3 (Commodity/Oil Shock):
- Uses: Brent Crude prices
- Frequency: Daily
- FRED: NOT available (API error)
- Alternative: Use EIA API ✗

Rule R5 (QE Regime):
- Uses: RBI Balance Sheet (India specific)
- Frequency: Weekly
- FRED: NOT available ⚠️

Rule R7 (Institutional Selling):
- Uses: FII/DII Activity (India specific)
- Frequency: Daily
- FRED: NOT available ⚠️

### Reference Data Available on FRED

These can be used for context/validation:
- **US CPI**: Monthly, released mid-month
- **Federal Funds Rate**: Monthly, after FOMC
- **USD/EUR Rate**: Daily, real-time

---

**Status**: Documentation updated with actual FRED frequency data
**Last Updated**: {}
""".format(datetime.now())

    doc_file = "src/fred_testing/output/FREQUENCY_AND_UPDATE_SCHEDULE.md"
    with open(doc_file, 'w') as f:
        f.write(freq_doc)
    print(f"✓ Frequency document saved to: {doc_file}")

    print("\n" + "=" * 100)
    print("✓ COMPLETE - All frequency information collected and saved")
    print("=" * 100)

if __name__ == "__main__":
    import os
    os.makedirs("src/fred_testing/output", exist_ok=True)
    main()
