# FRED API Testing Ground - Data Availability Check

This directory contains code to test which data points required for the Decision Algorithm are available via the FRED (Federal Reserve Economic Data) API.

## Overview

The Decision Algorithm requires data from multiple sources:
- **India-Specific**: RBI, NSE, MOSPI (not on FRED)
- **International/US Data**: Available via FRED API
- **Reference Data**: Some data from FRED for validation

This testing suite:
1. **Tests FRED API availability** for each required data point
2. **Fetches sample data** from available sources
3. **Saves all results to CSV** for analysis
4. **Provides implementation guidance** for data pipelines
5. **Is Lambda-compatible** for future serverless deployment

## Files

### Test Scripts
- `test_fred_api.py` - Original test script with JSON output
- `test_fred_api_csv.py` - **Recommended** - CSV-focused version

### Configuration
- `requirements.txt` - Python dependencies

### Output Directory
- `output/` - Contains all CSV results after running tests

## Output Files

After running the test, you'll get these CSV files:

### 1. `fred_test_results.csv`
**Raw test results for each data point**

Columns:
- `Data_Name`: Name of the data point (e.g., "Brent_Crude")
- `Status`: AVAILABLE / NOT_ON_FRED / NOT_AVAILABLE
- `FRED_Series_ID`: The FRED series ID if available
- `Available`: Yes/No
- `Source`: Primary source (FRED, RBI, NSE, etc.)
- `Frequency`: How often data is updated
- `Alternative_Source`: URL to alternative source
- `Title`: FRED series title
- `Units`: Data units (USD, percentage, etc.)
- `Latest_Value`: Most recent value
- `Latest_Date`: Date of latest value
- `Data_Range`: Historical data range available
- `Error_Message`: Any errors encountered

### 2. `data_availability_summary.csv`
**Quick summary of data availability**

Shows:
- Count of AVAILABLE data points
- Count of NOT_ON_FRED data points
- Count of NOT_AVAILABLE data points

### 3. `data_source_mapping.csv`
**Maps each data point to rules and implementation method**

Columns:
- `Data_Name`: Data point name
- `Required_For_Rules`: Which algorithm rules need this data
- `Frequency`: Update frequency
- `FRED_Available`: Yes/No
- `FRED_Series_ID`: FRED ID if available
- `Primary_Source`: First choice source
- `Alternative_Source`: Backup source
- `Status`: Current test status
- `Notes`: Implementation recommendations

### 4. `implementation_guide.csv`
**Step-by-step implementation roadmap**

Lists tasks in order:
1. Set up FRED API integration
2. Build RBI data scraper
3. Set up NSE data pipeline
4. Implement CPI data collection
5. Set up Gold price data feed
6. Database setup
7. Build Lambda functions
8. Set up S3 Parquet storage

Each task has:
- Implementation method
- Priority level
- Effort estimate
- Notes

### 5. `{DataName}_sample_data.csv`
**Actual sample data from FRED**

For each available data source (e.g., `Brent_Crude_sample_data.csv`):
- `date`: Date of observation
- `value`: Data value

## Quick Start

### 1. Install Dependencies

```bash
pip install -r src/fred_testing/requirements.txt
```

### 2. Run the Test

```bash
python src/fred_testing/test_fred_api_csv.py
```

### 3. Check Results

```bash
ls -la src/fred_testing/output/
cat src/fred_testing/output/fred_test_results.csv
cat src/fred_testing/output/data_availability_summary.csv
```

## API Key

The FRED API key is already configured in the script:
```python
FRED_API_KEY = "ae3adb3c2a3d380c98e1fff8847d2471"
```

For production, use environment variables:
```python
FRED_API_KEY = os.getenv('FRED_API_KEY', 'your-api-key')
```

## FRED Data Available

Based on testing, these FRED series are available:

| Data | Series ID | Frequency | Units | Status |
|------|-----------|-----------|-------|--------|
| Brent Crude Oil | DCOILBRENTD | Daily | USD/Barrel | ✓ Available |
| Gold Price | GOLDAMND | Daily | USD/troy oz | ✓ Available |
| US CPI | CPIAUCSL | Monthly | Index (1982-1984=100) | ✓ Available |
| Federal Funds Rate | FEDFUNDS | Daily | % | ✓ Available |
| USD/EUR Rate | DEXUSEU | Daily | EUR per USD | ✓ Available |

