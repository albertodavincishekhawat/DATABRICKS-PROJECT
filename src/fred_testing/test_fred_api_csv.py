"""
FRED API Testing Ground - Data Availability Check (CSV Export)
Tests which data points required for the Decision Algorithm are available via FRED API
Saves all results and sample data to CSV files for easy analysis
Lambda-compatible code structure for future migration to AWS Lambda + S3 storage
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FRED API Configuration
FRED_API_KEY = "ae3adb3c2a3d380c98e1fff8847d2471"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Output directory
OUTPUT_DIR = "src/fred_testing/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data Requirements from Implementation_Requirements.md
DATA_REQUIREMENTS = {
    "RBI_Repo_Rate": {
        "source": "RBI (India specific)",
        "frequency": "After each MPC meeting",
        "fred_series": None,
        "alternative_source": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
    },
    "USD_INR_Rate": {
        "source": "RBI (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx"
    },
    "India_CPI": {
        "source": "MOSPI (India specific)",
        "frequency": "Monthly",
        "fred_series": None,
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
        "source": "EIA",
        "frequency": "Daily",
        "fred_series": ["DCOILBRENTD"],
        "alternative_source": "https://www.eia.gov/petroleum/data.php"
    },
    "Nifty_50_Index": {
        "source": "NSE (India specific)",
        "frequency": "Daily",
        "fred_series": None,
        "alternative_source": "https://www.nseindia.com/"
    },
    "Gold_Price_USD": {
        "source": "FRED",
        "frequency": "Daily",
        "fred_series": ["GOLDAMND"],
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
        "fred_series": ["CPIAUCSL"],
        "alternative_source": None
    },
    "Federal_Funds_Rate": {
        "source": "Federal Reserve via FRED",
        "frequency": "Daily",
        "fred_series": ["FEDFUNDS"],
        "alternative_source": None
    },
    "USD_Index": {
        "source": "Federal Reserve via FRED",
        "frequency": "Daily",
        "fred_series": ["DEXUSEU"],
        "alternative_source": None
    }
}


class FREDAPICSVTester:
    """Test FRED API availability and save all data to CSV"""

    def __init__(self, api_key: str, output_dir: str = OUTPUT_DIR):
        self.api_key = api_key
        self.base_url = FRED_BASE_URL
        self.output_dir = output_dir
        self.test_results = []
        self.sample_data_frames = {}

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Output directory: {output_dir}")

    def test_series_availability(self, series_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Test if a FRED series is available"""
        try:
            # Get series info
            info_url = f"{self.base_url}/series?series_id={series_id}&api_key={self.api_key}&file_type=json"
            info_response = requests.get(info_url, timeout=10)
            info_response.raise_for_status()
            info_data = info_response.json()

            if 'seriess' not in info_data or len(info_data['seriess']) == 0:
                return False, {"error": "Series not found"}

            series_info = info_data['seriess'][0]

            # Get recent observations
            obs_url = f"{self.base_url}/series/observations?series_id={series_id}&api_key={self.api_key}&file_type=json&limit=10"
            obs_response = requests.get(obs_url, timeout=10)
            obs_response.raise_for_status()
            obs_data = obs_response.json()

            if 'observations' not in obs_data or len(obs_data['observations']) == 0:
                return False, {"error": "No observations available"}

            return True, {
                "series_id": series_id,
                "title": series_info.get('title'),
                "units": series_info.get('units'),
                "frequency": series_info.get('frequency'),
                "last_updated": series_info.get('last_updated'),
                "latest_observation": obs_data['observations'][-1],
                "observation_start": series_info.get('observation_start'),
                "observation_end": series_info.get('observation_end')
            }

        except Exception as e:
            logger.error(f"Error testing series {series_id}: {str(e)}")
            return False, {"error": str(e)}

    def fetch_series_data(self, series_id: str, limit: int = 252) -> Tuple[bool, pd.DataFrame]:
        """Fetch historical data for a FRED series"""
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "sort_order": "asc"
            }

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
            df = df.dropna(subset=['value'])  # Remove missing values
            df = df.sort_values('date')

            return True, df

        except Exception as e:
            logger.error(f"Error fetching data for {series_id}: {str(e)}")
            return False, None

    def run_all_tests(self):
        """Run tests for all data requirements"""
        logger.info("=" * 100)
        logger.info("FRED API TESTING - Data Availability Check")
        logger.info(f"API Key: {self.api_key[:20]}...")
        logger.info(f"Test Time: {datetime.now()}")
        logger.info("=" * 100)

        for data_name, requirement in DATA_REQUIREMENTS.items():
            logger.info(f"\n{'Testing: ' + data_name:<50} | Source: {requirement['source']}")

            if requirement['fred_series'] is None:
                # Not on FRED
                result_row = {
                    "Data_Name": data_name,
                    "Status": "NOT_ON_FRED",
                    "FRED_Series_ID": None,
                    "Available": "No",
                    "Source": requirement['source'],
                    "Frequency": requirement['frequency'],
                    "Alternative_Source": requirement['alternative_source'],
                    "Title": None,
                    "Units": None,
                    "FRED_Frequency": None,
                    "Latest_Value": None,
                    "Latest_Date": None,
                    "Data_Range": None,
                    "Error_Message": "India/NSE-specific data - not available on FRED",
                    "Test_Timestamp": datetime.now()
                }
                logger.warning(f"  ⚠️  NOT AVAILABLE ON FRED")
                self.test_results.append(result_row)

            else:
                # Test each FRED series
                for series_id in requirement['fred_series']:
                    logger.info(f"  Testing FRED Series: {series_id}")
                    is_available, response_data = self.test_series_availability(series_id)

                    if is_available:
                        logger.info(f"  ✓ AVAILABLE ON FRED")
                        logger.info(f"    Title: {response_data['title']}")
                        logger.info(f"    Units: {response_data['units']}")
                        logger.info(f"    Frequency: {response_data['frequency']}")
                        logger.info(f"    Latest: {response_data['latest_observation']}")

                        result_row = {
                            "Data_Name": data_name,
                            "Status": "AVAILABLE",
                            "FRED_Series_ID": series_id,
                            "Available": "Yes",
                            "Source": requirement['source'],
                            "Frequency": requirement['frequency'],
                            "Alternative_Source": requirement['alternative_source'],
                            "Title": response_data['title'],
                            "Units": response_data['units'],
                            "FRED_Frequency": response_data['frequency'],
                            "Latest_Value": response_data['latest_observation'].get('value'),
                            "Latest_Date": response_data['latest_observation'].get('date'),
                            "Data_Range": f"{response_data['observation_start']} to {response_data['observation_end']}",
                            "Error_Message": None,
                            "Test_Timestamp": datetime.now()
                        }
                    else:
                        logger.error(f"  ✗ NOT AVAILABLE - {response_data.get('error')}")
                        result_row = {
                            "Data_Name": data_name,
                            "Status": "NOT_AVAILABLE",
                            "FRED_Series_ID": series_id,
                            "Available": "No",
                            "Source": requirement['source'],
                            "Frequency": requirement['frequency'],
                            "Alternative_Source": requirement['alternative_source'],
                            "Title": None,
                            "Units": None,
                            "FRED_Frequency": None,
                            "Latest_Value": None,
                            "Latest_Date": None,
                            "Data_Range": None,
                            "Error_Message": response_data.get('error'),
                            "Test_Timestamp": datetime.now()
                        }

                    self.test_results.append(result_row)

    def fetch_sample_data(self):
        """Fetch and save sample data for available series"""
        logger.info("\n" + "=" * 100)
        logger.info("FETCHING SAMPLE DATA FOR AVAILABLE SERIES")
        logger.info("=" * 100)

        available_series = {
            "Brent_Crude": "DCOILBRENTD",
            "Gold_Price_USD": "GOLDAMND",
            "US_CPI": "CPIAUCSL",
            "Federal_Funds_Rate": "FEDFUNDS",
            "USD_EUR_Rate": "DEXUSEU"
        }

        for data_name, series_id in available_series.items():
            logger.info(f"\nFetching data for {data_name} ({series_id})...")
            success, df = self.fetch_series_data(series_id, limit=365)

            if success and df is not None:
                logger.info(f"  ✓ Retrieved {len(df)} observations")
                logger.info(f"    Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
                logger.info(f"    Latest Value: {df.iloc[-1]['value']:.4f} (as of {df.iloc[-1]['date'].date()})")

                # Store for later saving
                self.sample_data_frames[data_name] = df
            else:
                logger.error(f"  ✗ Failed to fetch data")

    def save_test_results_csv(self, filename: str = "fred_test_results.csv"):
        """Save test results to CSV"""
        filepath = os.path.join(self.output_dir, filename)
        results_df = pd.DataFrame(self.test_results)
        results_df.to_csv(filepath, index=False)
        logger.info(f"✓ Test results saved to: {filepath}")
        return filepath

    def save_sample_data_csv(self):
        """Save all sample data to individual CSV files"""
        logger.info("\nSaving sample data to CSV files...")
        saved_files = []

        for data_name, df in self.sample_data_frames.items():
            filename = f"{data_name}_sample_data.csv"
            filepath = os.path.join(self.output_dir, filename)
            df.to_csv(filepath, index=False)
            logger.info(f"  ✓ {data_name}: {filepath}")
            saved_files.append(filepath)

        return saved_files

    def save_summary_csv(self, filename: str = "data_availability_summary.csv"):
        """Save summary of data availability"""
        filepath = os.path.join(self.output_dir, filename)

        summary_data = {
            "Data_Type": [],
            "Status": [],
            "Count": []
        }

        results_df = pd.DataFrame(self.test_results)

        statuses = ["AVAILABLE", "NOT_ON_FRED", "NOT_AVAILABLE"]
        for status in statuses:
            count = len(results_df[results_df["Status"] == status])
            summary_data["Status"].append(status)
            summary_data["Count"].append(count)

            if status == "AVAILABLE":
                summary_data["Data_Type"].append("✓ Available on FRED")
            elif status == "NOT_ON_FRED":
                summary_data["Data_Type"].append("⚠️  India/NSE Specific (Use Alternative)")
            else:
                summary_data["Data_Type"].append("✗ Not Available")

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(filepath, index=False)
        logger.info(f"✓ Summary saved to: {filepath}")
        return filepath

    def save_data_source_mapping_csv(self, filename: str = "data_source_mapping.csv"):
        """Save mapping of required data to sources"""
        filepath = os.path.join(self.output_dir, filename)

        mapping_data = {
            "Data_Name": [],
            "Required_For_Rules": [],
            "Frequency": [],
            "FRED_Available": [],
            "FRED_Series_ID": [],
            "Primary_Source": [],
            "Alternative_Source": [],
            "Status": [],
            "Notes": []
        }

        # Map data to rules
        data_to_rules = {
            "RBI_Repo_Rate": "R1, R2",
            "USD_INR_Rate": "R1",
            "India_CPI": "R2",
            "RBI_Balance_Sheet": "R5",
            "FII_DII_Activity": "R7",
            "Brent_Crude": "R3",
            "Nifty_50_Index": "Quarterly Check",
            "Gold_Price_INR": "Quarterly Check",
            "Gold_ETF_Price": "Quarterly Check, SIP Execution",
            "Nifty_ETF_Price": "Quarterly Check, SIP Execution",
            "US_CPI": "Reference",
            "Federal_Funds_Rate": "Reference",
            "USD_Index": "Reference"
        }

        results_df = pd.DataFrame(self.test_results)

        for data_name, requirement in DATA_REQUIREMENTS.items():
            fred_available = "Yes" if requirement['fred_series'] is not None else "No"
            fred_series = requirement['fred_series'][0] if requirement['fred_series'] else None

            # Get status from results
            result_row = results_df[results_df["Data_Name"] == data_name]
            if not result_row.empty:
                status = result_row.iloc[0]["Status"]
            else:
                status = "NOT_TESTED"

            mapping_data["Data_Name"].append(data_name)
            mapping_data["Required_For_Rules"].append(data_to_rules.get(data_name, "N/A"))
            mapping_data["Frequency"].append(requirement['frequency'])
            mapping_data["FRED_Available"].append(fred_available)
            mapping_data["FRED_Series_ID"].append(fred_series)
            mapping_data["Primary_Source"].append(requirement['source'])
            mapping_data["Alternative_Source"].append(requirement['alternative_source'])
            mapping_data["Status"].append(status)

            # Add notes
            if status == "AVAILABLE":
                notes = "Use FRED API for this data"
            elif status == "NOT_ON_FRED":
                notes = "Build custom scraper or API integration"
            else:
                notes = "May need alternative or manual data entry"

            mapping_data["Notes"].append(notes)

        mapping_df = pd.DataFrame(mapping_data)
        mapping_df.to_csv(filepath, index=False)
        logger.info(f"✓ Mapping saved to: {filepath}")
        return filepath

    def generate_implementation_guide_csv(self, filename: str = "implementation_guide.csv"):
        """Generate implementation guide for data collection"""
        filepath = os.path.join(self.output_dir, filename)

        guide_data = {
            "Step": [],
            "Task": [],
            "Data_Source": [],
            "Implementation_Method": [],
            "Priority": [],
            "Effort_Level": [],
            "Notes": []
        }

        tasks = [
            {
                "step": 1,
                "task": "Set up FRED API integration",
                "source": "FRED",
                "method": "Use existing FRED API client (Python requests)",
                "priority": "High",
                "effort": "Low",
                "notes": "Can fetch Brent, Gold, US CPI, Fed Funds Rate"
            },
            {
                "step": 2,
                "task": "Build RBI data scraper",
                "source": "RBI",
                "method": "Web scraping or manual data entry",
                "priority": "High",
                "effort": "Medium",
                "notes": "Need Repo Rate, Balance Sheet, USD/INR rates"
            },
            {
                "step": 3,
                "task": "Set up NSE data pipeline",
                "source": "NSE",
                "method": "Web scraping or NSE API if available",
                "priority": "High",
                "effort": "Medium",
                "notes": "Need Nifty, FII/DII, ETF prices"
            },
            {
                "step": 4,
                "task": "Implement CPI data collection",
                "source": "MOSPI",
                "method": "Web scraping or MOSPI API",
                "priority": "High",
                "effort": "Low",
                "notes": "Monthly data, can be automated"
            },
            {
                "step": 5,
                "task": "Set up Gold price data feed",
                "source": "IBJA",
                "method": "Web scraping or API integration",
                "priority": "Medium",
                "effort": "Medium",
                "notes": "Need INR per gram, daily"
            },
            {
                "step": 6,
                "task": "Database setup",
                "source": "Internal",
                "method": "Create PostgreSQL/DynamoDB tables",
                "priority": "High",
                "effort": "Medium",
                "notes": "See Implementation_Requirements.md for schema"
            },
            {
                "step": 7,
                "task": "Build Lambda functions",
                "source": "AWS",
                "method": "AWS Lambda + EventBridge",
                "priority": "Medium",
                "effort": "Medium",
                "notes": "Daily/weekly schedule for data collection"
            },
            {
                "step": 8,
                "task": "Set up S3 Parquet storage",
                "source": "AWS",
                "method": "Lambda -> S3 Parquet conversion",
                "priority": "Medium",
                "effort": "Low",
                "notes": "For data lake and historical analysis"
            }
        ]

        for task in tasks:
            guide_data["Step"].append(task["step"])
            guide_data["Task"].append(task["task"])
            guide_data["Data_Source"].append(task["source"])
            guide_data["Implementation_Method"].append(task["method"])
            guide_data["Priority"].append(task["priority"])
            guide_data["Effort_Level"].append(task["effort"])
            guide_data["Notes"].append(task["notes"])

        guide_df = pd.DataFrame(guide_data)
        guide_df.to_csv(filepath, index=False)
        logger.info(f"✓ Implementation guide saved to: {filepath}")
        return filepath

    def run_complete_test_and_save(self):
        """Run complete test and save all CSV files"""
        logger.info("\nStarting complete FRED API test with CSV export...")
        logger.info(f"Output directory: {self.output_dir}\n")

        # Run tests
        self.run_all_tests()

        # Fetch sample data
        self.fetch_sample_data()

        # Save all CSV files
        logger.info("\nSaving CSV files...")
        files_saved = {
            "Test Results": self.save_test_results_csv(),
            "Summary": self.save_summary_csv(),
            "Data Source Mapping": self.save_data_source_mapping_csv(),
            "Implementation Guide": self.save_implementation_guide_csv()
        }

        # Save sample data
        data_files = self.save_sample_data_csv()
        files_saved["Sample Data Files"] = data_files

        logger.info("\n" + "=" * 100)
        logger.info("ALL FILES SAVED SUCCESSFULLY")
        logger.info("=" * 100)

        for category, files in files_saved.items():
            logger.info(f"\n{category}:")
            if isinstance(files, list):
                for f in files:
                    logger.info(f"  • {f}")
            else:
                logger.info(f"  • {files}")

        return files_saved


if __name__ == "__main__":
    # Run complete test
    tester = FREDAPICSVTester(FRED_API_KEY)
    files_saved = tester.run_complete_test_and_save()

    logger.info("\n✓ Test complete! All data saved as CSV files.")
    logger.info(f"Check the '{OUTPUT_DIR}' directory for results.")
