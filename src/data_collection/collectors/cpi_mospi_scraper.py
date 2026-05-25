"""
MOSPI CPI Scraper

Fetches latest Consumer Price Index data from MOSPI (Ministry of Statistics)
https://mospi.gov.in/

Official source for India's CPI data
"""

import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_mospi_cpi(retry_attempts=3):
    """
    Scrape latest CPI data from MOSPI website.

    Returns:
        DataFrame with columns: Date, CPI, Source
        or None if scraping fails
    """

    urls_to_try = [
        'https://mospi.gov.in/cpi-page',
        'https://mospi.gov.in/documents/statistics-documents/cpi',
        'https://mospi.gov.in/',
    ]

    for attempt in range(retry_attempts):
        for url in urls_to_try:
            try:
                logger.info(f"Attempt {attempt + 1}: Fetching {url}...")

                response = requests.get(
                    url,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Try to find CPI tables
                tables = soup.find_all('table')

                if tables:
                    for table in tables:
                        df = parse_cpi_table(table)
                        if df is not None and len(df) > 0:
                            logger.info(f"✓ Found CPI data: {len(df)} records")
                            df['Source'] = 'MOSPI'
                            return df

                logger.info("  No CPI table found in this page")

            except Exception as e:
                logger.debug(f"  Error with {url}: {str(e)[:80]}")
                time.sleep(1)

        if attempt < retry_attempts - 1:
            logger.info(f"  Retrying in 2 seconds...")
            time.sleep(2)

    logger.warning("MOSPI scraping failed - no CPI data retrieved")
    return None


def parse_cpi_table(table):
    """
    Parse HTML table for CPI data.

    Looks for columns containing month/year and CPI value

    Returns:
        DataFrame or None
    """
    try:
        rows = table.find_all('tr')

        if len(rows) < 2:
            return None

        data = []
        headers = []

        # Get headers from first row
        for th in rows[0].find_all(['th', 'td']):
            headers.append(th.get_text(strip=True).lower())

        # Skip if no clear month/date column
        month_idx = None
        cpi_idx = None

        for i, h in enumerate(headers):
            if 'month' in h or 'date' in h or 'period' in h:
                month_idx = i
            if 'cpi' in h or 'index' in h:
                cpi_idx = i

        if month_idx is None or cpi_idx is None:
            return None

        # Parse data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])

            if len(cells) <= max(month_idx, cpi_idx):
                continue

            try:
                month_str = cells[month_idx].get_text(strip=True)
                cpi_str = cells[cpi_idx].get_text(strip=True)

                # Try to parse month/year and CPI value
                date = parse_month_string(month_str)
                cpi = float(cpi_str.replace(',', ''))

                if date and cpi > 0:
                    data.append({
                        'Date': date,
                        'CPI': cpi
                    })

            except (ValueError, IndexError):
                continue

        if len(data) > 0:
            return pd.DataFrame(data)

    except Exception as e:
        logger.debug(f"Error parsing table: {str(e)[:50]}")

    return None


def parse_month_string(month_str):
    """
    Parse month string to datetime.

    Handles formats like:
    - 'Jan-2025', 'January 2025'
    - '2025-01', '01-2025'
    - 'Apr 2025'
    """

    month_str = month_str.strip()

    date_formats = [
        '%b-%Y',      # Jan-2025
        '%B-%Y',      # January-2025
        '%b %Y',      # Jan 2025
        '%B %Y',      # January 2025
        '%Y-%m',      # 2025-01
        '%m-%Y',      # 01-2025
        '%d-%m-%Y',   # 31-01-2025
        '%Y/%m',      # 2025/01
    ]

    for fmt in date_formats:
        try:
            return pd.to_datetime(month_str, format=fmt)
        except ValueError:
            continue

    # Try pandas parsing as fallback
    try:
        return pd.to_datetime(month_str)
    except:
        return None


def main():
    """Test the scraper"""
    print("\nFetching latest CPI from MOSPI...")
    print("="*70)

    df = scrape_mospi_cpi()

    if df is not None and len(df) > 0:
        print(f"\n✓ Success! Retrieved {len(df)} CPI records")
        print(f"\nLatest data:")
        print(df.tail(10))
        print(f"\nDate range: {df['Date'].min()} to {df['Date'].max()}")
        return df
    else:
        print("\n✗ No CPI data retrieved from MOSPI")
        return None


if __name__ == "__main__":
    main()
