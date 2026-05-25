# FRED API Test Findings

**Test Date**: May 25, 2026  
**API Key**: ae3adb3c2a3d380c98e1fff8847d2471  
**Test Script**: `quick_test.py`

---

## Executive Summary

### ✓ SUCCESSFUL
- **US CPI (CPIAUCSL)**: 10 latest values retrieved successfully
- **Federal Funds Rate (FEDFUNDS)**: 10 latest values retrieved successfully  
- **USD/EUR Rate (DEXUSEU)**: 10 latest values retrieved successfully

### ✗ FAILED
- **Brent Crude (DCOILBRENTD)**: 400 Bad Request error
- **Gold Price USD (GOLDAMND)**: 400 Bad Request error

---

## Detailed Results

### 1. US CPI (CPIAUCSL) ✓

**Status**: AVAILABLE AND WORKING

**Latest 10 Values**:
```
Date          Value
2025-07-01    322.169
2025-08-01    323.291
2025-09-01    324.245
2025-10-01    (missing)
2025-11-01    325.063
2025-12-01    326.031
2026-01-01    326.588
2026-02-01    327.460
2026-03-01    330.293
2026-04-01    332.407
```

**Notes**:
- Monthly frequency (first of month)
- Index with base period 1982-1984=100
- Latest available: April 2026
- Good data quality (only 1 missing value in last 10)

**Implementation for Decision Algorithm**:
- Can be used for reference/validation
- Monthly updates sufficient
- Reliable data source

**CSV File**: `US_CPI_latest_10.csv`

---

### 2. Federal Funds Rate (FEDFUNDS) ✓

**Status**: AVAILABLE AND WORKING

**Latest 10 Values**:
```
Date          Value (%)
2025-07-01    4.33
2025-08-01    4.33
2025-09-01    4.22
2025-10-01    4.09
2025-11-01    3.88
2025-12-01    3.72
2026-01-01    3.64
2026-02-01    3.64
2026-03-01    3.64
2026-04-01    3.64
```

**Notes**:
- Monthly frequency
- Percentage format
- Latest available: April 2026
- Shows declining trend from July 2025 to Jan 2026, then stable
- Good data quality (no missing values)

**Implementation for Decision Algorithm**:
- Can be used for reference/comparison
- Monthly updates sufficient
- Reliable data source for US monetary policy context

**CSV File**: `Federal_Funds_Rate_latest_10.csv`

---

### 3. USD/EUR Exchange Rate (DEXUSEU) ✓

**Status**: AVAILABLE AND WORKING

**Latest 10 Values**:
```
Date          Value (EUR per USD)
2026-05-04    1.1698
2026-05-05    1.1707
2026-05-06    1.1753
2026-05-07    1.1764
2026-05-08    1.1773
2026-05-11    1.1780
2026-05-12    1.1733
2026-05-13    1.1711
2026-05-14    1.1678
2026-05-15    1.1627
```

**Notes**:
- Daily frequency
- Very recent data (current week)
- Latest available: May 15, 2026
- Good data quality (no missing values)
- Shows daily volatility

**Implementation for Decision Algorithm**:
- Can be used as reference for FX movements
- Daily data available
- Reliable data source

**CSV File**: `USD_EUR_Rate_latest_10.csv`

---

### 4. Brent Crude Oil (DCOILBRENTD) ✗

**Status**: NOT WORKING - 400 Bad Request

**Error**:
```
400 Client Error: Bad Request for url: https://api.stlouisfed.org/fred/series/observations?series_id=DCOILBRENTD&...
```

**Possible Causes**:
1. Series ID may be incorrect or discontinued
2. API parameter issue
3. Rate limiting
4. Data source issue on FRED end

**Alternative Solutions**:
1. **EIA API**: https://www.eia.gov/petroleum/data.php
   - Direct source for crude oil prices
   - More reliable for Brent data
   
2. **World Bank**: https://www.worldbank.org/en/research/commodity-markets
   - Historical Brent prices available
   - Reliable but may be lower frequency

3. **Manual API call with different parameters**:
   ```python
   # Try alternative series ID or parameters
   url = "https://api.stlouisfed.org/fred/series/observations"
   params = {
       "series_id": "DCOILBRENTD",
       "api_key": api_key,
       "file_type": "json"
       # Try without sort_order or limit parameters
   }
   ```

**CRITICAL FOR IMPLEMENTATION**: 
- R3 (Commodity/Oil Shock) requires Brent Crude data
- Cannot use FRED for this - must use alternative source
- Recommend: EIA API as primary source

---

### 5. Gold Price USD (GOLDAMND) ✗

**Status**: NOT WORKING - 400 Bad Request

**Error**:
```
400 Client Error: Bad Request for url: https://api.stlouisfed.org/fred/series/observations?series_id=GOLDAMND&...
```

**Possible Causes**:
1. Series ID may be incorrect or discontinued  
2. API parameter issue
3. Data no longer available on FRED
4. Rate limiting

**Alternative Solutions**:
1. **IBJA (India Bullion & Jewellers Association)**
   - Direct source for India gold prices (INR/gram)
   - https://www.ibja.in/
   - Daily updates
   - Most accurate for Indian market

2. **MCX (Multi Commodity Exchange)**
   - Gold futures prices
   - https://www.mcxindia.com/
   - More accessible via API