## India-Specific Data (NOT on FRED)

These require alternative data sources:

| Data | Source | Frequency |
|------|--------|-----------|
| RBI Repo Rate | https://www.rbi.org.in/ | After MPC meetings |
| USD/INR Rate | https://www.rbi.org.in/ | Daily |
| India CPI | https://mospi.gov.in/ | Monthly |
| Nifty 50 Index | https://www.nseindia.com/ | Daily |
| FII/DII Activity | https://www.nseindia.com/ | Daily |
| Gold INR Price | https://www.ibja.in/ | Daily |
| ETF Prices | NSE/BSE | Daily |

## For Lambda Deployment

This code is structured to be easily converted to AWS Lambda:

### Current Flow
```
Run Script → Test FRED API → Fetch Data → Save CSV → Output Directory
```

### Lambda Flow
```
EventBridge Trigger → Lambda Function → Test FRED API → Fetch Data → Save to S3 (Parquet)
```

### Lambda Adaptation Checklist

- [ ] Add Lambda handler function (`lambda_handler`)
- [ ] Configure environment variables for API keys
- [ ] Add S3 writing capability
- [ ] Convert CSV to Parquet before S3 upload
- [ ] Add error handling and CloudWatch logging
- [ ] Set up EventBridge schedule (daily/weekly)
- [ ] Configure IAM role for S3 access

### Code for Lambda Conversion

```python
import boto3
import io
from pyarrow import parquet

def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Run tests
    tester = FREDAPICSVTester(os.getenv('FRED_API_KEY'))
    tester.run_complete_test_and_save()
    
    # Convert CSVs to Parquet and upload to S3
    for csv_file in os.listdir(OUTPUT_DIR):
        if csv_file.endswith('.csv'):
            csv_path = os.path.join(OUTPUT_DIR, csv_file)
            df = pd.read_csv(csv_path)
            
            # Convert to Parquet
            parquet_buffer = io.BytesIO()
            table = pa.Table.from_pandas(df)
            parquet.write_table(table, parquet_buffer)
            
            # Upload to S3
            s3_key = f"fred-data/{datetime.now().date()}/{csv_file.replace('.csv', '.parquet')}"
            s3_client.put_object(
                Bucket='your-bucket-name',
                Key=s3_key,
                Body=parquet_buffer.getvalue()
            )
    
    return {
        'statusCode': 200,
        'message': 'FRED API test and data upload complete'
    }
```

## Data Quality Notes

### FRED Data
- **Completeness**: Some series have gaps
- **Lag**: Daily data may have 1-2 day lag
- **Reliability**: Sourced from Federal Reserve, very reliable
- **Historical Depth**: 10+ years for most series

### India-Specific Data
- Need to build separate pipelines
- Some sources may require web scraping
- Data quality varies by source
- May need manual verification

## Troubleshooting

### API Rate Limit
FRED allows 120 requests per minute per API key
- If you hit limit: wait 1 minute and retry
- Increase delay between requests if needed

### No Data for Series
Some series may have no recent data
- Check `Data_Range` in CSV output
- May need to fall back to alternative source

### Connection Errors
Check:
- Internet connectivity
- API key validity
- FRED API status: https://fred.stlouisfed.org/

## Next Steps

1. **Review CSV outputs** to understand data availability
2. **Build data pipelines** for unavailable data (India-specific)
3. **Set up database** to store collected data
4. **Create Lambda functions** for automated collection
5. **Deploy to S3** as Parquet files for analysis

## References

- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [FRED Series Search](https://fred.stlouisfed.org/)
- [RBI Data Sources](https://www.rbi.org.in/)
- [NSE Market Data](https://www.nseindia.com/market-data/)
- [MOSPI CPI Data](https://mospi.gov.in/consumer-price-index)

---

**Last Updated**: May 25, 2026  
**Status**: Ready for Testing
