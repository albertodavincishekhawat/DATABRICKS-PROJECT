"""
Monthly Data Collection Orchestrator (Jan 2020 - Apr 2026)
Frequency Hierarchy: Monthly → Weekly → Daily
Aligned to same month-end dates with intelligent shifting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonthlyDateGenerator:
    """Generate month-end dates with intelligent shifting for holidays/weekends"""

    @staticmethod
    def get_month_end_dates(start_year=2020, start_month=1, end_year=2026, end_month=4):
        """
        Generate month-end dates from start to end
        Handles weekends automatically (Fri if Sat/Sun)
        """
        dates = []

        for year in range(start_year, end_year + 1):
            month_limit = 13 if year < end_year else end_month + 1

            for month in range(start_month if year == start_year else 1, month_limit):
                # Get last day of month
                last_day = calendar.monthrange(year, month)[1]
                date = datetime(year, month, last_day)

                # If Saturday, move to Friday
                if date.weekday() == 5:  # Saturday
                    date = date - timedelta(days=1)
                # If Sunday, move to Friday
                elif date.weekday() == 6:  # Sunday
                    date = date - timedelta(days=2)

                dates.append(date)

        return dates

    @staticmethod
    def get_shifted_date(base_date, max_shift=5):
        """
        For a base date, return the date or shifted dates to find data
        Try: base_date, +1, +2, +3, +4, +5 days
        """
        shifted = []
        for shift in range(max_shift + 1):
            shifted.append(base_date + timedelta(days=shift))
        return shifted


class MonthlyDataCollector:
    """Collect data by frequency hierarchy for each month"""

    def __init__(self, output_dir='src/data_collection/output/monthly'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Date generator
        self.date_gen = MonthlyDateGenerator()
        self.month_ends = self.date_gen.get_month_end_dates()

        # Data storage
        self.monthly_data = {}  # month_end_date → {parameter: value}
        self.data_quality = {}  # month_end_date → {source: status}

        logger.info(f"Generated {len(self.month_ends)} month-end dates")
        logger.info(f"Date range: {self.month_ends[0].date()} to {self.month_ends[-1].date()}")

    def collect_monthly_sources(self):
        """
        STEP 1: Collect MONTHLY frequency sources
        - India CPI (from FRED)
        - RBI Repo Rate (from press releases, with forward-fill)
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 1: MONTHLY SOURCES (Lowest Frequency)")
        logger.info("="*70)

        # Load FRED CPI data
        try:
            from pandas_datareader import data as web
            logger.info("Fetching India CPI from FRED...")

            cpi_data = {}
            # Get CPI data (monthly)
            cpi_df = web.DataReader('INDCPIALLMINMEI', 'fred', start='2020-01-01', end='2026-04-30')
            cpi_df = cpi_df.reset_index()
            cpi_df.columns = ['Date', 'CPI']

            # Convert to dict keyed by year-month
            for _, row in cpi_df.iterrows():
                date = pd.to_datetime(row['Date'])
                year_month = (date.year, date.month)
                cpi_data[year_month] = row['CPI']

            logger.info(f"✓ Loaded {len(cpi_data)} CPI data points")

            # For each month-end, get CPI for that month
            for month_end in self.month_ends:
                year_month = (month_end.year, month_end.month)

                if year_month not in self.monthly_data:
                    self.monthly_data[month_end.date()] = {}
                if month_end.date() not in self.data_quality:
                    self.data_quality[month_end.date()] = {}

                if year_month in cpi_data:
                    self.monthly_data[month_end.date()]['CPI'] = cpi_data[year_month]
                    self.data_quality[month_end.date()]['CPI'] = 'OK'
                else:
                    self.monthly_data[month_end.date()]['CPI'] = None
                    self.data_quality[month_end.date()]['CPI'] = 'MISSING'

        except Exception as e:
            logger.warning(f"FRED CPI fetch failed: {str(e)[:100]}")

        # RBI Repo Rate (MPC decisions ~6x/year, forward-fill others)
        try:
            logger.info("Getting RBI Repo Rate (MPC decisions with forward-fill)...")

            # TODO: Scrape actual MPC decisions
            # For now, use last known rate
            last_known_rate = 6.50
            last_decision_date = datetime(2026, 4, 10)

            for month_end in self.month_ends:
                if month_end.date() not in self.monthly_data:
                    self.monthly_data[month_end.date()] = {}

                self.monthly_data[month_end.date()]['Repo_Rate'] = last_known_rate
                self.data_quality[month_end.date()]['Repo_Rate'] = 'FORWARD_FILL'

            logger.info(f"✓ Set {len(self.month_ends)} repo rate values (with forward-fill)")

        except Exception as e:
            logger.warning(f"RBI Repo Rate collection failed: {str(e)[:100]}")

    def collect_weekly_sources(self):
        """
        STEP 2: Collect WEEKLY frequency sources, aggregate to MONTHLY
        - RBI Balance Sheet (get month-end Friday)
        - FII/DII (aggregate to monthly sum)
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 2: WEEKLY SOURCES (Intermediate Frequency)")
        logger.info("="*70)

        # RBI Balance Sheet - use the real data we already have
        try:
            logger.info("Loading RBI Balance Sheet (real data)...")
            rbi_csv = 'src/data_collection/input/rbi_balance_sheet_real.csv'

            if Path(rbi_csv).exists():
                rbi_df = pd.read_csv(rbi_csv)
                rbi_df['Date'] = pd.to_datetime(rbi_df['Date']).dt.date

                for month_end in self.month_ends:
                    if month_end.date() not in self.monthly_data:
                        self.monthly_data[month_end.date()] = {}

                    # Find closest date in RBI data for this month
                    month = month_end.month
                    year = month_end.year

                    month_data = rbi_df[
                        (pd.to_datetime(rbi_df['Date']).dt.month == month) &
                        (pd.to_datetime(rbi_df['Date']).dt.year == year)
                    ]

                    if len(month_data) > 0:
                        row = month_data.iloc[0]  # Get first (most recent) entry
                        self.monthly_data[month_end.date()]['Total_Assets'] = row['Total_Assets']
                        self.monthly_data[month_end.date()]['FCA'] = row['FCA']
                        self.monthly_data[month_end.date()]['Notes_Circulation'] = row['Notes_Circulation']
                        self.data_quality[month_end.date()]['RBI_Balance_Sheet'] = 'OK'
                    else:
                        self.data_quality[month_end.date()]['RBI_Balance_Sheet'] = 'MISSING'

                logger.info(f"✓ Loaded RBI Balance Sheet data")

        except Exception as e:
            logger.warning(f"RBI Balance Sheet load failed: {str(e)[:100]}")

        # FII/DII - placeholder (needs daily data aggregation)
        logger.info("Setting up FII/DII aggregation...")
        for month_end in self.month_ends:
            # TODO: Aggregate daily FII/DII to monthly
            self.monthly_data[month_end.date()]['FII_Net'] = 0  # Placeholder
            self.monthly_data[month_end.date()]['DII_Net'] = 0  # Placeholder
            self.data_quality[month_end.date()]['FII_DII'] = 'PENDING'

    def collect_daily_sources(self):
        """
        STEP 3: Collect DAILY frequency sources, aggregate to MONTHLY (month-end close)
        - YFinance: NIFTY50, USDINR, GOLD(INR), GOLD(USD), Brent Crude, NIFTYBEES
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 3: DAILY SOURCES (Highest Frequency)")
        logger.info("="*70)

        import yfinance as yf

        tickers = {
            'NIFTY50': '^NSEI',
            'USDINR': 'USDINR=X',
            'GOLD_INR': 'GOLD',
            'GOLD_USD': 'GC=F',
            'BRENT_CRUDE': 'BZ=F',
            'NIFTYBEES': 'NIFTYBEES.NS',
        }

        for param_name, ticker in tickers.items():
            logger.info(f"Fetching {param_name} ({ticker})...")

            try:
                # Fetch daily data
                data = yf.download(ticker, start='2020-01-01', end='2026-04-30', progress=False)

                if data.empty:
                    logger.warning(f"  ⚠ No data for {ticker}")
                    continue

                # For each month-end, find closest trading day
                for month_end in self.month_ends:
                    if month_end.date() not in self.monthly_data:
                        self.monthly_data[month_end.date()] = {}

                    # Try to find data on month-end date or +1, +2 days
                    shifted_dates = self.date_gen.get_shifted_date(month_end, max_shift=5)

                    found = False
                    for shifted_date in shifted_dates:
                        if shifted_date.date() in data.index:
                            close_price = data.loc[shifted_date.date(), 'Close']
                            self.monthly_data[month_end.date()][param_name] = float(close_price)

                            if shifted_date.date() != month_end.date():
                                self.data_quality[month_end.date()][param_name] = f'SHIFTED_{(shifted_date - month_end).days}d'
                            else:
                                self.data_quality[month_end.date()][param_name] = 'OK'
                            found = True
                            break

                    if not found:
                        self.data_quality[month_end.date()][param_name] = 'MISSING'

                logger.info(f"  ✓ Processed {param_name}")

            except Exception as e:
                logger.warning(f"  ✗ {param_name} failed: {str(e)[:100]}")

    def generate_final_csvs(self):
        """
        STEP 4: Generate final CSV for each parameter
        One CSV per data parameter, aligned to same month-end dates
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 4: GENERATE FINAL CSVs")
        logger.info("="*70)

        # Identify all parameters
        all_params = set()
        for month_data in self.monthly_data.values():
            all_params.update(month_data.keys())

        logger.info(f"Found {len(all_params)} parameters: {sorted(all_params)}")

        # Create one CSV per parameter
        for param in sorted(all_params):
            rows = []

            for month_end in self.month_ends:
                month_date = month_end.date()

                if month_date in self.monthly_data:
                    value = self.monthly_data[month_date].get(param, None)
                    status = self.data_quality[month_date].get(param, 'UNKNOWN')

                    rows.append({
                        'Date': month_date.isoformat(),
                        'Value': value,
                        'Data_Status': status
                    })

            # Create DataFrame and save
            df = pd.DataFrame(rows)

            csv_name = f"{param.lower()}_monthly.csv"
            csv_path = self.output_dir / csv_name
            df.to_csv(csv_path, index=False)

            logger.info(f"✓ {csv_name}: {len(df)} rows")

        # Generate master dates CSV with quality summary
        master_rows = []
        for month_end in self.month_ends:
            month_date = month_end.date()
            status_dict = self.data_quality.get(month_date, {})

            missing = [p for p, s in status_dict.items() if s == 'MISSING']
            shifted = [p for p, s in status_dict.items() if 'SHIFTED' in s]

            master_rows.append({
                'Date': month_date.isoformat(),
                'Day_of_Week': calendar.day_name[month_end.weekday()],
                'Complete_Data': len(missing) == 0,
                'Missing_Sources': ', '.join(missing) if missing else 'None',
                'Shifted_Sources': ', '.join(shifted) if shifted else 'None',
            })

        master_df = pd.DataFrame(master_rows)
        master_path = self.output_dir / 'master_dates.csv'
        master_df.to_csv(master_path, index=False)
        logger.info(f"✓ master_dates.csv: {len(master_df)} rows")

        return df, master_df

    def generate_quality_report(self):
        """Generate data quality metrics"""
        logger.info("\n" + "="*70)
        logger.info("DATA QUALITY REPORT")
        logger.info("="*70)

        total_months = len(self.month_ends)

        # Count complete months
        complete_months = 0
        for month_date in self.monthly_data.keys():
            status_dict = self.data_quality.get(month_date, {})
            missing = [p for p, s in status_dict.items() if s == 'MISSING']
            if len(missing) == 0:
                complete_months += 1

        # Count shifted dates
        shifted_count = 0
        for month_dict in self.data_quality.values():
            shifted_count += sum(1 for s in month_dict.values() if 'SHIFTED' in s)

        # Report
        logger.info(f"\nTotal Months: {total_months}")
        logger.info(f"Complete Data Months: {complete_months} ({100*complete_months/total_months:.1f}%)")
        logger.info(f"Shifted Dates (data moved +1/+2 days): {shifted_count}")

        # Parameter availability
        all_params = set()
        for month_data in self.monthly_data.values():
            all_params.update(month_data.keys())

        logger.info(f"\nParameter Availability:")
        for param in sorted(all_params):
            available = sum(1 for month_date in self.monthly_data
                          if month_date in self.monthly_data and self.monthly_data[month_date].get(param) is not None)
            pct = 100 * available / total_months if available > 0 else 0
            logger.info(f"  {param:20} {available:3}/{total_months} months ({pct:5.1f}%)")

    def run(self):
        """Execute full collection pipeline"""
        logger.info("\n" + "#"*70)
        logger.info("# MONTHLY DATA COLLECTION - FREQUENCY HIERARCHY")
        logger.info("# Jan 2020 - Apr 2026 (76 months)")
        logger.info("#"*70)

        self.collect_monthly_sources()
        self.collect_weekly_sources()
        self.collect_daily_sources()
        self.generate_final_csvs()
        self.generate_quality_report()

        logger.info("\n✓ Data collection complete!")
        logger.info(f"Output directory: {self.output_dir}")


if __name__ == "__main__":
    collector = MonthlyDataCollector()
    collector.run()
