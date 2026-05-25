# Data Collection Strategy - Decision Algorithm Implementation

**Last Updated**: May 25, 2026  
**Status**: ✓ All 10 data sources identified and validated  
**Next Phase**: Build unified pipeline combining YFinance + web scrapers

---

## Executive Summary

Successfully identified and validated all 10 required data sources for the portfolio rebalancing decision algorithm. 

- **6 sources via YFinance**: Free, daily updates, no authentication
- **4 sources via web scraping**: Accessible, HTML-based, 5-7 hours dev effort

**Total estimated development time**: 1-2 weeks for complete pipeline + testing

---

## Complete Data Collection Architecture

### Phase 1: YFinance Data (6 Sources) ✓ READY

| # | Data | Ticker | Frequency | Difficulty | Status |
|---|------|--------|-----------|-----------|--------|
| 1 | USD/INR Exchange Rate | USDINR=X | Daily | ✓ LOW | Ready |
| 2 | Nifty 50 Index | ^NSEI | Daily | ✓ LOW | Ready |
| 3 | Gold Price (INR) | GOLD | Daily | ✓ LOW | Ready |
| 4 | Gold Price (USD) | GC=F | Daily | ✓ LOW | Ready |
| 5 | Brent Crude Oil | BZ=F | Daily | ✓ LOW | Ready |
| 6 | Nifty BeES ETF | NIFTYBEES.NS | Daily | ✓ LOW | Ready |

**Implementation**:
```python
import yfinance as yf

YFINANCE_TICKERS = {
    'USDINR': 'USDINR=X',
    'NIFTY': '^NSEI',
    'GOLD_INR': 'GOLD',
    'GOLD_USD': 'GC=F',
    'BRENT': 'BZ=F',
    'NIFTY_BEES': 'NIFTYBEES.NS'
}

def fetch_yfinance_data(start_date='2025-01-01'):
    """Fetch all YFinance data at once"""
    data = {}
    for name, ticker in YFINANCE_TICKERS.items():
        data[name] = yf.download(ticker, start=start_date, progress=False)
    return data
```

**Data Requirements**:
- Historical: 12+ months for calculations
- Update frequency: Daily (automated)
- Format output: CSV + Parquet
- Lambda compatible: ✓ Yes

---

### Phase 2: Web Scrapers (4 Sources) 🚀 READY TO BUILD

#### 2.1 RBI Repo Rate
| Attribute | Value |
|-----------|-------|
| **Source** | https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx |
| **Frequency** | After MPC meetings (~6x/year) |
| **Data Format** | HTML press releases |
| **Difficulty** | ✓ LOW |
| **Dev Effort** | 1-2 hours |
| **Parser** | BeautifulSoup4 |
| **Status Code** | 200 ✓ |

**What to extract**: Latest repo rate from MPC press releases  
**Data structure**: {date, repo_rate, mpc_decision}  
**Storage**: CSV with timestamps

---

#### 2.2 FII/DII Activity (UPDATED - TrendLyne)
| Attribute | Value |
|-----------|-------|
| **Source** | https://trendlyne.com/macro-data/fii-dii/month/snapshot-month/ |
| **Frequency** | Daily |
| **Data Format** | HTML tables (24 tables with Date, FII Equity, FII Debt, FII Derivatives, FII Total) |
| **Difficulty** | ✓ LOW |
| **Dev Effort** | 2-3 hours |
| **Parser** | BeautifulSoup4 |
| **Status Code** | 200 ✓ |
| **Advantage** | Better than NSE: structured tables, no JavaScript rendering needed |

**What to extract**: FII net flows (Equity + Debt + Derivatives)  
**Data structure**: {date, fii_net_equity, fii_net_debt, fii_net_derivatives, dii_net}  
**Storage**: CSV with daily snapshots

---

#### 2.3 RBI Balance Sheet (Weekly Statistical Supplement)
| Attribute | Value |
|-----------|-------|
| **Source** | https://www.rbi.org.in/scripts/WSSView.aspx |
| **Frequency** | Weekly (usually Fridays) |
| **Data Format** | HTML tables with RBI balance sheet data |
| **Difficulty** | ✓ LOW |
| **Dev Effort** | 1-2 hours |
| **Parser** | BeautifulSoup4 + pandas |
| **Status Code** | 200 ✓ |

