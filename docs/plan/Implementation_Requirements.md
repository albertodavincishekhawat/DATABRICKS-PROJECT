# Implementation Requirements - Data & Infrastructure Setup

**Project**: Decision Algo DB Project  
**Version**: May 2026  
**Created**: May 25, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Data Requirements Summary](#data-requirements-summary)
3. [Confirmed Data Sources](#confirmed-data-sources)
4. [Pending Data Sources](#pending-data-sources)
5. [Data Infrastructure](#data-infrastructure)
6. [Processing Requirements](#processing-requirements)
7. [Database Schema](#database-schema)
8. [Testing & Validation](#testing--validation)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

To implement the Decision Algorithm system, we need to establish:
1. **Real-time data pipelines** for 7+ economic indicators
2. **Data storage** with historical tracking
3. **Calculation engine** for formula execution
4. **Monitoring & alerting** system
5. **Logging & audit trail** for all decisions

This document outlines what data is needed, where it comes from, and how to set it up.

---

## Data Requirements Summary

### Essential Data Feeds (By Rule)

| Rule | Data Required | Frequency | Status |
|------|---------------|-----------|--------|
| R1 | RBI Repo Rate, USD/INR | After each MPC, Daily | ✓ Confirmed |
| R2 | RBI Repo Rate, CPI | Monthly MPC, Monthly CPI | ✓ Confirmed |
| R3 | Brent Crude Price | Daily | ⏳ **PENDING** |
| R5 | RBI Balance Sheet | Weekly | ✓ Confirmed |
| R7 | FII Activity | Monthly | ✓ Confirmed |
| Quarterly Check | Nifty Index, Gold INR Price | Daily | ⏳ **PENDING** |
| SIP Execution | Portfolio NAV, Gold ETF Price, Nifty ETF Price | Daily | ⏳ **PENDING** |

---

## Confirmed Data Sources

### 1. RBI Repo Rate & Monetary Policy

**Endpoint**: https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx

**Frequency**: After each MPC meeting (typically 6 meetings/year)

**Data Points**:
- Repo Rate (%)
- Reverse Repo Rate (%)
- Policy stance (Hawkish, Neutral, Dovish)
- MPC meeting date

**Implementation**:
```python
# Pseudo-code for data collection
def fetch_rbi_repo_rate():
    url = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
    # Parse press release for latest repo rate
    # Extract: meeting_date, new_rate, direction
    return {
        'date': meeting_date,
        'rate': repo_rate,
        'direction': 'HIKING' or 'CUTTING'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD format)
- `rate` (percentage)
- `direction` (HIKING/CUTTING/PAUSE)

---

### 2. USD/INR Exchange Rate

**Endpoint**: https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx

**Frequency**: Daily (business days only)

**Data Points**:
- USD/INR spot rate (RBI reference rate)
- Date
- Historical rates (180-day lookback required)

**Implementation**:
```python
def fetch_usdinr_rate(date=None):
    # Fetch RBI reference rate
    # If date not provided, fetch latest
    # Must maintain 6-month historical data
    return {
        'date': date,
        'usdinr': spot_rate,
        'source': 'RBI'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `usdinr` (numerical rate, e.g., 82.45)

---

### 3. India Headline CPI

**Endpoint**: https://mospi.gov.in/consumer-price-index

**Frequency**: Monthly (released monthly)

**Data Points**:
- CPI Combined (All India)
- All Items category
- YoY % change
- Month-end

**Implementation**:
```python
def fetch_india_cpi():
    # Source: Ministry of Statistics and Programme Implementation
    # CPI Series: CPI Combined (All India), All Items
    return {
        'date': month_end_date,
        'cpi_yoy_pct': inflation_rate,
        'source': 'MOSPI'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `cpi_yoy_pct` (percentage, e.g., 4.5)

---

### 4. RBI Balance Sheet (Weekly)

**Source**: RBI Weekly Statistical Supplement (WSS), Table 1

**Endpoint**: https://www.rbi.org.in/scripts/WSSView.aspx

**Frequency**: Weekly (typically Fridays)

**Data Points**:
- Total Liabilities/Assets (Rs. Crore)
- Foreign Currency Assets (FCA) - **TO EXCLUDE**
- Gold holdings
- Data as of specific week-end date

**Implementation**:
```python
def fetch_rbi_balance_sheet():
    # Source: RBI WSS Table 1
    # CRITICAL: Exclude FCA from calculation
    # FCA line: WSS Table 3, Foreign Exchange Reserves section
    return {
        'date': week_end_date,
        'total_assets_excl_fca': bs_value,
        'fca_value': fca_value,  # for reference/logging
        'source': 'RBI WSS Table 1'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD, week-end date)
- `total_assets_excl_fca` (Rs. Crore)
- `fca_value` (Rs. Crore, for audit trail)

---

### 5. FII Activity

**Endpoint**: https://www.fpi.nsdl.co.in/Reports/Yearwise.aspx?RptType=6

**Frequency**: Monthly (NSDL publishes monthly FPI net investment totals)

**Data Points**:
- FII Net Equity Investment (Rs. Crore/month)
- Equity cash segment only (exclude debt, hybrid)

**Implementation**:
```python
def fetch_fii_activity(year):
    # Source: NSDL FPI Yearwise report
    # CRITICAL: Equity cash segment ONLY
    # Exclude debt, hybrid instruments
    return {
        'date': month_end_date,
        'fii_net': fii_amount,  # positive = inflow, negative = outflow
        'source': 'NSDL'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD, last day of month)
- `fii_net` (Rs. Crore, signed)

---

## Pending Data Sources

### ⏳ 1. Brent Crude Oil Price (CRITICAL)

**Current Status**: PENDING - Primary source to be identified and tested

**Requirements**:
- Daily spot price in USD/barrel
- Historical data (365+ days for 12-month average)
- Reliable, real-time feed required for R3 trigger

**Candidate Sources**:
1. **US Energy Information Administration (EIA)**
   - URL: https://www.eia.gov/petroleum/data.php
   - Data: Daily Brent Crude spot price
   - Lag: ~1 day
   - Reliability: High

2. **World Bank Commodity Prices**
   - URL: https://www.worldbank.org/en/research/commodity-markets
   - Data: Monthly/Daily Brent prices
   - Reliability: High

3. **CME (Chicago Mercantile Exchange)**
   - Brent crude futures prices (proxy for spot)
   - Real-time data
   - Reliability: Very high

4. **Oil & Gas Journal**
   - Daily Brent assessments
   - Reliability: High

**Recommended Approach**:
```
Primary: EIA API (free, reliable)
Backup: World Bank data (if EIA unavailable)
Fallback: Manual entry from Bloomberg/Reuters terminals
```

**Data Collection Implementation**:
```python
def fetch_brent_crude_price(date=None):
    # PRIMARY: EIA API
    try:
        return fetch_from_eia_api(date)
    except:
        # FALLBACK: World Bank
        return fetch_from_worldbank(date)
    
    # Returns: {'date': YYYY-MM-DD, 'brent_price': USD/barrel}
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `brent_price` (USD/barrel, decimal)

---

### ⏳ 2. Nifty 50 Index Price (CRITICAL)

**Current Status**: PENDING - Primary source to be identified and tested

**Requirements**:
- Daily closing price
- Historical data (6+ months for quarterly calculations)
- For 6-month differential calculations

**Candidate Sources**:
1. **NSE (National Stock Exchange)**
   - URL: https://www.nseindia.com/
   - Nifty 50 daily closing price
   - Reliability: Highest (primary exchange)

2. **BSE (Bombay Stock Exchange)**
   - Nifty futures proxy
   - Reliability: High

3. **Financial Data APIs**
   - Alpha Vantage, IEX Cloud, etc.
   - Reliability: High, but fee-based

**Recommended Approach**:
```
Primary: NSE direct API/website scraping
Backup: Financial API (Alpha Vantage, etc.)
```

**Data Collection Implementation**:
```python
def fetch_nifty_price(date=None):
    # PRIMARY: NSE
    return {
        'date': date,
        'nifty_close': closing_price,
        'nifty_open': opening_price,
        'nifty_high': high_price,
        'nifty_low': low_price,
        'volume': volume,
        'source': 'NSE'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `nifty_close` (closing price)

---

### ⏳ 3. Gold INR Price (CRITICAL)

**Current Status**: PENDING - Primary source to be identified and tested

**Requirements**:
- Daily closing price in INR per gram (or per troy ounce, normalized)
- Historical data (6+ months)
- For 6-month differential calculations
- Should track physical gold price (spot rate)

**Candidate Sources**:
1. **IBJA (Indian Bullion & Jewellers Association)**
   - URL: https://www.ibja.in/
   - Daily gold rates (per gram)
   - Reliability: Very High (official association)

2. **MCX (Multi Commodity Exchange)**
   - Gold futures prices
   - URL: https://www.mcxindia.com/
   - Reliability: High

3. **RBI Reference Rates**
   - Gold holdings at RBI
   - Not direct price data, but related

4. **Reuters/Bloomberg**
   - INR/gram gold prices
   - Fee-based, but reliable

**Recommended Approach**:
```
Primary: IBJA daily rates (free, official)
Backup: MCX gold futures (normalized)
```

**Data Collection Implementation**:
```python
def fetch_gold_inr_price(date=None):
    # PRIMARY: IBJA
    return {
        'date': date,
        'gold_inr_per_gram': price,  # or normalize from per_tola
        'source': 'IBJA'
    }
    
    # Normalization if needed:
    # 1 tola = 11.666 grams
    # Use consistent unit (per gram recommended)
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `gold_inr_per_gram` (INR, decimal)

---

### ⏳ 4. ETF Prices (Gold ETF & Nifty ETF)

**Current Status**: PENDING - Source to be identified

**Requirements**:
- Daily NAV (Net Asset Value) for:
  - **Gold ETF**: e.g., SBI Gold ETF, ICICI Gold ETF
  - **Nifty ETF**: e.g., Nifty BeES, ICICI Nifty ETF
- For portfolio rebalancing calculations

**Candidate Sources**:
1. **BSE/NSE**
   - Direct ETF prices
   - Daily updates

2. **Fund House Websites**
   - Official NAV data
   - Reliable

3. **Financial Data APIs**
   - Alpha Vantage, IEX Cloud, etc.

**Data Collection Implementation**:
```python
def fetch_etf_prices(gold_etf_symbol, nifty_etf_symbol):
    return {
        'date': date,
        'gold_etf_nav': nav_price,
        'nifty_etf_nav': nav_price,
        'source': 'BSE/NSE'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `gold_etf_nav` (price per unit)
- `nifty_etf_nav` (price per unit)

---

### ⏳ 5. Portfolio NAV

**Current Status**: PENDING - Internal calculation required

**Requirements**:
- Monthly total portfolio value (rupees)
- Used for SIP amount and rebalancing calculations
- As of month-end date

**Data Collection Implementation**:
```python
def calculate_portfolio_nav(date):
    # Calculate from holdings + current prices
    gold_units = portfolio['gold_units']
    nifty_units = portfolio['nifty_units']
    
    gold_price = fetch_gold_etf_price(date)
    nifty_price = fetch_nifty_etf_price(date)
    
    nav = (gold_units * gold_price) + (nifty_units * nifty_price)
    return {
        'date': date,
        'nav': nav,
        'source': 'Internal calculation'
    }
```

**Required Fields**:
- `date` (YYYY-MM-DD)
- `nav` (portfolio value in INR)

---

## Data Infrastructure

### Database Schema

```sql
-- Core Tables

CREATE TABLE repo_rate (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    rate DECIMAL(5,2) NOT NULL,
    direction VARCHAR(10),  -- HIKING, CUTTING, PAUSE
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE usdinr_rate (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    rate DECIMAL(8,4) NOT NULL,
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE cpi_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    cpi_yoy_pct DECIMAL(5,2) NOT NULL,
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE rbi_balance_sheet (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    total_assets_excl_fca BIGINT NOT NULL,  -- Rs. Crore
    fca_value BIGINT,
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE fii_activity (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    fii_net BIGINT NOT NULL,  -- Rs. Crore, signed
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE brent_crude_price (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    price DECIMAL(8,3) NOT NULL,  -- USD/barrel
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE nifty_price (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    volume BIGINT,
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE gold_inr_price (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    price_per_gram DECIMAL(8,2) NOT NULL,  -- INR
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

CREATE TABLE etf_prices (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    gold_etf_nav DECIMAL(10,2) NOT NULL,
    nifty_etf_nav DECIMAL(10,2) NOT NULL,
    source VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date),
    INDEX(date)
);

CREATE TABLE portfolio_nav (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    nav BIGINT NOT NULL,  -- INR
    gold_units DECIMAL(12,2),
    nifty_units DECIMAL(12,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(date)
);

-- Logging Tables

CREATE TABLE rule_triggers (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    rule_id VARCHAR(10),  -- R1, R2, R3, R5, R7
    trigger_type VARCHAR(50),  -- TRIGGERED, YELLOW, EXIT
    metric_values JSON,  -- Store all calculated metrics
    action_taken VARCHAR(500),
    portfolio_state_before VARCHAR(50),
    portfolio_state_after VARCHAR(50),
    INDEX(date),
    INDEX(rule_id)
);

CREATE TABLE rebalancing_actions (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    rule_triggered VARCHAR(10),
    action_type VARCHAR(50),  -- BUY, SELL, HOLD
    asset VARCHAR(20),  -- GOLD, NIFTY
    amount_inr BIGINT,
    units DECIMAL(12,2),
    price_at_execution DECIMAL(10,2),
    execution_status VARCHAR(50),  -- PENDING, EXECUTED, FAILED
    INDEX(date)
);

CREATE TABLE state_history (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    current_state VARCHAR(20),  -- STATE_1, STATE_2, STATE_3
    differential DECIMAL(8,2),
    nifty_6m_return DECIMAL(8,2),
    gold_6m_return DECIMAL(8,2),
    active_rules JSON,  -- List of active rules at this state
    INDEX(date)
);
```

### Data Retention

| Data | Retention Period | Purpose |
|------|------------------|---------|
| Daily market data | 5+ years | Historical analysis, 180-day lookback |
| Weekly RBI data | 5+ years | YoY balance sheet calculations |
| Monthly CPI | 5+ years | Real rate calculations |
| Rule triggers | 3+ years | Audit trail, performance analysis |
| Rebalancing actions | Permanent | Compliance, transaction history |

---

## Data Pipeline Architecture

Three distinct pipeline types are required to manage data ingestion:

### Pipeline Type 1: Per-Parameter Full Refresh (On-Demand)

**Purpose**: Rebuild the complete history for a single data parameter from scratch, up to today.

**Trigger**: Manual / on-demand (user selects which parameter to refresh)

**Behavior**:
- Wipes existing data for the selected parameter
- Re-fetches the entire historical range from the source (2020-01 → today)
- Replaces the parameter's input CSV / table
- Re-runs monthly aggregation for that parameter

**Use cases**:
- Source schema changed and historical reparse is needed
- A specific parameter is suspected to be stale or corrupted
- Initial backfill when adding a new data source

**Required**: One refresh script per parameter (10 total — Nifty50, USDINR, Gold INR, Gold USD, Brent, NiftyBees, CPI, Repo Rate, FII, RBI Balance Sheet).

**Interface**: `python -m src.data_collection.refresh --param <name>`

---

### Pipeline Type 2: Global Full Refresh (On-Demand)

**Purpose**: Rebuild the complete history for **all** data parameters in one run, up to today.

**Trigger**: Manual / on-demand (no parameter selection — runs everything)

**Behavior**:
- Iterates through all per-parameter full-refresh pipelines (Type 1)
- Re-runs the monthly aggregator at the end to regenerate aligned monthly CSVs and master_dates
- Produces a single quality report covering all sources

**Use cases**:
- Initial system setup / fresh clone
- After major code changes affecting multiple collectors
- Disaster recovery / data integrity restoration

**Interface**: `python -m src.data_collection.refresh --all`

---

### Pipeline Type 3: Per-Parameter Monthly Upsert (Scheduled)

**Purpose**: Append only the newest data (latest month) for a single parameter, leaving historical rows untouched.

**Trigger**: Scheduled — runs monthly (1st of each month, after month-end data is published)

**Behavior**:
- Reads the latest date present in the existing input CSV
- Fetches only data from `latest_date + 1 day` onward
- Upserts new rows (insert if missing, update if same date already exists with different value — handles late-published revisions)
- Re-runs monthly aggregation incrementally for the affected month

**Use cases**:
- Routine monthly data refresh
- Keeping the system current without re-downloading history
- Bandwidth-efficient daily/weekly cron jobs

**Required**: One upsert script per parameter (10 total).

**Interface**: `python -m src.data_collection.upsert --param <name>`

**Idempotency requirement**: Running the upsert pipeline twice in the same day must produce the same result (no duplicate rows).

---

### Pipeline Type Summary

| # | Pipeline                       | Scope        | Trigger    | Behavior        |
|---|--------------------------------|--------------|------------|-----------------|
| 1 | Per-parameter full refresh     | 1 parameter  | On-demand  | Wipe + rebuild  |
| 2 | Global full refresh            | All 10       | On-demand  | Wipe + rebuild  |
| 3 | Per-parameter monthly upsert   | 1 parameter  | Scheduled  | Append only     |

---

## Processing Requirements

### Data Pipeline Components

```
Data Collection (Hourly/Daily)
        ↓
Data Validation & Transformation
        ↓
Database Storage
        ↓
Metric Calculation Engine
        ↓
Rule Trigger Detection
        ↓
Conflict Resolution
        ↓
Action Queue
        ↓
Execution & Logging
```

### Required Calculations

1. **Weekly (Every Monday)**
   - R3 ratio: `brent_today / brent_12m_avg`
   - R1 pct_change: `ABS(rate_current - rate_baseline) / rate_baseline * 100`
   - R1 inr_depreciation: `(usdinr_today - usdinr_6m_ago) / usdinr_6m_ago * 100`
   - R2 real_rate: `repo_rate - cpi_yoy`
   - R5 bs_yoy: `(bs_current - bs_year_ago) / bs_year_ago * 100`
   - R7 fii_peak_inflow, fii_3m_cumulative

2. **Monthly (1st of month)**
   - Brent 12-month average recalculation
   - FII peak inflow and outflow threshold recalculation
   - SIP amount calculation based on portfolio NAV

3. **Quarterly (Jan 1, Apr 1, Jul 1, Oct 1)**
   - 6-month returns: Nifty and Gold
   - State determination based on differential
   - Full rebalancing with 75% shift rule

### Computational Requirements

- **Processing Time**: < 15 minutes for weekly decision tree
- **Latency**: < 1 hour from data availability to decision
- **Uptime**: 99.9% (critical infrastructure)
- **Scalability**: Handle 10+ years of historical data

---

## Testing & Validation

### Data Validation Rules

```python
# Repo Rate validation
assert 0 < repo_rate < 15, "Repo rate out of normal range"

# USD/INR validation
assert 70 < usdinr < 100, "USD/INR out of normal range"

# CPI validation
assert -5 < cpi_yoy < 20, "CPI YoY out of normal range"

# Brent validation
assert 20 < brent < 200, "Brent price out of normal range"

# FII validation
assert -100000 < fii_net < 100000, "FII net flow out of range"
```

### Source Verification

For each pending source:
1. **Source Availability**: Verify endpoint accessibility
2. **Data Format**: Confirm data structure and units
3. **Historical Depth**: Ensure 180-day minimum historical data
4. **Update Frequency**: Confirm data freshness/lag
5. **Redundancy**: Establish backup source

### Backtesting

Before production deployment:
1. Collect 12+ months of historical data
2. Run algorithm on past 6 months of data
3. Verify against actual market movements
4. Validate rule trigger accuracy
5. Check conflict resolution logic
6. Document edge cases and exceptions

---

## Implementation Roadmap

### Phase 1: Core Data Setup (Weeks 1-2)

- [ ] Confirm Brent crude oil price source
- [ ] Confirm Nifty index price source
- [ ] Confirm Gold INR price source
- [ ] Establish API connections for all sources
- [ ] Create database schema
- [ ] Build data collection scripts

### Phase 2: Data Pipeline (Weeks 3-4)

- [ ] Implement daily data collection
- [ ] Set up hourly/weekly refresh schedules
- [ ] Add data validation & error handling
- [ ] Create data quality dashboards
- [ ] Test all 7 data sources in parallel
- [ ] Establish 12-month historical data baseline

### Phase 3: Calculation Engine (Weeks 5-6)

- [ ] Implement all metric calculations
- [ ] Build weekly decision tree logic
- [ ] Create quarterly check algorithm
- [ ] Set up rule trigger detection
- [ ] Implement conflict resolution matrix
- [ ] Add comprehensive logging

### Phase 4: Testing & Validation (Weeks 7-8)

- [ ] Backtest on historical data (6 months)
- [ ] Verify all rule triggers
- [ ] Test conflict resolution scenarios
- [ ] Validate calculations against manual checks
- [ ] Document edge cases
- [ ] Create test suite

### Phase 5: Monitoring & Execution (Weeks 9-10)

- [ ] Set up alert system for rule triggers
- [ ] Create execution queue for actions
- [ ] Build portfolio tracking dashboard
- [ ] Implement audit logging
- [ ] Create operational runbooks
- [ ] Train operations team

### Phase 6: Production Deployment (Week 11+)

- [ ] Deploy to production environment
- [ ] Enable live monitoring
- [ ] Execute first manual test transaction
- [ ] Monitor for 2+ weeks before full automation
- [ ] Adjust thresholds if needed
- [ ] Go live with automated execution

---

## Critical Success Factors

1. **Data Quality**: All 7 data sources must be reliable and real-time
2. **Latency**: Decision-to-execution must be < 1 hour
3. **Accuracy**: Formula calculations must match algorithm specification exactly
4. **Auditability**: All decisions and actions must be logged with full trail
5. **Redundancy**: Backup sources for all critical data feeds
6. **Testing**: Comprehensive backtesting before production
7. **Monitoring**: Real-time alerts for anomalies

---

## Risk Mitigation

### Data Unavailability

| Source | Contingency Plan |
|--------|-----------------|
| Brent Crude | Use Week 1 average or previous day's price |
| Nifty Price | Hold position, rebalance when data available |
| Gold INR | Use spot price from IBJA if ETF price unavailable |
| FII Data | Use previous month's data with lag flag |
| RBI Data | Weekly data, can use prior week if delayed |
| CPI | Monthly data, use prior month if delayed |

### System Failures

- **Database Down**: Queue decisions in-memory, replay when recovered
- **Data Pipeline Failure**: Manual data entry with 2-person verification
- **Calculation Error**: Dual-system verification before execution
- **Network Outage**: Store last 7 days of data locally for calculations

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| Data Availability | > 99.5% | % of expected data points received |
| Calculation Accuracy | 100% | Against manual verification |
| Rule Trigger Accuracy | 100% | Against backtested results |
| Processing Latency | < 15 min | Time from data to decision |
| Rebalancing Execution | < 1 hour | Time from trigger to execution |
| Audit Trail Completeness | 100% | All actions logged with full context |

---

**Document Status**: Ready for Implementation  
**Last Updated**: May 25, 2026  
**Next Steps**: Identify and test pending data sources
