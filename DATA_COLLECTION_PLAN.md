# Data Collection Plan - Tailored per Parameter
**Target**: 76 months (Jan 2020 - Apr 2026), all aligned to same month-end dates

---

## Parameter-Specific Collection Strategy

### 1. **India CPI** (Used by: R2 - Real Rate Shock)

**Current Status**: 63/76 months available (FRED: 2021-03 to 2025-03)
**Issue**: Missing 2020 data, latest data is March 2025 (need through Apr 2026)

**Collection Strategy**:
```
Priority 1: FRED INDCPIALLMINMEI (pandas_datareader)
  - Available: 2021-03 to 2025-03 (63 months)
  - Action: Get all available data
  
Priority 2: RBI CPI (Alternative source)
  - Check: https://www.rbi.org.in/Scripts/Statistics.aspx
  - Get: Monthly CPI data if available
  
Priority 3: Backfill 2020 data
  - 2020 Jan-Feb: Use extrapolation from 2021 data
  - 2025-04 to 2026-04: Use last known value (forward-fill) + note as estimated
  
Final: One CSV (cpi_monthly.csv)
  Columns: Date | CPI | YoY_Change | Data_Quality (actual/estimated/interpolated)
```

**Decision**: 
- ✓ Use FRED for 2021-03 onwards
- ✓ Backfill 2020 with linear regression from first 3 months of 2021
- ✓ Forward-fill 2025-04 to 2026-04 with mark as "FORECAST"

---

### 2. **RBI Repo Rate** (Used by: R1 - Monetary System Shift)

**Current Status**: All months have forward-filled 6.50% (as of 2026-04-10)
**Issue**: Only ~6 MPC decisions/year, not monthly. Need latest rate for each month-end

**Collection Strategy**:
```
Priority 1: RBI Press Releases (MPC Decisions)
  - Source: https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx
  - Get: All MPC decisions 2020-2026
  - Method: Parse press releases for rate decision dates
  
Priority 2: For months without decisions
  - Action: Forward-fill previous rate
  - Example: If rate = 5.5% on 2026-03-15 (MPC meeting)
             Then 2026-01-31, 2026-02-28 = 5.5% (forward-fill)
  
Final: One CSV (repo_rate_monthly.csv)
  Columns: Date | Repo_Rate | MPC_Decision_Date | Data_Type (actual/forward_fill)
```

**Decision**:
- ✓ Get actual MPC decisions 2020-2026
- ✓ Forward-fill non-decision months
- ✓ Document which rates are actual vs forward-filled

---

### 3. **RBI Balance Sheet (Total Assets, FCA, Notes Circulation)** (Used by: R5 - QE Regime)

**Current Status**: Only 12 weeks (Mar-May 2026) available
**Issue**: Need 6 years (312 weeks, 76 months) of historical weekly data

**Collection Strategy**:
```
Priority 1: DBIE Manual Download (BEST QUALITY)
  - User downloads from: https://data.rbi.org.in/DBIE/
  - Category: Money, Banking & Financial System
  - Dataset: RBI Balance Sheet (Weekly)
  - Period: 2020-01-01 to 2026-04-30
  - Save as: src/data_collection/input/rbi_balance_sheet_historical.csv
  - Time: ~5 minutes to download
  
Priority 2: If manual download not available
  - Use RBI Weekly Statistical Supplement (WSS)
  - Try scraping: https://www.rbi.org.in/scripts/WSSView.aspx
  - Method: Extract balance sheet table, convert to CSV
  
Priority 3: If neither works
  - Use synthetic data based on:
    * Known values (2020 start, 2026 end)
    * Realistic growth patterns (2-5% annual)
    * Create 76 monthly aggregates from estimated weekly data
  
Final: One CSV (rbi_balance_sheet_monthly.csv)
  Columns: Date | Total_Assets | FCA | Notes_Circulation | BS_YoY_Growth | Data_Source
```

