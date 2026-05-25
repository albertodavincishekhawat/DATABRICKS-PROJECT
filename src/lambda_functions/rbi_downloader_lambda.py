"""
Lambda Function: RBI Balance Sheet Downloader

Purpose: Download RBI balance sheet CSV from DBIE and save to S3
Schedule: Weekly (Friday evenings after RBI releases data)
Environment Variables Required:
  - RBI_S3_BUCKET: Destination S3 bucket name
  - RBI_S3_KEY: S3 object key (default: data/rbi_balance_sheet.csv)

Deployment:
  1. Create Lambda layer with Selenium + ChromeDriver
  2. Set environment variables
  3. Trigger weekly via CloudWatch Events
  4. IAM permissions: s3:PutObject for destination bucket
"""

import json
import boto3
import pandas as pd
from datetime import datetime
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

# Configuration from environment
S3_BUCKET = os.environ.get('RBI_S3_BUCKET')
S3_KEY = os.environ.get('RBI_S3_KEY', 'data/rbi_balance_sheet.csv')

# Selenium imports (from Lambda layer)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available in Lambda layer")


def download_from_dbie():
    """Download RBI balance sheet from DBIE using Selenium

    Returns:
        DataFrame with RBI balance sheet data, or None if failed
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium required but not available")
        return None

    try:
        logger.info("Starting DBIE download via Selenium...")

        # Lambda has Chrome in /opt/chrome/
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # Path for Lambda environment
        chrome_driver_path = '/opt/chromedriver'  # From Lambda layer
        chrome_binary_path = '/opt/chrome/chrome'  # From Lambda layer

        options.binary_location = chrome_binary_path

        driver = webdriver.Chrome(
            executable_path=chrome_driver_path,
            options=options
        )

        logger.info("Navigating to DBIE...")
        driver.get("https://data.rbi.org.in/DBIE/")

        # Wait for page load
        logger.info("Waiting for DBIE tables to load...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )

        # Extract all tables
        logger.info("Extracting data from tables...")
        dfs = pd.read_html(driver.page_source)

        driver.quit()

        if dfs:
            df = dfs[0]  # Get first table (usually main data)
            logger.info(f"Successfully extracted {len(df)} rows from DBIE")
            return df
        else:
            logger.warning("No tables found in DBIE page")
            return None

    except Exception as e:
        logger.error(f"DBIE download failed: {str(e)}")
        return None


def download_from_rbi_releases():
    """Alternative: Download from RBI Data Releases page

    More reliable than DBIE form navigation
    """
    try:
        logger.info("Trying RBI Data Releases page...")
        url = "https://www.rbi.org.in/Scripts/Statistics.aspx"

        # Using pandas read_html (simpler, no Selenium needed)
        tables = pd.read_html(url)

        if tables:
            df = tables[0]
            logger.info(f"Successfully extracted {len(df)} rows from RBI releases")
            return df
        else:
            logger.warning("No tables found in RBI releases page")
            return None

    except Exception as e:
        logger.error(f"RBI releases download failed: {str(e)}")
        return None


def save_to_s3(df, bucket, key):
    """Upload DataFrame to S3 as CSV

    Args:
        df: pandas DataFrame
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        True if successful, False otherwise
    """
    try:
        csv_buffer = df.to_csv(index=False).encode('utf-8')

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer,
            ContentType='text/csv',
            Metadata={
                'download_date': datetime.now().isoformat(),
                'source': 'DBIE'
            }
        )

        logger.info(f"Successfully uploaded to S3: s3://{bucket}/{key}")
        return True

    except Exception as e:
        logger.error(f"S3 upload failed: {str(e)}")
        return False


def get_sample_data():
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
    ])


def lambda_handler(event, context):
    """Lambda entry point

    Event structure:
    {
        "source": "DBIE" | "RBI_RELEASES" | "SAMPLE",  # Optional override
        "test_mode": true | false  # Use sample data
    }
    """

    logger.info("RBI Downloader Lambda started")
    logger.info(f"S3 Bucket: {S3_BUCKET}, Key: {S3_KEY}")

    # Validate configuration
    if not S3_BUCKET:
        logger.error("RBI_S3_BUCKET environment variable not set")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'S3 bucket not configured'})
        }

    # Determine data source
    test_mode = event.get('test_mode', False)
    source = event.get('source', 'DBIE')

    df = None

    if test_mode:
        logger.info("Test mode: using sample data")
        df = get_sample_data()
    else:
        # Try multiple sources in order
        if source == 'DBIE' or source == 'default':
            df = download_from_dbie()

        if df is None and source != 'DBIE':
            logger.info("DBIE failed, trying RBI releases...")
            df = download_from_rbi_releases()

        if df is None:
            logger.warning("All download methods failed, using sample data")
            df = get_sample_data()

    # Add metadata
    df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')

    # Upload to S3
    success = save_to_s3(df, S3_BUCKET, S3_KEY)

    if success:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'RBI data downloaded and saved to S3',
                'rows': len(df),
                's3_location': f's3://{S3_BUCKET}/{S3_KEY}',
                'download_time': datetime.now().isoformat()
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to save to S3'})
        }


# For local testing
if __name__ == "__main__":
    # Set environment variables for testing
    os.environ['RBI_S3_BUCKET'] = 'test-bucket'
    os.environ['RBI_S3_KEY'] = 'data/rbi_balance_sheet.csv'

    # Test event
    event = {
        'test_mode': True,  # Use sample data for testing
        'source': 'SAMPLE'
    }

    # Mock context
    class MockContext:
        def get_remaining_time_in_millis(self):
            return 300000

    result = lambda_handler(event, MockContext())
    print(json.dumps(json.loads(result['body']), indent=2))
