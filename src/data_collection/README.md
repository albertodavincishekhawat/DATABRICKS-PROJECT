# YFinance Data Collection Module

**Status**: ✓ Phase 1 Complete - 12+ months of historical data fetched for all 6 tickers

---

## Overview

Unified data fetcher for Yahoo Finance data sources required by the portfolio rebalancing decision algorithm.

**Data Coverage**: May 30, 2025 - May 25, 2026 (365+ days)

---

## Data Sources (6 Total)

| Ticker | Symbol | Rows | Latest Value | Required For |
|--------|--------|------|--------------|--------------|
| USDINR | USDINR=X | 254 | 96.17 INR/USD | R1 (Monetary System Shift) |
| NIFTY50 | ^NSEI | 242 | 23,719.30 | Quarterly Check, R7 |
| Gold INR | GOLD | 247 | 43.40 INR | Quarterly Check |
| Gold USD | GC=F | 248 | $4,521.00 | Reference data |
| Brent Crude | BZ=F | 248 | $103.54 | R3 (Oil Shock) |
| Nifty BeES | NIFTYBEES.NS | 243 | 269.10 INR | Portfolio NAV |

**Total data points**: 1,482 rows across all sources

---

## Usage

### Run the Fetcher

```bash
python3 src/data_collection/yfinance_fetcher.py
```

### Class Usage (Python)

```python
from yfinance_fetcher import YFinanceFetcher

# Fetch 12 months of data
fetcher = YFinanceFetcher(months_back=12)
all_data = fetcher.fetch_all()

# Save in multiple formats
fetcher.save_individual_csv(all_data)
fetcher.save_combined_csv(all_data)
fetcher.save_parquet(all_data)
fetcher.save_summary_json(all_data)

# Or use convenience method
fetcher.run()
```

---

## Output Files

All files saved to `src/data_collection/output/`

### Individual CSVs (6 files)
- `USDINR_data.csv` - Raw YFinance data for USD/INR
- `NIFTY50_data.csv` - Raw YFinance data for Nifty 50
- `GOLD_INR_data.csv` - Raw YFinance data for Gold (INR)
- `GOLD_USD_data.csv` - Raw YFinance data for Gold (USD)
- `BRENT_CRUDE_data.csv` - Raw YFinance data for Brent Crude
- `NIFTY_BEES_data.csv` - Raw YFinance data for Nifty BeES ETF

**Format**: Standard YFinance CSV with columns: Date, Open, High, Low, Close, Volume, Adj Close

### Combined Files

#### CSV Format (for spreadsheets & analysis)
```
src/data_collection/output/yfinance_all_data.csv
```

**Columns**: Date, Ticker, Ticker_Name, Close, Open, High, Low, Volume, Fetch_Date

**Size**: ~172 KB (1,482 rows)

**Example rows**:
```
2025-05-30,USDINR=X,USDINR,85.36,85.36,85.64,85.24,0,2026-05-25 14:44:35
2026-05-22,NSEI,NIFTY50,23719.30,23705.95,23741.45,23661.05,9000000,2026-05-25 14:44:35
```

#### Parquet Format (for Lambda/production)
```
src/data_collection/output/yfinance_all_data.parquet
```

**Advantages**:
- Compressed (~60 KB vs 172 KB CSV)
- Type-safe (schema preserved)
- Faster to read/write
- Native support in pandas, PySpark, AWS Athena
- Ready for S3 storage

### Summary JSON
```
src/data_collection/output/yfinance_summary.json
```

**Contains**:
- Fetch timestamp
- Date range (2025-05-30 to 2026-05-22)
- Per-ticker metadata:
  - Symbol
  - Description
  - Required for (which algorithm rule)
  - Rows fetched
  - Latest value
  - Latest date

---

## Integration with Decision Algorithm

### Data ready for:
1. **R1 (Monetary System Shift)** - Uses USD/INR daily data
2. **R2 (Real Rate Shock)** - Provides reference market data
3. **R3 (Commodity/Oil Shock)** - Uses Brent Crude daily
4. **R7 (Institutional Selling)** - Uses Nifty 50 data (FII/DII from separate scrapers)
5. **Quarterly Check** - Uses Nifty 50 & Gold for state determination
6. **Portfolio NAV** - Uses Nifty BeES ETF NAV for holdings valuation

### Next Steps:
1. Load combined CSV or Parquet into algorithm
2. Run decision rules against 12-month historical data
3. Validate state transitions
4. Compare rebalancing signals with expected outcomes
5. Backtest portfolio returns

---

## Lambda Deployment

### Package Configuration
```python
# For AWS Lambda
import yfinance_fetcher

# Lambda handler
def lambda_handler(event, context):
    fetcher = YFinanceFetcher(months_back=1)  # Fetch only new data
    all_data = fetcher.fetch_all()
    parquet_file = fetcher.save_parquet(all_data)
    
    # Upload to S3
    s3.upload_file(parquet_file, 'bucket-name', 'data/yfinance_data.parquet')
    
    return {'status': 'success', 'file': parquet_file}
```

### Scheduled Trigger
- **Frequency**: Daily (4:00 PM IST after market close)
- **Timeout**: 300 seconds
- **Memory**: 512 MB
- **Output**: S3 path to Parquet file

---

## Data Quality

### Validation Checks
- ✓ All 6 tickers return data
- ✓ 240+ days of data for each ticker
- ✓ No missing values in Close price
- ✓ Timestamps in ascending order
- ✓ Volume data realistic (>0 for stocks)

### Data Freshness
- Latest data: May 22, 2026 (trading day before fetch)
- Lag: 1-2 business days (standard for YFinance)
- Update frequency: Daily (after market close)

---

## Dependencies

```
yfinance>=0.2.0
pandas>=1.5.0
pyarrow>=11.0.0  # For Parquet
```

Install with:
```bash
pip install yfinance pandas pyarrow
```

---

## File Structure

```
src/data_collection/
├── yfinance_fetcher.py          # Main fetcher module
├── README.md                     # This file
└── output/
    ├── USDINR_data.csv          # Individual ticker CSVs
    ├── NIFTY50_data.csv
    ├── GOLD_INR_data.csv
    ├── GOLD_USD_data.csv
    ├── BRENT_CRUDE_data.csv
    ├── NIFTY_BEES_data.csv
    ├── yfinance_all_data.csv     # Combined CSV
    ├── yfinance_all_data.parquet # Combined Parquet
    └── yfinance_summary.json     # Metadata summary
```

---

## Next Phase: Web Scrapers

Phase 2 will add custom scrapers for remaining 4 data sources:
- RBI Repo Rate (https://www.rbi.org.in/)
- FII/DII Activity (https://trendlyne.com/)
- RBI Balance Sheet (https://www.rbi.org.in/)
- India CPI (https://mospi.gov.in/)

See `docs/DATA_COLLECTION_STRATEGY.md` for timeline and details.

---

**Module Status**: ✓ Phase 1 Complete  
**Last Run**: May 25, 2026, 14:44 UTC  
**Data Coverage**: 12+ months (May 2025 - May 2026)  
**Ready for**: Algorithm backtesting and Phase 2 integration