**Decision**:
- ⚠️ **USER ACTION REQUIRED**: Download from DBIE (5 min, highest quality)
- Fallback: Use available 12 weeks + synthetic estimates for 2020-2026-02
- Document data quality clearly (actual vs synthetic)

---

### 4. **FII/DII Activity** (Used by: R7 - Institutional Selling Signal)

**Current Status**: Placeholder zeros (100% available but wrong data)
**Issue**: Need daily FII/DII flows, aggregate to monthly net

**Collection Strategy**:
```
Priority 1: nsefin Library (Recommended)
  - Get daily FII/DII data from NSE via nsefin
  - Method: 
      from nsefin import NSEClient
      nse = NSEClient()
      daily_flows = nse.get_fii_dii_activity()
  - Aggregate: Sum daily flows per calendar month
  
Priority 2: NSE Website Scraping (Alternative)
  - Source: https://www.nseindia.com/market-data/fii-dii-activity
  - Method: Scrape historical FII/DII monthly data if available
  - Tool: BeautifulSoup to extract table
  
Priority 3: TrendLyne API (as alternative)
  - Check: https://trendlyne.com/macro-data/fii-dii/month/
  - Get: Monthly FII/DII data directly
  - Note: May require login
  
Final: One CSV (fii_dii_monthly.csv)
  Columns: Date | FII_Net | DII_Net | FII_3M_Cumulative | DII_3M_Sum | Data_Source
```

**Decision**:
- ✓ Try nsefin first (if available, cleanest data)
- ✓ Fallback to NSE website scraping
- ✓ Use TrendLyne if both fail
- ✓ Document source for each month

---

### 5. **NIFTY50 Index** (Used by: Quarterly Check for 6-month return)

**Current Status**: 1,564 trading days available (2020-01-01 to 2026-04-29)
**Issue**: None - full coverage

**Collection Strategy**:
```
Priority 1: YFinance (^NSEI)
  - Method: yf.download('^NSEI', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily data
  - Aggregate: For each month-end date, get close price on that date
              If month-end is weekend, use last trading day before
  
Final: One CSV (nifty50_monthly.csv)
  Columns: Date | Close_Price | MoM_Return_Pct | Data_Quality
```

**Decision**:
- ✓ Use YFinance
- ✓ Handle weekends/holidays with +1, +2 day shifting
- ✓ All 76 months should have data

---

### 6. **USD/INR Exchange Rate** (Used by: R1 - Currency Regime)

**Current Status**: Full coverage available (2020-01-01 to 2026-04-29)
**Issue**: None

**Collection Strategy**:
```
Priority 1: YFinance (USDINR=X)
  - Method: yf.download('USDINR=X', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily data
  - Aggregate: Month-end close price
  
Priority 2: RBI Reference Rate (if YFinance unavailable)
  - Source: https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx
  - Get: Official RBI exchange rate for each month-end
  
Final: One CSV (usdinr_monthly.csv)
  Columns: Date | Close_Rate | MoM_Return_Pct | INR_Depreciation_6M
```

**Decision**:
- ✓ Use YFinance (YF has 1,564 trading days)
- ✓ All 76 months should have data
- ✓ Fallback: RBI Reference Rate

---

### 7. **Gold (INR)** (Used by: Quarterly Check for 6-month return)

**Current Status**: 1,564 trading days available
**Issue**: None

**Collection Strategy**:
```
Priority 1: YFinance (GOLD)
  - Method: yf.download('GOLD', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily (MCX gold prices)
  - Aggregate: Month-end close
  
Final: One CSV (gold_inr_monthly.csv)
  Columns: Date | Close_Price_INR | MoM_Return_Pct
```

**Decision**:
- ✓ Use YFinance
- ✓ All 76 months should have data

---

### 8. **Gold (USD)** (Used by: Quarterly Check for 6-month return)

**Current Status**: 1,564 trading days available
**Issue**: None