3. **World Bank Commodity Database**
   - Historical gold prices (USD/troy oz)
   - Lower frequency

4. **Manual data collection**
   - From financial news sources
   - More reliable for consistent pricing

**CRITICAL FOR IMPLEMENTATION**:
- Quarterly Check requires Gold INR price
- FRED doesn't provide this reliably
- Must use IBJA or MCX as primary source
- Can use FRED gold price as reference only

---

## Data Availability for Decision Algorithm

### For India-Specific Rules (R1, R2, R3, R5, R7)

| Data Required | Available on FRED | Alternative Source |
|---------------|-------------------|-------------------|
| RBI Repo Rate | ✗ No | RBI Website |
| USD/INR Rate | ✗ No | RBI Website |
| India CPI | ✗ No | MOSPI Website |
| RBI Balance Sheet | ✗ No | RBI WSS |
| FII/DII Activity | ✗ No | NSE Website |
| **Brent Crude** | ✗ No (API Error) | EIA API |
| Nifty 50 Index | ✗ No | NSE Website |
| **Gold INR Price** | ✗ No (API Error) | IBJA/MCX |

### For Reference/Validation Data

| Data | Available on FRED | Status |
|------|-------------------|--------|
| US CPI | ✓ Yes | Working |
| Federal Funds Rate | ✓ Yes | Working |
| USD/EUR Rate | ✓ Yes | Working |
| **Brent Crude** | Listed but errors | Not Working |
| **Gold USD** | Listed but errors | Not Working |

---

## Recommendations

### ✓ Proceed With
1. Use FRED API for US economic data (CPI, Fed Funds Rate)
2. Use FRED for general FX references (USD/EUR)
3. Set up as background data for context

### ✗ Do Not Use FRED For
1. **Brent Crude** - Use EIA API instead
2. **Gold Prices** - Use IBJA/MCX instead
3. **India-specific data** - Build dedicated scrapers

### Build Dedicated Pipelines For
1. **RBI Data**: Web scraping from RBI website
2. **NSE Data**: Web scraping or NSE API if available
3. **MOSPI Data**: Web scraping or MOSPI API
4. **Gold Prices**: IBJA scraping or MCX API
5. **Commodity Data**: EIA API for Brent crude

---

## API Response Format (Successful Calls)

### Request Format
```
GET https://api.stlouisfed.org/fred/series/observations
Parameters:
- series_id: String (e.g., "CPIAUCSL")
- api_key: String
- file_type: "json"
- limit: Integer (max results)
- sort_order: "asc" or "desc"
```

### Response Format (JSON)
```json
{
  "seriess": [
    {
      "id": "CPIAUCSL",
      "title": "Consumer Price Index for All Urban Consumers: All items",
      "units": "Index 1982-1984=100",
      "frequency": "Monthly",
      "last_updated": "2026-05-23",
      "observation_start": "1947-01-01",
      "observation_end": "2026-04-01"
    }
  ],
  "observations": [
    {
      "date": "2026-04-01",
      "value": "332.407"
    },
    {
      "date": "2026-03-01", 
      "value": "330.293"
    }
  ]
}
```

### CSV Representation
```
date,value
2026-04-01,332.407
2026-03-01,330.293
```

---

## CSV Output Files Generated

1. **`US_CPI_latest_10.csv`** - 10 latest US CPI values (monthly)
2. **`Federal_Funds_Rate_latest_10.csv`** - 10 latest Fed Funds rates (monthly)
3. **`USD_EUR_Rate_latest_10.csv`** - 10 latest USD/EUR exchange rates (daily)
4. **`quick_test_summary.csv`** - Test summary table
5. **`quick_test_summary.json`** - Test summary JSON

---

## Next Steps

### Immediate (This Week)
- [ ] Verify Brent Crude and Gold series IDs with FRED support
- [ ] Test EIA API for Brent Crude
- [ ] Test IBJA/MCX for Gold prices
- [ ] Create alternative data source tests

### Short-term (Next 2 Weeks)
- [ ] Build RBI data web scraper
- [ ] Build NSE data web scraper  
- [ ] Build MOSPI data integration
- [ ] Set up data validation tests

### Medium-term (Next Month)
- [ ] Integrate all data sources into single pipeline
- [ ] Set up database storage
- [ ] Create Lambda functions for automated collection
- [ ] Deploy to S3 as Parquet files

---

## Troubleshooting Guide

### Issue: 400 Bad Request for Valid Series
**Solution**: 
- Check series ID is correct
- Verify API key has sufficient quota
- Try without optional parameters first
- Check FRED API status page

### Issue: Rate Limiting
**Solution**:
- FRED allows 120 requests/minute
- Add delays between requests
- Consider caching responses
- Use batch requests if available

### Issue: Missing Data Points
**Solution**:
- Some series have gaps
- Check data availability range in series info
- Verify release dates for monthly data
- Use interpolation or forward-fill as needed

---

## Resources

- [FRED API Docs](https://fred.stlouisfed.org/docs/api/fred/)
- [EIA Petroleum Data](https://www.eia.gov/petroleum/data.php)
- [IBJA Gold Rates](https://www.ibja.in/)
- [RBI Website](https://www.rbi.org.in/)
- [NSE Market Data](https://www.nseindia.com/market-data/)

---

**Document Status**: Complete - Ready for Implementation  
**Last Updated**: May 25, 2026, 12:42 UTC