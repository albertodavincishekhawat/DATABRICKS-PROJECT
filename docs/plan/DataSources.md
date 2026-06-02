# Data Sources — How Each Parameter Is Sourced

This document defines exactly how each of the 10 required data parameters is obtained. All sources are free and publicly accessible. No API keys, no commercial data subscriptions.

---

## Summary Table

| # | Parameter | Frequency | Source | Method | Collector |
|---|-----------|-----------|--------|--------|-----------|
| 1 | NIFTY50 Index | Daily | YFinance (`^NSEI`) | Scrape → CSV | `yfinance_scraper.py` → `yfinance_collector.py` |
| 2 | USD/INR Exchange Rate | Daily | YFinance (`USDINR=X`) | Scrape → CSV | `yfinance_scraper.py` → `yfinance_collector.py` |
| 3 | Gold INR | Daily | YFinance (`GOLD`) | Scrape → CSV | `yfinance_scraper.py` → `yfinance_collector.py` |
| 4 | Gold USD | Daily | YFinance (`GC=F`) | Scrape → CSV | `yfinance_scraper.py` → `yfinance_collector.py` |
| 5 | WTI Crude Oil (USOIL) | Daily | YFinance (`CL=F`) | Library call + CSV seed | `usoil_collector.py` |
| 6 | NiftyBEES ETF | Daily | YFinance (`NIFTYBEES.NS`) | Scrape → CSV | `yfinance_scraper.py` → `yfinance_collector.py` |
| 7 | India CPI | Monthly | MOSPI via rateinflation.com | HTML scrape (`pd.read_html`) | `cpi_collector.py` |
| 8 | RBI Repo Rate | Daily (derived) | RBI Money Market Operations page | Scrape MSF + SDF → repo = (MSF+SDF)/2 | `rbi_mmo_scraper.py` → `repo_rate_collector.py` |
| 9 | FII Net Equity Flows | Monthly | NSDL FPI Yearwise data | ASP.NET WebForms scrape | `fii_dii_collector.py` |
| 10 | RBI Balance Sheet | Weekly | RBI Weekly Statistical Supplement (WSS) | F5-bypass POST scrape (curl_cffi) | `rbi_balance_sheet_collector.py` |

---

## 1. NIFTY50 Index

- **What it provides**: Daily closing price of the Nifty 50 index
- **Source**: Yahoo Finance via the `yfinance` Python library
- **Ticker**: `^NSEI`
- **Frequency**: Daily (trading days only)
- **Lag**: Previous trading day
- **Data file**: `src/data_collection/input/yfinance_daily.csv` (column: `NIFTY50`)
- **How to refresh**: `python3 -m src.data_collection.collectors.yfinance_scraper`
- **Used by**: R7 (quarterly base State calculation via 6-month performance differential)

---

## 2. USD/INR Exchange Rate

- **What it provides**: Daily USD/INR spot rate (how many INR per 1 USD)
- **Source**: Yahoo Finance via the `yfinance` Python library
- **Ticker**: `USDINR=X`
- **Frequency**: Daily
- **Lag**: Previous trading day
- **Data file**: `src/data_collection/input/yfinance_daily.csv` (column: `USDINR`)
- **How to refresh**: `python3 -m src.data_collection.collectors.yfinance_scraper`
- **Used by**: R1B (INR depreciation vs USD over 6 months)

---

## 3. Gold INR

- **What it provides**: Daily Gold price in Indian Rupees
- **Source**: Yahoo Finance via the `yfinance` Python library — ticker `GOLD`
- **Ticker**: `GOLD`
- **Frequency**: Daily
- **Lag**: Previous trading day
- **Data file**: `src/data_collection/input/yfinance_daily.csv` (column: `GOLD_INR`)
- **How to refresh**: `python3 -m src.data_collection.collectors.yfinance_scraper`
- **Used by**: Quarterly base State calculation (6-month Gold ETF return)

---

## 4. Gold USD

- **What it provides**: Daily Gold price in US Dollars (per troy ounce)
- **Source**: Yahoo Finance via the `yfinance` Python library
- **Ticker**: `GC=F` (Gold futures, front month)
- **Frequency**: Daily
- **Lag**: Previous trading day
- **Data file**: `src/data_collection/input/yfinance_daily.csv` (column: `GOLD_USD`)
- **How to refresh**: `python3 -m src.data_collection.collectors.yfinance_scraper`
- **Used by**: Reference / cross-check for Gold INR calculation

---

## 5. WTI Crude Oil (USOIL)

