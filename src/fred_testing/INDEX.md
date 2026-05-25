# FRED API Testing Ground - Complete Index

**Project**: Decision Algorithm DB Project  
**Created**: May 25, 2026  
**Status**: ✓ Testing Complete - CSV Output Ready

---

## Quick Navigation

### 📋 Start Here
1. **[TESTING_SUMMARY.md](TESTING_SUMMARY.md)** - Overview of all findings (5 min read)
2. **[README.md](README.md)** - How to use this testing ground (10 min read)
3. **[FRED_API_TEST_FINDINGS.md](FRED_API_TEST_FINDINGS.md)** - Detailed test results (15 min read)

### 🧪 Test Scripts
1. **[quick_test.py](quick_test.py)** - Quick 10-value fetch (fastest, use first)
2. **[test_fred_api_csv.py](test_fred_api_csv.py)** - Complete test with CSV export (comprehensive)
3. **[test_fred_api.py](test_fred_api.py)** - Full test with JSON output (original)

### 📊 CSV Output Files (Generated from quick_test.py)
- **[US_CPI_latest_10.csv](output/US_CPI_latest_10.csv)** - 10 latest US CPI values
- **[Federal_Funds_Rate_latest_10.csv](output/Federal_Funds_Rate_latest_10.csv)** - 10 latest Fed rates
- **[USD_EUR_Rate_latest_10.csv](output/USD_EUR_Rate_latest_10.csv)** - 10 latest USD/EUR rates
- **[quick_test_summary.csv](output/quick_test_summary.csv)** - Test summary
- **[quick_test_summary.json](output/quick_test_summary.json)** - JSON summary

### 📦 Setup Files
- **[requirements.txt](requirements.txt)** - Python dependencies (pandas, requests, boto3)

---

## Test Results at a Glance

### ✓ Available on FRED
```
US CPI (CPIAUCSL)           ✓ Working - Latest: 332.407 (Apr 2026)
Federal Funds Rate (FEDFUNDS) ✓ Working - Latest: 3.64% (Apr 2026)
USD/EUR Rate (DEXUSEU)      ✓ Working - Latest: 1.1627 (May 15, 2026)
```

### ✗ Not Available on FRED
```
Brent Crude (DCOILBRENTD)   ✗ 400 Error → Use EIA API
Gold Price USD (GOLDAMND)   ✗ 400 Error → Use IBJA/MCX
```

### ⚠️ India-Specific (Not on FRED)
```
RBI Repo Rate               → https://www.rbi.org.in/
USD/INR Rate                → https://www.rbi.org.in/
India CPI                   → https://mospi.gov.in/
RBI Balance Sheet           → RBI WSS
FII/DII Activity            → https://www.nseindia.com/
Nifty 50 Index              → https://www.nseindia.com/
Gold INR Price              → https://www.ibja.in/
ETF Prices                  → NSE/BSE
```

---

## CSV Files Format

### What Gets Saved
Every test produces CSV files with this structure:

```csv
date,value
2026-04-01,332.407
2026-03-01,330.293
2026-02-01,327.46
2026-01-01,326.588
2025-12-01,326.031
```

### Processing Features
- Date in ISO 8601 format (YYYY-MM-DD)
- Values as decimals (handled correctly)
- No missing headers
- Clean, ready for analysis
- Compatible with pandas.read_csv()

### Lambda-Compatible
- Code structure ready for AWS Lambda deployment
- S3 upload ready (just uncomment boto3 code)
- Parquet conversion ready (pyarrow available)
- Environment variable support built-in

---

## How to Use

### Option 1: Quick Test (Recommended First)
```bash
python3 src/fred_testing/quick_test.py
# Output: 5 CSV files in output/ directory
# Time: ~30 seconds
```

### Option 2: Full Test
```bash
pip install -r src/fred_testing/requirements.txt
python3 src/fred_testing/test_fred_api_csv.py
# Output: Comprehensive CSV files with all metadata
# Time: ~2-3 minutes
```

### Option 3: Check Results
```bash
# View test summary
cat src/fred_testing/output/quick_test_summary.csv

# View actual data
cat src/fred_testing/output/US_CPI_latest_10.csv

# View JSON summary
cat src/fred_testing/output/quick_test_summary.json
```

