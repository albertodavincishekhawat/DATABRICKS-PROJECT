"""
FRED API Testing Ground - Data Availability Check
Tests which data points required for the Decision Algorithm are available via FRED API
Lambda-compatible code structure for future migration to AWS Lambda + S3 Parquet storage
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FRED API Configuration
FRED_API_KEY = "ae3adb3c2a3d380c98e1fff8847d2471"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Data Requirements from Implementation_Requirements.md
DATA_REQUIREMENTS = {
    "RBI_Repo_Rate": {
        "source": "RBI (India specific)",
        "frequency": "After each MPC meeting",
        "fred_series": None,  # India-specific, not on FRED
        "alternative_source": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
    },
    "USD_INR_Rate": {
        "source": "RBI (India specific)",
        "frequency": "Daily",
        "fred_series": None,  # India-specific, not on FRED
        "alternative_source": "https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx"
    },
    "India_CPI": {
        "source": "MOSPI (India specific)",
        "frequency": "Monthly",
        "fred_series": None,  # FRED has US CPI, not India CPI
        "alternative_source": "https://mospi.gov.in/consumer-price-index"
    },
    "RBI_Balance_Sheet": {
        "source": "RBI (India specific)",
        "frequency": "Weekly",
        "fred_series": None,
        "alternative_source": "https://www.rbi.org.in/scripts/WSSView.aspx"
    },
    "FII_DII_Activity": {
        "source": "NSE (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.nseindia.com/market-data/fii-dii-activity"
    },
    "Brent_Crude": {
        "source": "EIA or World Bank",
        "frequency": "Daily",
        "fred_series": ["DCOILBRENTD"],  # FRED has this!
        "alternative_source": "https://www.eia.gov/petroleum/data.php"
    },
    "Nifty_50_Index": {
        "source": "NSE (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.nseindia.com/"
    },
    "Gold_Price_INR": {
        "source": "IBJA (India specific)",
        "frequency": "Daily",
        "fred_series": ["GOLDAMND"],  # Gold price in USD - need to convert
        "alternative_source": "https://www.ibja.in/"
    },
    "Gold_ETF_Price": {
        "source": "NSE/BSE (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.nseindia.com/"
    },
    "Nifty_ETF_Price": {
        "source": "NSE/BSE (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.nseindia.com/"
    },
    "US_CPI": {
        "source": "BLS via FRED",
        "frequency": "Monthly",
        "fred_series": ["CPIAUCSL"],  # All Urban Consumers CPI
        "alternative_source": None
    },
    "US_Federal_Funds_Rate": {
        "source": "Federal Reserve via FRED",
        "frequency": "Daily",
        "fred_series": ["FEDFUNDS"],
        "alternative_source": None
    },
    "USD_Index": {
        "source": "Federal Reserve via FRED",
        "frequency": "Daily",
        "fred_series": ["DEXUSEU"],  # USD/EUR as proxy
        "alternative_source": None
    }
}


class FREDAPITester:
    """Test FRED API availability for required data points"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = FRED_BASE_URL
        self.results = {}
        self.test_report = []

    def test_series_availability(self, series_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Test if a FRED series is available

        Args:
            series_id: FRED series ID (e.g., "CPIAUCSL")

        Returns:
            Tuple of (is_available, response_data)
        """
        try:
            # Test 1: Series info
            info_url = f"{self.base_url}/series?series_id={series_id}&api_key={self.api_key}&file_type=json"
            info_response = requests.get(info_url, timeout=10)
            info_response.raise_for_status()
            info_data = info_response.json()

            if 'seriess' not in info_data or len(info_data['seriess']) == 0:
                return False, {"error": "Series not found"}

            series_info = info_data['seriess'][0]

            # Test 2: Get recent observations
            obs_url = f"{self.base_url}/series/observations?series_id={series_id}&api_key={self.api_key}&file_type=json&limit=10&sort_order=desc"
            obs_response = requests.get(obs_url, timeout=10)
            obs_response.raise_for_status()
            obs_data = obs_response.json()

            if 'observations' not in obs_data or len(obs_data['observations']) == 0:
                return False, {"error": "No observations available"}

            return True, {
                "series_info": series_info,
                "latest_observation": obs_data['observations'][0],
                "sample_observations": obs_data['observations'][:3],
                "last_updated": series_info.get('last_updated'),
                "frequency": series_info.get('frequency'),
                "units": series_info.get('units')
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for series {series_id}: {str(e)}")
            return False, {"error": str(e)}
        except Exception as e:
            logger.error(f"Error testing series {series_id}: {str(e)}")
            return False, {"error": str(e)}

    def fetch_series_data(self,
                         series_id: str,
                         limit: int = 252,  # ~1 year of trading days
                         units: str = None) -> Tuple[bool, pd.DataFrame]:
        """
        Fetch historical data for a FRED series

        Args:
            series_id: FRED series ID
            limit: Number of observations to fetch
            units: Optional unit conversion parameter

        Returns:
            Tuple of (success, dataframe)
        """
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "sort_order": "desc"
            }
            if units:
                params["units"] = units

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'observations' not in data:
                return False, None

            # Convert to DataFrame
            obs_list = data['observations']
            df = pd.DataFrame(obs_list)
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.sort_values('date')

            return True, df

        except Exception as e:
            logger.error(f"Error fetching data for {series_id}: {str(e)}")
            return False, None

    def run_all_tests(self):
        """Run tests for all data requirements"""
        logger.info("=" * 80)
        logger.info("FRED API TESTING - Data Availability Check")
        logger.info(f"API Key: {self.api_key[:20]}...")
        logger.info(f"Test Time: {datetime.now()}")
        logger.info("=" * 80)

        for data_name, requirement in DATA_REQUIREMENTS.items():
            logger.info(f"\nTesting: {data_name}")
            logger.info(f"  Required Frequency: {requirement['frequency']}")
            logger.info(f"  Primary Source: {requirement['source']}")

            if requirement['fred_series'] is None:
                result = {
                    "status": "NOT_ON_FRED",
                    "data_name": data_name,
                    "fred_series": None,
                    "message": "This is India/NSE-specific data. FRED doesn't provide it.",
                    "alternative": requirement['alternative_source']
                }
                logger.warning(f"  ⚠️  NOT AVAILABLE ON FRED - Use alternative source")
                self.results[data_name] = result
                self.test_report.append(result)
            else:
                # Test each FRED series
                for series_id in requirement['fred_series']:
                    logger.info(f"  Testing FRED Series: {series_id}")
                    is_available, response_data = self.test_series_availability(series_id)

                    if is_available:
                        logger.info(f"  ✓ AVAILABLE ON FRED")
                        logger.info(f"    Last Updated: {response_data['series_info'].get('last_updated')}")
                        logger.info(f"    Frequency: {response_data['series_info'].get('frequency')}")
                        logger.info(f"    Units: {response_data['series_info'].get('units')}")
                        logger.info(f"    Latest Value: {response_data['latest_observation']}")

                        result = {
                            "status": "AVAILABLE",
                            "data_name": data_name,
                            "fred_series": series_id,
                            "series_info": response_data['series_info'],
                            "latest_value": response_data['latest_observation'],
                            "sample_data": response_data['sample_observations']
                        }
                    else:
                        logger.error(f"  ✗ NOT AVAILABLE - {response_data.get('error')}")
                        result = {
                            "status": "NOT_AVAILABLE",
                            "data_name": data_name,
                            "fred_series": series_id,
                            "error": response_data.get('error'),
                            "alternative": requirement['alternative_source']
                        }

                    self.results[data_name] = result
                    self.test_report.append(result)

    def fetch_sample_data(self):
        """Fetch and display sample data for available series"""
        logger.info("\n" + "=" * 80)
        logger.info("FETCHING SAMPLE DATA FOR AVAILABLE SERIES")
        logger.info("=" * 80)

        available_series = {
            "Brent_Crude": "DCOILBRENTD",
            "Gold_Price_USD": "GOLDAMND",
            "US_CPI": "CPIAUCSL",
            "Federal_Funds_Rate": "FEDFUNDS"
        }

        for data_name, series_id in available_series.items():
            logger.info(f"\nFetching data for {data_name} ({series_id})...")
            success, df = self.fetch_series_data(series_id, limit=30)

            if success and df is not None:
                logger.info(f"  Retrieved {len(df)} observations")
                logger.info(f"  Date Range: {df['date'].min()} to {df['date'].max()}")
                logger.info(f"  Latest Value: {df.iloc[-1]['value']} (as of {df.iloc[-1]['date']})")
                logger.info(f"\n  Sample Data (Last 5 rows):")
                logger.info(f"\n{df.tail().to_string()}")

                self.results[data_name + "_Sample"] = {
                    "series_id": series_id,
                    "row_count": len(df),
                    "date_range": f"{df['date'].min()} to {df['date'].max()}",
                    "latest_value": float(df.iloc[-1]['value']),
                    "dataframe": df
                }

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("FRED API DATA AVAILABILITY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now()}")
        report.append(f"API Key Used: {self.api_key[:20]}...")
        report.append("")

        # Summary
        available_count = sum(1 for r in self.test_report if r.get('status') == 'AVAILABLE')
        not_on_fred_count = sum(1 for r in self.test_report if r.get('status') == 'NOT_ON_FRED')
        not_available_count = sum(1 for r in self.test_report if r.get('status') == 'NOT_AVAILABLE')

        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Data Points Tested: {len(self.test_report)}")
        report.append(f"Available on FRED: {available_count}")
        report.append(f"Not on FRED (India/NSE specific): {not_on_fred_count}")
        report.append(f"Not Available: {not_available_count}")
        report.append("")

        # Detailed Results
        report.append("AVAILABLE ON FRED")
        report.append("-" * 80)
        for item in self.test_report:
            if item.get('status') == 'AVAILABLE':
                report.append(f"\n✓ {item['data_name']}")
                report.append(f"  Series ID: {item['fred_series']}")
                report.append(f"  Units: {item['series_info'].get('units')}")
                report.append(f"  Frequency: {item['series_info'].get('frequency')}")
                report.append(f"  Last Updated: {item['series_info'].get('last_updated')}")
                report.append(f"  Latest Value: {item['latest_value']}")

        report.append("\n\nNOT ON FRED (USE ALTERNATIVE SOURCES)")
        report.append("-" * 80)
        for item in self.test_report:
            if item.get('status') == 'NOT_ON_FRED':
                report.append(f"\n⚠️  {item['data_name']}")
                report.append(f"  Alternative Source: {item.get('alternative')}")

        report.append("\n\nNOT AVAILABLE")
        report.append("-" * 80)
        for item in self.test_report:
            if item.get('status') == 'NOT_AVAILABLE':
                report.append(f"\n✗ {item['data_name']}")
                report.append(f"  Series ID: {item['fred_series']}")
                report.append(f"  Error: {item.get('error')}")

        report.append("\n\nRECOMMENDATIONS")
        report.append("-" * 80)
        report.append("""
1. FRED API provides only US economic data
2. For India-specific data (RBI, CPI, FII/DII, Nifty), build separate data pipelines
3. Available FRED data can be used as reference for USD/INR rates, Brent, and Gold
4. Recommend multi-source architecture:
   - FRED API: Brent Crude, Gold price, US indicators
   - RBI Scraping: Repo Rate, Balance Sheet, USD/INR
   - NSE Scraping: Nifty Index, FII/DII, ETF Prices
   - MOSPI API: India CPI
5. All data should be stored in DynamoDB or S3 Parquet for Lambda processing
""")

        return "\n".join(report)

    def save_results_to_json(self, filename: str = "fred_test_results.json"):
        """Save test results to JSON file"""
        # Convert DataFrames to serializable format
        serializable_results = {}
        for key, value in self.results.items():
            if isinstance(value, dict):
                if 'dataframe' in value:
                    serializable_results[key] = {
                        **{k: v for k, v in value.items() if k != 'dataframe'},
                        'sample_data': value['dataframe'].head(10).to_dict(orient='records')
                    }
                else:
                    serializable_results[key] = value
            else:
                serializable_results[key] = str(value)

        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        logger.info(f"\nResults saved to {filename}")

    def save_report_to_file(self, filename: str = "fred_test_report.txt"):
        """Save test report to text file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {filename}")


# Lambda-compatible data fetching function
def lambda_handler_template(event, context):
    """
    Template for AWS Lambda function
    This can be deployed to Lambda to run scheduled tests and store results in S3
    """
    import boto3

    api_key = event.get('api_key', FRED_API_KEY)

    # Initialize tester
    tester = FREDAPITester(api_key)

    # Run tests
    tester.run_all_tests()
    tester.fetch_sample_data()

    # Generate report
    report = tester.generate_report()

    # Save to S3 as Parquet (if deploying to Lambda)
    # s3_client = boto3.client('s3')
    # ...

    return {
        'statusCode': 200,
        'body': {
            'report': report,
            'test_count': len(tester.test_report),
            'timestamp': datetime.now().isoformat()
        }
    }


if __name__ == "__main__":
    # Run tests
    tester = FREDAPITester(FRED_API_KEY)

    print("Starting FRED API tests...")
    tester.run_all_tests()
    tester.fetch_sample_data()

    # Generate and print report
    report = tester.generate_report()
    print("\n" + report)

    # Save results
    tester.save_results_to_json("src/fred_testing/fred_test_results.json")
    tester.save_report_to_file("src/fred_testing/fred_test_report.txt")

    print("\n✓ Tests complete! Check output files for detailed results.")