- **What it provides**: Daily WTI crude oil closing price in USD per barrel
- **Source**: Yahoo Finance via the `yfinance` Python library
- **Ticker**: `CL=F` (WTI crude futures, front month)
- **Frequency**: Daily
- **Lag**: Previous trading day
- **Seed data**: `src/data_collection/input/usoil_daily.csv` — 1,609 days Jan 2020–May 2026
- **How to refresh**: `python3 -m src.data_collection.collectors.usoil_scraper`
- **Used by**: R3 (oil ratio = today's price / 12-month rolling average)

---

## 6. NiftyBEES ETF

- **What it provides**: Daily closing price of NiftyBEES — the proxy for Nifty ETF held by the investor
- **Source**: Yahoo Finance via the `yfinance` Python library
- **Ticker**: `NIFTYBEES.NS`
- **Frequency**: Daily (trading days only)
- **Lag**: Previous trading day
- **Data file**: `src/data_collection/input/yfinance_daily.csv` (column: `NIFTYBEES`)
- **How to refresh**: `python3 -m src.data_collection.collectors.yfinance_scraper`
- **Used by**: Quarterly base State calculation (6-month equity ETF return)

---

## 7. India CPI (Consumer Price Index)

- **What it provides**: Monthly India CPI inflation rate (base year 2024 = 100), published by MOSPI
- **Source**: rateinflation.com — scrapes MOSPI data, no bot detection, simple HTML table
- **Method**: `pd.read_html()` — no authentication required
- **Frequency**: Monthly (published on or after the 12th of the following month)
- **Data file**: `src/data_collection/input/cpi_combined.csv` — 160 months Jan 2013–Apr 2026
- **How to refresh**: `python3 -m src.data_collection.collectors.cpi_mospi_scraper` (run on or after 12th of the month)
- **Used by**: R2 (real rate = repo rate − CPI)

---

## 8. RBI Repo Rate

- **What it provides**: The RBI policy repo rate, derived daily from the Money Market Operations report
- **Source**: RBI Money Market Operations page — `rbi.org.in/Scripts/BS_ViewMMO.aspx`
- **Method**: Scrape MSF and SDF rates from the daily MMO report. The RBI corridor is always ±25bps from the policy repo rate, so: `repo rate = (MSF + SDF) / 2`. No hardcoding.
- **Frequency**: Published every working day. Rate only changes at MPC meetings (~6 per year) but the source is refreshed daily so no manual updates needed after meetings.
- **Data file**: `src/data_collection/input/repo_rate_daily.csv` — columns: date, msf_rate, sdf_rate, repo_rate
- **How to refresh**: `python3 -m src.data_collection.collectors.rbi_mmo_scraper`
- **Used by**: R1A (rate cycle), R2 (real rate = repo rate − CPI)
- **Note**: Confirmed working — May 26 2026: MSF=5.50%, SDF=5.00% → repo=5.25%

---

## 9. FII Net Equity Flows (Foreign Portfolio Investors)

- **What it provides**: Monthly net equity investment by Foreign Portfolio Investors (FPIs) in India — equity cash segment only
- **Source**: NSDL FPI Yearwise data portal (`nsdl.co.in`)
- **Method**: ASP.NET WebForms scrape — GET to parse `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION` tokens, then POST with `Referer` header and form fields. Uses `requests.Session()`.
- **Frequency**: Monthly (available by the 1st of the following month)
- **Data file**: `src/data_collection/input/fii_nsdl_monthly.csv` — 77 months Jan 2020–May 2026
- **How to refresh**: `python3 -m src.data_collection.collectors.nsdl_fpi_scraper`
- **Used by**: R7 (3-month cumulative FII outflow vs peak inflow)

---

## 10. RBI Balance Sheet (Weekly Statistical Supplement)

- **What it provides**: Weekly RBI balance sheet — Total Assets, Foreign Currency Assets (FCA), Notes in Circulation. Used to compute YoY balance sheet growth excluding FCA.
- **Source**: RBI Weekly Statistical Supplement (WSS), Table 1 — published at `rbidocs.rbi.org.in`
- **Method**: Two-step scrape — (1) GET the WSS portal to find the latest publication link, (2) POST to download the XLSX. Requires `curl_cffi` with `impersonate='chrome120'` to bypass F5 bot detection. Download request requires `Referer: https://www.rbi.org.in/` to avoid TLS reset.
- **Frequency**: Weekly (published each Friday, within 5 days)
- **Data file**: `src/data_collection/input/rbi_wss_monthly.csv` — 331 weekly / 77 monthly entries, Jan 2020–May 2026
- **How to refresh**: `python3 -m src.data_collection.collectors.rbi_wss_scraper` (takes ~3 minutes)
- **Used by**: R5 (YoY balance sheet growth excluding FCA)

---

## Refresh Schedule

| When to run | Parameters to refresh |
|-------------|----------------------|
| Each trading day | All YFinance params + WTI Oil: `python3 -m src.data_collection.collectors.yfinance_scraper` and `usoil_scraper` |
| On or after 1st of the month | FII flows (NSDL scraper) |
| On or after 12th of the month | CPI (MOSPI scraper) |
| Within 5 days of each Friday | RBI Balance Sheet (WSS scraper) |
| Each working day | Repo Rate (MMO scraper — picks up rate changes automatically after MPC meetings) |

---

## Technical Notes

| Challenge | Solution |
|-----------|----------|
| NSDL ASP.NET WebForms | GET → parse hidden form tokens → POST with `Referer` header using `requests.Session()` |
| RBI WSS F5 bot detection | `curl_cffi` with `impersonate='chrome120'` |
| RBI download TLS reset | Add `Referer: https://www.rbi.org.in/` to download request headers |
| rateinflation.com | No bot detection — `pd.read_html()` sufficient |
| Repo rate between meetings | Forward-fill is legitimate — rate is legally fixed between MPC decisions |
