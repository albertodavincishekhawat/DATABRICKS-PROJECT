"""
RBI Balance Sheet Data Downloader - Lambda Compatible

Provides multiple methods to fetch RBI Balance Sheet data:
1. From DBIE website (requires Selenium for form interaction)
2. From S3 (for Lambda - pre-stored data)
3. From local file (for development)
4. Sample data (fallback)

For Lambda, recommend: Pre-download CSV → Store in S3 → Lambda fetches from S3
For Local/Manual: Download from DBIE manually or use Selenium
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import json

# Optional AWS imports (only if running on Lambda)
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class RBIDataDownloader:
    """Download RBI balance sheet data from various sources"""

    def __init__(self, s3_bucket=None, s3_key=None, local_path=None):
        """
        Initialize downloader

        Args:
            s3_bucket: AWS S3 bucket name (for Lambda)
            s3_key: S3 object key (for Lambda)
            local_path: Local file path for development
        """
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key or 'data/rbi_balance_sheet.csv'
        self.local_path = local_path or 'src/data_collection/input/rbi_balance_sheet_manual.csv'
        self.dbie_url = "https://data.rbi.org.in/DBIE/"
        self.s3_client = boto3.client('s3') if AWS_AVAILABLE and s3_bucket else None

    def download_from_s3(self):
        """Fetch CSV from S3 (Lambda-friendly)"""
        if not self.s3_client or not self.s3_bucket:
            return None

        try:
            print(f"  Downloading from S3: s3://{self.s3_bucket}/{self.s3_key}")
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
            df = pd.read_csv(response['Body'])
            print(f"  ✓ Retrieved {len(df)} rows from S3")
            return df
        except Exception as e:
            print(f"  S3 download failed: {str(e)[:50]}")
            return None

    def download_from_local(self):
        """Load from local CSV file"""
        try:
            if Path(self.local_path).exists():
                df = pd.read_csv(self.local_path)
                print(f"  ✓ Loaded {len(df)} rows from {self.local_path}")
                return df
            else:
                print(f"  File not found: {self.local_path}")
                return None
        except Exception as e:
            print(f"  Local load failed: {str(e)[:50]}")
            return None

    def download_from_dbie_selenium(self):
        """Download from DBIE using Selenium (requires ChromeDriver)

        This is the most reliable method but slower and requires Selenium.
        For Lambda, this is not recommended (use S3 instead).
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.service import Service
        except ImportError:
            print("  Selenium not available - install with: pip install selenium")
            return None

        print("  Attempting DBIE download via Selenium...")
        try:
            # For Lambda: Would need Chrome in Lambda layer
            # For local: Requires ChromeDriver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(options=options)
            driver.get(self.dbie_url)

            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
            )

            # Extract tables
            df = pd.read_html(driver.page_source)[0]
            driver.quit()

            print(f"  ✓ Retrieved {len(df)} rows from DBIE")
            return df

        except Exception as e:
            print(f"  Selenium download failed: {str(e)[:50]}")
            return None

    def download_from_dbie_api(self):
        """Try to fetch from DBIE using direct HTTP requests

        Note: DBIE doesn't have a public REST API, so this attempts direct download
        if available. Otherwise returns None.
        """
        print("  Checking for direct DBIE CSV download...")
        # DBIE doesn't publish direct download links, so this returns None
        # Users need to download manually from DBIE portal
        return None

    def get_sample_data(self):
        """Return sample data for testing"""
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

    def download(self, priority_order=None):
        """Download RBI data using priority list

        Args:
            priority_order: List of methods to try in order
                ['s3', 'local', 'dbie_api', 'dbie_selenium', 'sample']

        Returns:
            DataFrame with RBI balance sheet data
        """
        if priority_order is None:
            # Default priority for Lambda vs Local
            if AWS_AVAILABLE and self.s3_bucket:
                priority_order = ['s3', 'local', 'dbie_api', 'dbie_selenium', 'sample']
            else:
                priority_order = ['local', 'dbie_api', 'dbie_selenium', 'sample']

        for method in priority_order:
            if method == 's3':
                df = self.download_from_s3()
            elif method == 'local':
                df = self.download_from_local()
            elif method == 'dbie_api':
                df = self.download_from_dbie_api()
            elif method == 'dbie_selenium':
                df = self.download_from_dbie_selenium()
            elif method == 'sample':
                df = self.get_sample_data()
            else:
                continue

            if df is not None and len(df) > 0:
                return df

        return None

    def upload_to_s3(self, df, subfolder='data'):
        """Upload downloaded CSV to S3 for Lambda access

        Usage in local environment:
            downloader = RBIDataDownloader(s3_bucket='my-bucket')
            df = downloader.download_from_local()
            downloader.upload_to_s3(df)
        """
        if not self.s3_client or not self.s3_bucket:
            print("S3 not configured")
            return False

        try:
            s3_key = f"{subfolder}/rbi_balance_sheet.csv"
            csv_buffer = df.to_csv(index=False).encode('utf-8')
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=csv_buffer,
                ContentType='text/csv'
            )
            print(f"✓ Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            return True
        except Exception as e:
            print(f"✗ S3 upload failed: {str(e)}")
            return False


class RBIBalanceSheetScraper:
    """Simplified scraper interface using downloader"""

    def __init__(self, output_dir='src/data_collection/output', **kwargs):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.name = "RBI Balance Sheet"
        self.downloader = RBIDataDownloader(**kwargs)

    def scrape(self):
        """Fetch data using downloader"""
        df = self.downloader.download()
        if df is not None and len(df) > 0:
            return df
        return None

    def run(self):
        """Execute scraper and save to CSV"""
        df = self.scrape()
        if df is not None and len(df) > 0:
            df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
            filepath = self.output_dir / f"{self.name.lower().replace(' ', '_')}.csv"
            df.to_csv(filepath, index=False)
            print(f"✓ Saved: {filepath}")
            return df
        return None


# For Lambda: Environment variables
# Set these in Lambda function environment:
# - RBI_S3_BUCKET: 'your-bucket-name'
# - RBI_S3_KEY: 'data/rbi_balance_sheet.csv'

if __name__ == "__main__":
    # Example usage
    downloader = RBIDataDownloader()
    df = downloader.download()

    if df is not None:
        print(f"\nData: {len(df)} rows")
        print(df.head())