**What to extract**: Total Assets (excluding FCA), Foreign Currency Assets, Notes in circulation  
**Data structure**: {date, total_assets, fca, notes_circulation}  
**Storage**: CSV with weekly data points

---

#### 2.4 India CPI (MOSPI)
| Attribute | Value |
|-----------|-------|
| **Source** | https://mospi.gov.in/consumer-price-index |
| **Frequency** | Monthly |
| **Data Format** | HTML tables or PDF documents |
| **Difficulty** | ✓ LOW-MEDIUM |
| **Dev Effort** | 1-2 hours |
| **Parser** | BeautifulSoup4 or pdfplumber |
| **Status Code** | 200 ✓ |

**What to extract**: CPI Combined (All India), All Items, YoY % change  
**Data structure**: {date, cpi_value, yoy_change_pct}  
**Storage**: CSV with monthly releases

---

## Implementation Timeline

### Week 1: YFinance Integration
- [x] Test YFinance availability (COMPLETED)
- [ ] Build unified YFinance fetch function
- [ ] Create CSV/Parquet exporters
- [ ] Test 12-month historical data retrieval
- [ ] Lambda packaging and testing

**Time**: 1-2 days  
**Output**: `src/data_collection/yfinance_fetcher.py`

---

### Week 2: Web Scrapers
- [ ] Build RBI Repo Rate scraper (1-2 hours)
- [ ] Build FII/DII scraper using TrendLyne (2-3 hours)
- [ ] Build RBI Balance Sheet scraper (1-2 hours)
- [ ] Build India CPI scraper (1-2 hours)
- [ ] Rate limiting + error handling for all scrapers
- [ ] Test with historical data

**Time**: 2-3 days  
**Output**: 
- `src/data_collection/rbi_repo_rate_scraper.py`
- `src/data_collection/fii_dii_scraper.py`
- `src/data_collection/rbi_balance_sheet_scraper.py`
- `src/data_collection/mospi_cpi_scraper.py`

---

### Week 3: Unified Pipeline + Testing
- [ ] Create unified `data_collector.py` combining all sources
- [ ] Implement frequency-aware scheduling (daily, weekly, monthly, 6x/year)
- [ ] Add error handling and retry logic
- [ ] CSV and Parquet export functions
- [ ] Validation layer (data completeness, freshness)
- [ ] Backtesting with 12+ months historical data

**Time**: 2-3 days  
**Output**:
- `src/data_collection/unified_collector.py`
- `src/data_collection/data_validator.py`
- Historical data CSV files for backtesting

---

### Week 4: Lambda Deployment
- [ ] Package all scrapers for AWS Lambda
- [ ] Set up CloudWatch triggers (daily, weekly, monthly)
- [ ] S3 output configuration
- [ ] Monitoring and alerting
- [ ] Documentation for deployment

**Time**: 2-3 days

---

## Data Freshness & Update Schedule

| Source | Update Freq | Typical Lag | Lambda Trigger |
|--------|------------|-----------|-----------------|
| YFinance (6x) | Daily | 1-2 days | Daily (4 PM IST) |
| RBI Repo Rate | ~6x/year | After MPC | Manual trigger |
| FII/DII (TrendLyne) | Daily | 1 day | Daily (4:30 PM IST) |
| RBI Balance Sheet | Weekly | Next Friday | Weekly (Friday EOD) |
| India CPI | Monthly | ~20 days | Manual trigger |

---

## Testing & Validation

### Unit Tests
- [ ] Each scraper tested independently with live URLs
- [ ] Data format validation (required columns, data types)
- [ ] Error handling (timeouts, 404s, network issues)
- [ ] Rate limiting compliance

### Integration Tests
- [ ] Unified pipeline with all sources
- [ ] Data consistency across sources
- [ ] CSV/Parquet export validation
- [ ] Frequency scheduling accuracy

### Backtesting
- [ ] 12+ months historical data collection
- [ ] Decision algorithm against collected data
- [ ] State transition validation
- [ ] Portfolio rebalancing calculations

---

## Data Storage Structure

### CSV Format (for easy review)
```
date,source,data_type,value
2026-05-25,YFINANCE,USDINR,96.17
2026-05-25,YFINANCE,NIFTY50,23719.30
2026-05-25,SCRAPER,FII_NET_EQUITY,1234.56
```