**Collection Strategy**:
```
Priority 1: YFinance (GC=F) - COMEX Gold Futures
  - Method: yf.download('GC=F', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily
  - Aggregate: Month-end close
  
Final: One CSV (gold_usd_monthly.csv)
  Columns: Date | Close_Price_USD | MoM_Return_Pct
```

**Decision**:
- ✓ Use YFinance
- ✓ All 76 months should have data

---

### 9. **Brent Crude Oil** (Used by: R3 - Commodity/Oil Shock)

**Current Status**: 1,564 trading days available
**Issue**: None for monthly prices, but need 12-month rolling average

**Collection Strategy**:
```
Priority 1: YFinance (BZ=F) - Brent Crude Futures
  - Method: yf.download('BZ=F', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily
  - Aggregate: 
    * Month-end close price
    * 12-month rolling average (calculated from daily data)
    * Ratio = Month-end / 12M avg (for R3 trigger)
  
Final: One CSV (brent_crude_monthly.csv)
  Columns: Date | Close_Price_USD | 12M_Average | Ratio | Data_Quality
```

**Decision**:
- ✓ Use YFinance for daily data
- ✓ Calculate 12-month rolling average on daily basis
- ✓ Extract month-end values
- ✓ All 76 months should have data

---

### 10. **NIFTYBEES ETF** (Used by: Portfolio implementation)

**Current Status**: 1,564 trading days available
**Issue**: None

**Collection Strategy**:
```
Priority 1: YFinance (NIFTYBEES.NS) - NSE listing
  - Method: yf.download('NIFTYBEES.NS', start='2020-01-01', end='2026-04-30')
  - Frequency: Daily
  - Aggregate: Month-end close
  
Final: One CSV (niftybees_monthly.csv)
  Columns: Date | Close_Price | MoM_Return_Pct
```

**Decision**:
- ✓ Use YFinance
- ✓ All 76 months should have data

---

## Data Quality & Handling Missing Data

| Parameter | Priority 1 | Priority 2 | If Missing | Quality Target |
|-----------|-----------|-----------|-----------|----------------|
| CPI | FRED | RBI CPI | Interpolate | 95%+ |
| Repo Rate | MPC Decisions | RBI releases | Forward-fill | 100% (OK for non-decision months) |
| RBI Balance Sheet | DBIE download | WSS scrape | Synthetic | 100% (if manual download) |
| FII/DII | nsefin | NSE scrape | TrendLyne | 90%+ |
| NIFTY50 | YFinance | RBI data | N/A | 100% |
| USDINR | YFinance | RBI rate | Interpolate | 100% |
| GOLD INR | YFinance | MCX direct | Interpolate | 100% |
| GOLD USD | YFinance | Spot market | Interpolate | 100% |
| Brent Crude | YFinance | Futures | Interpolate | 100% |
| NIFTYBEES | YFinance | NSE direct | Interpolate | 100% |

---

## Implementation Sequence

1. **Prerequisite**: User downloads RBI Balance Sheet from DBIE (5 min, highest priority)
2. **YFinance Data**: Collect all daily data (Jan 2020 - Apr 2026)
3. **FII/DII**: Use nsefin or NSE scraping
4. **CPI**: Get FRED + backfill/forward-fill
5. **Repo Rate**: Get MPC decisions + forward-fill
6. **Aggregate**: Convert to monthly, align to month-end dates
7. **Quality Check**: Identify gaps, apply fallback strategies
8. **Final CSVs**: One CSV per parameter, all 76 rows aligned

---

## Questions Before Implementation

1. **RBI Balance Sheet**: Will you download from DBIE, or should we use synthetic data?
2. **FII/DII**: nsefin installed and working?
3. **Data Gaps**: For missing months - preference:
   - Forward-fill (copy previous month)?
   - Linear interpolation?
   - Mark as "INCOMPLETE" and use algorithm defaults?

**Next Step**: User clarifies preferences, then implement parameter-specific collectors.
