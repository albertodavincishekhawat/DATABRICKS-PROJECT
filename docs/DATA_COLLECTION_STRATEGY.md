# Data Collection Strategy - Decision Algorithm Implementation

**Last Updated**: May 25, 2026  
**Current Status**: 
- ✓ Phase 1 (YFinance) COMPLETE - 6 sources live, 1,482 rows extracted
- 🚀 Phase 2A (RBI Scraper) IN PROGRESS - 1/4 scrapers working
- ⏸ Phase 2B (JS Blockers) BLOCKED - 3/4 scrapers need Selenium/API research
- 🚫 Phase 3 BLOCKED - Cannot start until all 10 sources ready
  
**Critical Blocker**: Algorithm rules need specific data sources. Missing data blocks testing of R2, R5, R7 (3 of 5 rules)
**Next Action**: Phase 2B API research (1-2 hours) to solve TrendLyne, RBI WSS, MOSPI blockers

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

**Estimated Total**: 2-3 weeks (10-15 business days)

### Phase 1: YFinance Integration ✓ COMPLETE
- [x] Test YFinance availability 
- [x] Build unified YFinance fetch function
- [x] Create CSV/Parquet exporters
- [x] Test 12-month historical data retrieval
- [x] Lambda packaging and testing

**Completed**: May 25, 2026  
**Output**: `src/data_collection/yfinance_fetcher.py` - 1,482 rows extracted (May 2025-May 2026)
- 6 YFinance sources: USDINR=X, ^NSEI, GOLD, GC=F, BZ=F, NIFTYBEES.NS
- Formats: CSV, Parquet, JSON
- Ready for Phase 3 testing: ✓ YES

---

### Phase 2A: RBI Repo Rate Scraper 🚀 IN PROGRESS
- [x] Build RBI Repo Rate scraper (1-2 hours)
- [x] Parse RBI press releases
- [x] Extract recent repo announcements + last known rate
- [x] Create framework for manual MPC updates

**Completed**: May 25, 2026  
**Output**: `src/data_collection/scrapers.py` - 22 rows extracted, last known rate: 6.50% (April 10, 2026)
- Ready for Phase 3 testing: ✓ YES

---

### Phase 2B: Solve JavaScript-Rendering Blockers ⏸ BLOCKED
**Critical**: This must complete before Phase 3 can start

**Blockers**:
- **FII/DII (TrendLyne)**: JavaScript renders tables client-side - static HTML scraping returns no data
- **RBI Balance Sheet (WSS)**: Form-based - requires dropdown selection before data appears
- **MOSPI CPI**: Complex page structure - data may be in PDFs or dynamic content

**Investigation Required** (1-2 hours):
- [ ] Research if APIs available (MOSPI, RBI, TrendLyne public APIs)
- [ ] Check for alternative data sources
- [ ] Decide implementation path: API → Selenium → Manual updates

**Implementation** (4-6 hours if Selenium needed):
- [ ] Build FII/DII scraper (2-3 hours using TrendLyne API or Selenium)
- [ ] Build RBI Balance Sheet scraper (1-2 hours)
- [ ] Build India CPI scraper (1-2 hours)

**Data Requirements for Phase 3**:
- **R2 (Real Rate Shock Rule)**: Needs India CPI → CPI scraper REQUIRED
- **R5 (QE Regime Rule)**: Needs RBI Balance Sheet → Balance Sheet scraper REQUIRED
- **R7 (FII/DII Signal Rule)**: Needs FII/DII Activity → FII/DII scraper REQUIRED

**Time**: 1-2 hours research + 4-6 hours implementation  
**Output**: 3 additional working scrapers, all 10 sources live

---

### Phase 3: Unified Pipeline + Algorithm Testing 🚫 BLOCKED UNTIL PHASE 2B COMPLETE
**Prerequisite**: All 10 data sources must be working

- [ ] Create unified `data_collector.py` combining all sources
- [ ] Implement frequency-aware scheduling (daily, weekly, monthly, 6x/year)
- [ ] Add error handling and retry logic
- [ ] CSV and Parquet export functions
- [ ] Validation layer (data completeness, freshness)
- [ ] **Run decision algorithm on 12+ months historical data**
- [ ] Validate all 5 rules (R1, R2, R3, R5, R7) trigger correctly

**Time**: 2-3 days (after Phase 2B complete)  
**Output**:
- `src/data_collection/unified_collector.py`
- `src/data_collection/data_validator.py`
- Historical data CSV files for all 10 sources
- Backtesting results showing all 5 rules can execute

---

### Phase 4: Lambda Deployment
- [ ] Package all scrapers for AWS Lambda
- [ ] Set up CloudWatch triggers (daily, weekly, monthly, 6x/year)
- [ ] S3 output configuration
- [ ] Monitoring and alerting
- [ ] Documentation for deployment

**Time**: 2-3 days  
**Prerequisite**: Phase 3 complete with validated algorithm behavior

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

### Phase 1 ✓ COMPLETE
- [x] All 10 data sources identified
- [x] All sources tested for accessibility
- [x] Scrapability assessment complete
- [x] YFinance unified fetcher built (6/6 sources)
- [x] 12+ months historical data collected (1,482 rows)

### Phase 2A ✓ COMPLETE
- [x] RBI Repo Rate scraper working (1/4)
- [x] 22 rows extracted from RBI press releases
- [x] Manual update framework documented

### Phase 2B ⏸ BLOCKED (Requires Action)
- [ ] API research for CPI, RBI Balance Sheet, FII/DII (1-2 hours)
- [ ] Decision: API vs Selenium vs Manual updates
- [ ] 3 remaining custom scrapers implemented (FII/DII, Balance Sheet, CPI)
- [ ] All 10 data sources working

### Phase 3 🚫 BLOCKED UNTIL PHASE 2B COMPLETE
- [ ] Unified pipeline tested
- [ ] 12+ months backtesting data collected (all 10 sources)
- [ ] Decision algorithm tested against real data
- [ ] All 5 rules validated: R1 ✓, R2 ✗, R3 ✓, R5 ✗, R7 ✗
  - R1: ✓ (has Repo Rate + USD/INR)
  - R2: ✗ (needs India CPI - Phase 2B)
  - R3: ✓ (has Brent Crude)
  - R5: ✗ (needs RBI Balance Sheet - Phase 2B)
  - R7: ✗ (needs FII/DII - Phase 2B)

### Phase 4 ⏸ PENDING (After Phase 3)
- [ ] Lambda deployment ready
- [ ] CloudWatch triggers configured
- [ ] S3 Parquet output working
- [ ] Production monitoring active

---

## Critical Next Action

**Phase 2B must complete before Phase 3 can start.** The decision algorithm cannot be fully tested without:
1. India CPI (needed for R2 - Real Rate Shock)
2. RBI Balance Sheet (needed for R5 - QE Regime)
3. FII/DII Activity (needed for R7 - FII/DII Signal)

**Recommended approach**:
1. Spend 1-2 hours researching if public APIs exist for these 3 sources
2. If APIs found: integrate directly (fastest path)
3. If APIs not found: implement Selenium for JavaScript rendering (4-6 hours)
4. Then proceed to Phase 3 with complete data set

---

**Current Status**: Phase 2A complete, Phase 2B research needed.  
**Estimated remaining time**: 6-10 hours (API research + implementation)