"""
Web scrapers for India-specific economic data
RBI, NSE, MOSPI data collection with CSV/Parquet export
Refined with better HTML parsing and error handling
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
import time
import re

class BaseScraper:
    """Base class for all web scrapers"""

    def __init__(self, output_dir='src/data_collection/output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.fetch_time = datetime.now()

    def fetch_url(self, url, timeout=10, retry_count=3):
        """Fetch URL with retry logic"""
        for attempt in range(retry_count):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except Exception as e:
                if attempt == retry_count - 1:
                    raise
                time.sleep(2 ** attempt)

    def save_csv(self, df, filename):
        """Save DataFrame to CSV"""
        filepath = self.output_dir / f"{filename}.csv"
        df.to_csv(filepath, index=False)
        return str(filepath)

    def save_json(self, data, filename):
        """Save data to JSON"""
        filepath = self.output_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return str(filepath)


class RBIRepoRateScraper(BaseScraper):
    """Scrapes RBI Monetary Policy Rate from press releases"""

    def __init__(self, output_dir='src/data_collection/output'):
        super().__init__(output_dir)
        self.url = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
        self.name = "RBI Repo Rate"

    def scrape(self):
        try:
            print(f"\n{self.name} - Scraping RBI Press Releases")
            response = self.fetch_url(self.url)
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')
            if not tables:
                print("⚠️  No tables found")
                return None

            repo_data = []
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        if any(kw in row_text.lower() for kw in ['repo', 'monetary policy', 'mpc']):
                            repo_data.append({'raw_text': row_text[:200], 'fetch_date': datetime.now().strftime('%Y-%m-%d')})

            if repo_data:
                df = pd.DataFrame(repo_data)
                print(f"✓ Found {len(df)} repo rate mentions")
                return df

            print("⚠️  No repo rate data found")
            return None

        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
            return None

    def run(self):
        df = self.scrape()
        if df is not None and len(df) > 0:
            csv_file = self.save_csv(df, "rbi_repo_rate")
            print(f"✓ Saved: {csv_file}")
            return df
        return None


class FIIDIIScraper(BaseScraper):
    """Scrapes FII/DII from TrendLyne with multi-method parsing"""

    def __init__(self, output_dir='src/data_collection/output'):
        super().__init__(output_dir)
        self.url = "https://trendlyne.com/macro-data/fii-dii/month/snapshot-month/"
        self.name = "FII/DII Activity"

    def scrape(self):
        try:
            print(f"\n{self.name} - Scraping TrendLyne")
            response = self.fetch_url(self.url)
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    if len(df) > 0 and any(kw in str(df.columns).lower() for kw in ['fii', 'dii', 'date']):
                        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
                        print(f"✓ Extracted {len(df)} rows")
                        return df
                except:
                    continue

            print("⚠️  No usable tables found")
            return None

        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
            return None

    def run(self):
        df = self.scrape()
        if df is not None and len(df) > 0:
            csv_file = self.save_csv(df, "fii_dii_activity")
            print(f"✓ Saved: {csv_file}")
            return df
        return None


class RBIBalanceSheetScraper(BaseScraper):
    """Scrapes RBI Balance Sheet from WSS"""

    def __init__(self, output_dir='src/data_collection/output'):
        super().__init__(output_dir)
        self.url = "https://www.rbi.org.in/scripts/WSSView.aspx"
        self.name = "RBI Balance Sheet"

    def scrape(self):
        try:
            print(f"\n{self.name} - Scraping RBI WSS")
            response = self.fetch_url(self.url)
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    header_text = ' '.join([str(c).lower() for c in df.columns])
                    if any(kw in header_text for kw in ['assets', 'liabilities', 'balance']):
                        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
                        print(f"✓ Extracted {len(df)} rows")
                        return df
                except:
                    continue

            print("⚠️  No balance sheet tables found")
            return None

        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
            return None

    def run(self):
        df = self.scrape()
        if df is not None and len(df) > 0:
            csv_file = self.save_csv(df, "rbi_balance_sheet")
            print(f"✓ Saved: {csv_file}")
            return df
        return None


class MOSPICPIScraper(BaseScraper):
    """Scrapes India CPI from MOSPI"""

    def __init__(self, output_dir='src/data_collection/output'):
        super().__init__(output_dir)
        self.url = "https://mospi.gov.in/consumer-price-index"
        self.name = "India CPI"

    def scrape(self):
        try:
            print(f"\n{self.name} - Scraping MOSPI")
            response = self.fetch_url(self.url)
            soup = BeautifulSoup(response.content, 'html.parser')

            tables = soup.find_all('table')
            for table in tables:
                try:
                    df = pd.read_html(str(table))[0]
                    header_text = ' '.join([str(c).lower() for c in df.columns])
                    if any(kw in header_text for kw in ['cpi', 'index', 'inflation']):
                        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')
                        print(f"✓ Extracted {len(df)} rows")
                        return df
                except:
                    continue

            print("⚠️  No CPI tables found")
            return None

        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
            return None

    def run(self):
        df = self.scrape()
        if df is not None and len(df) > 0:
            csv_file = self.save_csv(df, "mospi_cpi")
            print(f"✓ Saved: {csv_file}")
            return df
        return None


def run_all_scrapers(output_dir='src/data_collection/output'):
    """Run all 4 scrapers"""

    print("=" * 100)
    print("WEB SCRAPER SUITE - Phase 2 (Refined)")
    print(f"Time: {datetime.now()}")
    print("=" * 100)

    scrapers = [
        RBIRepoRateScraper(output_dir),
        FIIDIIScraper(output_dir),
        RBIBalanceSheetScraper(output_dir),
        MOSPICPIScraper(output_dir)
    ]

    results = {}

    for scraper in scrapers:
        try:
            df = scraper.run()
            results[scraper.name] = {
                'status': 'success' if df is not None else 'no_data',
                'rows': len(df) if df is not None else 0
            }
        except Exception as e:
            results[scraper.name] = {
                'status': 'error',
                'error': str(e)[:100]
            }

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_rows = sum(r.get('rows', 0) for r in results.values())

    for name, result in results.items():
        status = "✓" if result['status'] == 'success' else "⚠️ "
        rows = result.get('rows', '?')
        print(f"{status} {name}: {rows} rows")

    print(f"\n✓ {success_count}/4 working, {total_rows} total rows extracted")
    print("=" * 100)

    return results


if __name__ == "__main__":
    import os
    os.makedirs("src/data_collection/output", exist_ok=True)
    run_all_scrapers()