---

## Key Findings Summary

| Aspect | Finding | Impact |
|--------|---------|--------|
| **API Connectivity** | ✓ Working | Can use FRED for US data |
| **Data Availability** | Partial (3/5) | Need alternative sources for Brent & Gold |
| **India Data** | ✗ Not on FRED | Must build custom scrapers |
| **CSV Export** | ✓ Working | Easy to integrate with data pipeline |
| **Data Currency** | Recent | April-May 2026 latest available |
| **API Errors** | 2 series failing | Likely discontinued or parameter issues |
| **Lambda Ready** | ✓ Yes | Code ready for serverless deployment |

---

## Next Steps

### Immediate Action Items
1. ✓ Review CSV output files
2. ✓ Confirm data format meets requirements
3. [ ] Test alternative sources (EIA, IBJA)
4. [ ] Plan data pipeline architecture

### Implementation Phases
- **Phase 1**: ✓ FRED API testing (DONE)
- **Phase 2**: Build alternative data pipelines
- **Phase 3**: Database and storage setup
- **Phase 4**: Lambda function deployment
- **Phase 5**: Full integration testing

---

## Important Notes

### API Key Information
```
FRED API Key: ae3adb3c2a3d380c98e1fff8847d2471
Rate Limit: 120 requests/minute
Base URL: https://api.stlouisfed.org/fred
```

### Data Retention
- FRED data has 1-2 day lag typically
- Historical data available for 10+ years
- CSV exports preserve all data points
- Consider archiving daily/weekly

### For Production Deployment
1. Use environment variables for API keys
2. Implement error handling for failed requests
3. Add logging and monitoring
4. Set up S3 bucket for Parquet storage
5. Configure Lambda execution role
6. Set up CloudWatch alarms

---

## File Tree
```
src/fred_testing/
├── INDEX.md                          ← You are here
├── README.md                         ← Setup guide
├── TESTING_SUMMARY.md                ← Overview
├── FRED_API_TEST_FINDINGS.md         ← Detailed results
├── test_fred_api.py                  ← Full tester (JSON)
├── test_fred_api_csv.py              ← CSV tester (RECOMMENDED)
├── quick_test.py                     ← Quick test (FASTEST)
├── requirements.txt                  ← Dependencies
└── output/                           ← Generated files
    ├── US_CPI_latest_10.csv
    ├── Federal_Funds_Rate_latest_10.csv
    ├── USD_EUR_Rate_latest_10.csv
    ├── quick_test_summary.csv
    └── quick_test_summary.json
```

---

## Document Summaries

### TESTING_SUMMARY.md
- Complete overview of what was created
- Test results summary table
- Data format examples
- Implementation roadmap
- Success criteria checklist

### README.md
- Detailed setup instructions
- CSV output file descriptions
- FRED data availability list
- Lambda deployment guide
- Troubleshooting section

### FRED_API_TEST_FINDINGS.md
- Executive summary of test results
- Detailed results for each series
- Error analysis and solutions
- API response format examples
- Resource links and recommendations

---

## Quick Reference

### Working FRED Series
```
CPIAUCSL      US CPI (Monthly)
FEDFUNDS      Federal Funds Rate (Monthly)
DEXUSEU       USD/EUR Rate (Daily)
```

### Failed FRED Series
```
DCOILBRENTD   Brent Crude → Use EIA API
GOLDAMND      Gold Price → Use IBJA/MCX
```

### Alternative Sources Needed
```
RBI Data      → https://www.rbi.org.in/
NSE Data      → https://www.nseindia.com/
MOSPI Data    → https://mospi.gov.in/
IBJA Data     → https://www.ibja.in/
EIA Data      → https://www.eia.gov/petroleum/
```

---

## Testing Timeline

- **Created**: May 25, 2026, 12:42 UTC
- **API Test**: Successful (3/5 series)
- **CSV Export**: Working
- **Documentation**: Complete
- **Status**: Ready for next phase

---

**Contact for Questions**: Check TESTING_SUMMARY.md for recommendations
**Next Review**: After implementing Phase 2 (Alternative Data Pipelines)