### Parquet Format (for Lambda/analytics)
```
date: timestamp
source: string (YFINANCE, RBI, NSE, MOSPI)
data_type: string
value: float
unit: string (INR, points, %, etc.)
```

---

## Critical Notes for Continuation

### Known Issues & Solutions
1. **NSE FII/DII original URL returned 404**: ✓ RESOLVED with TrendLyne alternative
2. **FRED API had Brent Crude error**: ✓ SOLVED using YFinance (BZ=F)
3. **Gold ETF availability**: Used physical gold price (GOLD ticker) instead of ETF

### Dependencies
```
yfinance>=0.2.0
beautifulsoup4>=4.11.0
requests>=2.28.0
pandas>=1.5.0
lxml>=4.9.0
pdfplumber>=0.7.0  # For MOSPI if PDF parsing needed
```

### Environment Setup
```bash
pip install yfinance beautifulsoup4 requests pandas lxml pdfplumber

# For AWS Lambda deployment:
pip install aws-lambda-powertools
```

---

## Architecture Overview

```
Data Collection Pipeline
├── YFinance Module (fetch_yfinance_data)
│   ├── USDINR=X → Close price
│   ├── ^NSEI → Close price
│   ├── GOLD → Close price
│   ├── GC=F → Close price
│   ├── BZ=F → Close price
│   └── NIFTYBEES.NS → Close price
│
├── Web Scrapers Module
│   ├── RBI Repo Rate → Parse press releases
│   ├── FII/DII (TrendLyne) → Parse HTML tables
│   ├── RBI Balance Sheet → Parse WSS tables
│   └── India CPI → Parse MOSPI tables/PDFs
│
├── Unified Collector (orchestrator)
│   ├── Frequency scheduler
│   ├── Error handling & retries
│   ├── Data validation
│   └── Format converter (CSV/Parquet)
│
├── Storage Layer
│   ├── Local: CSV files (development)
│   ├── S3: Parquet files (production)
│   └── Database: Schema from Implementation_Requirements.md
│
└── Decision Algorithm
    ├── Load latest data
    ├── Calculate rules (R1, R2, R3, R5, R7)
    ├── Quarterly check (Nifty vs Gold)
    └── Generate rebalancing signals
```

---

## Next Session Checklist

When resuming this project:

1. **Check memory files** - Review project context in `/Users/ravisinghshekhawat/.claude/projects/-Users-ravisinghshekhawat-Learning-DataBricks-Project/memory/`

2. **Start with Phase 1** - Build YFinance unified fetcher
   - File: `src/data_collection/yfinance_fetcher.py`
   - Test with 12-month data retrieval
   - Export to CSV/Parquet

3. **Then Phase 2** - Build 4 custom scrapers
   - Use TrendLyne for FII/DII (not NSE)
   - BeautifulSoup4 for HTML parsing
   - Pandas for data cleaning

4. **Then Phase 3** - Unified pipeline + backtesting
   - Combine all sources
   - Test against decision algorithm
   - Validate 12+ months of data

5. **Finally Phase 4** - Lambda deployment
   - Package for AWS Lambda
   - Set up CloudWatch triggers
   - S3 Parquet output

---

## Key Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `src/scraping_tests/check_scrapability.py` | Validates all 4 sources are accessible | ✓ COMPLETE |
| `src/fred_testing/test_yfinance.py` | Validates 6 YFinance tickers | ✓ COMPLETE |
| `docs/plan/Algorithms.md` | Decision rules (R1-R7) specification | ✓ COMPLETE |
| `docs/plan/Implementation_Requirements.md` | Database schema + architecture | ✓ COMPLETE |
| `src/data_collection/` | To be created | 🚀 PENDING |

---

## Success Criteria

- [x] All 10 data sources identified
- [x] All sources tested for accessibility
- [x] Scrapability assessment complete
- [ ] YFinance unified fetcher built
- [ ] 4 custom scrapers implemented
- [ ] Unified pipeline tested
- [ ] 12+ months backtesting data collected
- [ ] Decision algorithm tested against real data
- [ ] Lambda deployment ready

---

**Status**: Ready to proceed with Phase 1 (YFinance integration) in next session.  
**Estimated total time**: 1-2 weeks for complete implementation + testing.