"""
Unified YFinance Data Fetcher
Fetches 6 required data points from Yahoo Finance for portfolio algorithm
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

# All tickers required by the decision algorithm
YFINANCE_TICKERS = {
    'USDINR': {
        'ticker': 'USDINR=X',
        'description': 'USD/INR Exchange Rate',
        'required_for': 'R1 (Monetary System Shift)',
        'frequency': 'Daily'
    },
    'NIFTY50': {
        'ticker': '^NSEI',
        'description': 'Nifty 50 Index',
        'required_for': 'Quarterly Check, R7 (Institutional Selling)',
        'frequency': 'Daily'
    },
    'GOLD_INR': {
        'ticker': 'GOLD',
        'description': 'Gold Price (INR) - Physical',
        'required_for': 'Quarterly Check',
        'frequency': 'Daily'
    },
    'GOLD_USD': {
        'ticker': 'GC=F',
        'description': 'Gold Price (USD/Troy Oz)',
        'required_for': 'Reference for international gold price',
        'frequency': 'Daily'
    },
    'BRENT_CRUDE': {
        'ticker': 'BZ=F',
        'description': 'Brent Crude Oil Futures',
        'required_for': 'R3 (Commodity/Oil Shock)',
        'frequency': 'Daily'
    },
    'NIFTY_BEES': {
        'ticker': 'NIFTYBEES.NS',
        'description': 'Nifty BeES ETF',
        'required_for': 'Portfolio Rebalancing (NAV)',
        'frequency': 'Daily'
    }
}


class YFinanceFetcher:
    """Unified fetcher for all YFinance data sources"""

    def __init__(self, output_dir='src/data_collection/output', months_back=12):
        """
        Initialize fetcher

        Args:
            output_dir: Directory to save CSV/Parquet files
            months_back: Number of months of historical data to fetch (default: 12)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)  # ~12 months

        self.start_date = start_date.strftime('%Y-%m-%d')
        self.end_date = end_date.strftime('%Y-%m-%d')
        self.fetch_time = datetime.now()

        print(f"YFinance Fetcher initialized")
        print(f"  Date range: {self.start_date} to {self.end_date}")
        print(f"  Output directory: {self.output_dir}")

    def fetch_ticker(self, ticker_name, ticker_symbol, retry_count=3):
        """
        Fetch data for a single ticker with retry logic

        Args:
            ticker_name: Human-readable name
            ticker_symbol: Yahoo Finance ticker symbol
            retry_count: Number of retries on failure

        Returns:
            DataFrame with historical data or None if failed
        """
        for attempt in range(retry_count):
            try:
                print(f"  Fetching {ticker_name} ({ticker_symbol})...", end=' ')

                data = yf.download(
                    ticker_symbol,
                    start=self.start_date,
                    end=self.end_date,
                    progress=False
                )

                if data is None or data.empty:
                    print(f"✗ No data returned")
                    return None

                print(f"✓ {len(data)} rows")

                # Add metadata columns
                data['ticker'] = ticker_symbol
                data['ticker_name'] = ticker_name
                data['fetch_date'] = self.fetch_time.strftime('%Y-%m-%d %H:%M:%S')

                return data

            except Exception as e:
                if attempt == retry_count - 1:
                    print(f"✗ Error: {str(e)[:50]}")
                    return None
                print(f"⚠️  Retry {attempt + 1}/{retry_count - 1}...", end=' ')

    def fetch_all(self):
        """
        Fetch data for all tickers

        Returns:
            Dictionary with {ticker_name: DataFrame}
        """
        print("\n" + "=" * 100)
        print("FETCHING YFINANCE DATA")
        print(f"Fetch Time: {self.fetch_time}")
        print("=" * 100 + "\n")

        all_data = {}

        for ticker_name, ticker_info in YFINANCE_TICKERS.items():
            print(f"{ticker_name}")
            print(f"  Description: {ticker_info['description']}")
            print(f"  Required for: {ticker_info['required_for']}")

            data = self.fetch_ticker(
                ticker_name,
                ticker_info['ticker']
            )

            if data is not None:
                all_data[ticker_name] = data
            print()

        return all_data

    def save_individual_csv(self, all_data):
        """Save each ticker's data to individual CSV file"""
        print("=" * 100)
        print("SAVING INDIVIDUAL CSV FILES")
        print("=" * 100 + "\n")

        csv_files = {}

        for ticker_name, data in all_data.items():
            csv_file = self.output_dir / f"{ticker_name}_data.csv"
            data.to_csv(csv_file)
            csv_files[ticker_name] = str(csv_file)
            print(f"✓ {csv_file.name} ({len(data)} rows)")

        return csv_files

    def save_combined_csv(self, all_data):
        """Save all data combined into single CSV"""
        print("\nCreating combined CSV...")

        combined_data = []

        for ticker_name, data in all_data.items():
            # Flatten the dataframe
            df = data.copy()
            df['Date'] = df.index
            df = df.reset_index(drop=True)

            # Select core columns that exist
            cols_to_keep = ['Date', 'ticker', 'ticker_name', 'Close', 'Open', 'High', 'Low', 'Volume', 'fetch_date']
            df_clean = df[cols_to_keep].copy()
            df_clean.columns = ['Date', 'Ticker', 'Ticker_Name', 'Close', 'Open', 'High', 'Low', 'Volume', 'Fetch_Date']

            combined_data.append(df_clean)

        combined_df = pd.concat(combined_data, ignore_index=True)
        combined_df['Date'] = pd.to_datetime(combined_df['Date'])
        combined_df = combined_df.sort_values('Date').reset_index(drop=True)

        csv_file = self.output_dir / "yfinance_all_data.csv"
        combined_df.to_csv(csv_file, index=False)
        print(f"✓ {csv_file.name} ({len(combined_df)} rows)")

        return str(csv_file)

    def save_parquet(self, all_data):
        """Save all data to Parquet format (for Lambda/production)"""
        print("\nCreating Parquet file...")

        combined_data = []

        for ticker_name, data in all_data.items():
            df = data.copy()
            df['Date'] = df.index
            df = df.reset_index(drop=True)

            cols_to_keep = ['Date', 'ticker', 'ticker_name', 'Close', 'Open', 'High', 'Low', 'Volume', 'fetch_date']
            df_clean = df[cols_to_keep].copy()
            df_clean.columns = ['Date', 'Ticker', 'Ticker_Name', 'Close', 'Open', 'High', 'Low', 'Volume', 'Fetch_Date']

            # Convert to float64
            for col in ['Close', 'Open', 'High', 'Low', 'Volume']:
                df_clean[col] = df_clean[col].astype('float64')

            combined_data.append(df_clean)

        combined_df = pd.concat(combined_data, ignore_index=True)
        combined_df['Date'] = pd.to_datetime(combined_df['Date'])
        combined_df = combined_df.sort_values('Date').reset_index(drop=True)

        parquet_file = self.output_dir / "yfinance_all_data.parquet"
        combined_df.to_parquet(parquet_file, index=False, engine='pyarrow')
        print(f"✓ {parquet_file.name} ({len(combined_df)} rows)")

        return str(parquet_file)

    def save_summary_json(self, all_data):
        """Save summary statistics and metadata"""
        print("\nCreating summary JSON...")

        summary = {
            'fetch_time': self.fetch_time.isoformat(),
            'date_range': {
                'start': self.start_date,
                'end': self.end_date
            },
            'tickers': {}
        }

        for ticker_name, data in all_data.items():
            ticker_info = YFINANCE_TICKERS[ticker_name]
            latest = data.iloc[-1]
            earliest = data.iloc[0]

            # Get date string from index
            latest_date = latest.name if hasattr(latest.name, 'strftime') else latest.name
            earliest_date = earliest.name if hasattr(earliest.name, 'strftime') else earliest.name

            if hasattr(latest_date, 'strftime'):
                latest_date_str = latest_date.strftime('%Y-%m-%d')
                earliest_date_str = earliest_date.strftime('%Y-%m-%d')
            else:
                latest_date_str = str(latest_date)
                earliest_date_str = str(earliest_date)

            summary['tickers'][ticker_name] = {
                'symbol': ticker_info['ticker'],
                'description': ticker_info['description'],
                'required_for': ticker_info['required_for'],
                'rows_fetched': len(data),
                'date_range': {
                    'start': earliest_date_str,
                    'end': latest_date_str
                },
                'latest_close': float(latest['Close']),
                'latest_date': latest_date_str
            }

        json_file = self.output_dir / "yfinance_summary.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ {json_file.name}")

        return str(json_file)

    def run(self):
        """Execute full fetch and save pipeline"""
        print("\n" + "=" * 100)
        print("YFINANCE UNIFIED DATA FETCHER")
        print("=" * 100 + "\n")

        # Fetch all data
        all_data = self.fetch_all()

        if not all_data:
            print("\n✗ ERROR: No data fetched. Check ticker symbols and internet connection.")
            return False

        print("\n" + "=" * 100)
        print("SAVING DATA")
        print("=" * 100 + "\n")

        # Save in multiple formats
        self.save_individual_csv(all_data)
        csv_combined = self.save_combined_csv(all_data)
        parquet_file = self.save_parquet(all_data)
        summary_json = self.save_summary_json(all_data)

        # Print completion summary
        print("\n" + "=" * 100)
        print("✓ COMPLETE")
        print("=" * 100)
        print(f"\nFetched: {len(all_data)} tickers")
        print(f"Total rows: {sum(len(df) for df in all_data.values())}")
        print(f"\nFiles saved:")
        print(f"  • Individual CSVs: {len(all_data)} files")
        print(f"  • Combined CSV: {csv_combined}")
        print(f"  • Parquet: {parquet_file}")
        print(f"  • Summary: {summary_json}")
        print("\n✓ Ready for algorithm testing")

        return True


def main():
    """Main entry point"""
    fetcher = YFinanceFetcher(months_back=12)
    success = fetcher.run()

    if not success:
        exit(1)


if __name__ == "__main__":
    main()
