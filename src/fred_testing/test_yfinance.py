"""
YFinance Data Availability Test
Test which required data can be obtained from yfinance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

# Data we still need (not on FRED)
DATA_TO_TEST = {
    "USD_INR": {
        "ticker": "USDINR=X",
        "description": "USD/INR Exchange Rate",
        "required_for": "R1 (Monetary System Shift)",
        "frequency": "Daily"
    },
    "Nifty_50": {
        "ticker": "^NSEI",
        "description": "Nifty 50 Index",
        "required_for": "Quarterly Check, R7",
        "frequency": "Daily"
    },
    "Gold_INR": {
        "ticker": "GOLD",  # Might be in INR
        "description": "Gold Price (INR)",
        "required_for": "Quarterly Check",
        "frequency": "Daily"
    },
    "Gold_USD": {
        "ticker": "GC=F",  # Gold futures
        "description": "Gold Price (USD/Troy Oz)",
        "required_for": "Quarterly Check (Reference)",
        "frequency": "Daily"
    },
    "Brent_Crude": {
        "ticker": "BZ=F",  # Brent Crude futures
        "description": "Brent Crude Oil",
        "required_for": "R3 (Commodity/Oil Shock)",
        "frequency": "Daily"
    },
    "Gold_ETF_SBI": {
        "ticker": "SBIN",  # SBI as proxy for ETF
        "description": "SBI Gold ETF proxy",
        "required_for": "Portfolio Rebalancing",
        "frequency": "Daily"
    },
    "Nifty_BeES": {
        "ticker": "NIFTYBEES.NS",
        "description": "Nifty BeES ETF",
        "required_for": "Portfolio Rebalancing",
        "frequency": "Daily"
    },
    "RBI_Repo_Rate": {
        "ticker": None,
        "description": "RBI Repo Rate",
        "required_for": "R1, R2",
        "frequency": "After MPC meetings (not available on yfinance)"
    },
    "FII_DII": {
        "ticker": None,
        "description": "FII/DII Activity",
        "required_for": "R7",
        "frequency": "Daily (not available on yfinance)"
    },
    "RBI_Balance_Sheet": {
        "ticker": None,
        "description": "RBI Balance Sheet",
        "required_for": "R5",
        "frequency": "Weekly (not available on yfinance)"
    },
    "India_CPI": {
        "ticker": None,
        "description": "India CPI",
        "required_for": "R2",
        "frequency": "Monthly (not available on yfinance)"
    }
}

def test_yfinance_ticker(ticker, data_name, max_retries=3):
    """Test if a ticker is available on yfinance"""
    if ticker is None:
        return {
            "status": "NOT_ON_YFINANCE",
            "ticker": None,
            "data_name": data_name,
            "error": "Not available on yfinance (India/NSE specific or system data)"
        }

    for attempt in range(max_retries):
        try:
            print(f"  Testing {ticker}... (attempt {attempt+1}/{max_retries})")

            # Download last 5 days of data
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if data is None or data.empty:
                return {
                    "status": "NOT_FOUND",
                    "ticker": ticker,
                    "data_name": data_name,
                    "error": "No data returned from yfinance"
                }

            # Get latest value
            latest_date = data.index[-1]
            latest_close = data['Close'].iloc[-1]

            # Get series info
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info if hasattr(ticker_obj, 'info') else {}

            return {
                "status": "AVAILABLE",
                "ticker": ticker,
                "data_name": data_name,
                "latest_date": str(latest_date.date()),
                "latest_value": float(latest_close),
                "rows_available": len(data),
                "currency": info.get('currency', 'Unknown'),
                "market_cap": info.get('marketCap', 'N/A')
            }

        except Exception as e:
            error_msg = str(e)
            if "No data found" in error_msg or "not found" in error_msg.lower():
                return {
                    "status": "NOT_FOUND",
                    "ticker": ticker,
                    "data_name": data_name,
                    "error": f"Ticker not found: {ticker}"
                }

            if attempt == max_retries - 1:
                return {
                    "status": "ERROR",
                    "ticker": ticker,
                    "data_name": data_name,
                    "error": error_msg
                }

    return {
        "status": "ERROR",
        "ticker": ticker,
        "data_name": data_name,
        "error": "Max retries exceeded"
    }

def main():
    print("=" * 100)
    print("YFINANCE DATA AVAILABILITY TEST")
    print(f"Test Date: {datetime.now()}")
    print("=" * 100)

    results = []
    available_count = 0
    not_available_count = 0

    for data_name, data_info in DATA_TO_TEST.items():
        print(f"\n📊 {data_name}")
        print(f"   Description: {data_info['description']}")
        print(f"   Required for: {data_info['required_for']}")
        print(f"   Frequency: {data_info['frequency']}")

        result = test_yfinance_ticker(data_info['ticker'], data_name)
        results.append(result)

        if result['status'] == 'AVAILABLE':
            print(f"   ✓ AVAILABLE")
            print(f"     Latest: {result['latest_value']} ({result['latest_date']})")
            print(f"     Data points: {result['rows_available']}")
            available_count += 1
        elif result['status'] == 'NOT_ON_YFINANCE':
            print(f"   ⚠️  NOT ON YFINANCE")
            print(f"     Reason: {result['error']}")
            not_available_count += 1
        else:
            print(f"   ✗ {result['status']}")
            print(f"     Error: {result['error']}")

    # Summary
    print("\n" + "=" * 100)
    print("YFINANCE AVAILABILITY SUMMARY")
    print("=" * 100)

    summary_df = pd.DataFrame(results)

    # Count by status
    available = len(summary_df[summary_df['status'] == 'AVAILABLE'])
    not_on_yf = len(summary_df[summary_df['status'] == 'NOT_ON_YFINANCE'])
    errors = len(summary_df[summary_df['status'].isin(['NOT_FOUND', 'ERROR'])])

    print(f"\n✓ Available on yfinance: {available}")
    print(f"⚠️  Not on yfinance: {not_on_yf}")
    print(f"✗ Errors/Not found: {errors}")

    # Show available
    available_df = summary_df[summary_df['status'] == 'AVAILABLE']
    if len(available_df) > 0:
        print("\nAvailable on yfinance:")
        for _, row in available_df.iterrows():
            print(f"  • {row['data_name']} ({row['ticker']}) - Latest: {row['latest_value']} ({row['latest_date']})")

    # Save results
    results_csv = "src/fred_testing/output/yfinance_availability.csv"
    summary_df.to_csv(results_csv, index=False)
    print(f"\n✓ Results saved to: {results_csv}")

    results_json = "src/fred_testing/output/yfinance_availability.json"
    with open(results_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"✓ JSON saved to: {results_json}")

if __name__ == "__main__":
    import os
    os.makedirs("src/fred_testing/output", exist_ok=True)

    print("Installing yfinance if needed...")
    import subprocess
    import sys

    try:
        import yfinance
    except ImportError:
        print("Installing yfinance...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])

    main()
