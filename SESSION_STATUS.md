# Current Session Status

**Last Updated**: May 27, 2026
**Branch**: `ravi-UAT` (synced with `origin/ravi-UAT`)
**Latest commits**:
- `11fb86e` — Switch R3 data source from Brent to USOIL (WTI, YFinance CL=F)
- `fa6b93b` — Codebase cleanup — remove dead code, stale docs, legacy directories
- `e6c7bba` — Wire FII collector to NSDL monthly CSV — drop DII and nsefin
- `4fe04f1` — Remove DII clause from R7 — FII-only selling signal

---

## TL;DR — Where We Are Right Now

User mandate: **"no synthetic data, get real data from free sources"**

All 10 parameters now have real data sources. DII removed from algo (R7 is FII-only).
Codebase cleaned — dead code, stale docs, and legacy directories deleted.

---

## Data Source Status

| # | Parameter | Status | Source | Notes |
|---|-----------|--------|--------|-------|
| 1 | NIFTY50 | ✅ REAL | YFinance | Live daily |
| 2 | USDINR | ✅ REAL | YFinance | Live daily |
| 3 | Gold INR | ✅ REAL | YFinance | Live daily |
| 4 | Gold USD | ✅ REAL | YFinance | Live daily |
| 5 | USOIL (WTI) | ✅ REAL | YFinance CL=F | 1,609 days Jan 2020–May 2026, current to prev trading day |
| 6 | NiftyBees | ✅ REAL | YFinance | Live daily |
| 7 | CPI | ✅ REAL | MOSPI via rateinflation.com | 160 months Jan 2013–Apr 2026, base 2024=100 |
| 8 | Repo Rate | ✅ REAL + forward-fill | RBI MPC decisions | 39 real + legitimate forward-fill |
| 9 | FII (FPI Equity) | ✅ REAL | NSDL ASP.NET scraper | 77 months Jan 2020–May 2026 |
| 10 | ~~DII~~ | ✅ REMOVED | — | R7 redesigned as FII-only signal; DII dropped from algo |
| 11 | RBI Balance Sheet | ✅ REAL | RBI WSS XLSX scraper | 331 weekly / 77 monthly, Jan 2020–May 2026 |

---

## Active Collectors

| Collector | File | Data File |
|---|---|---|
| YFinanceCollector | `yfinance_collector.py` | live fetch |
| CPICollector | `cpi_collector.py` | `cpi_combined.csv` |
| RepoRateCollector | `repo_rate_collector.py` | hardcoded MPC decisions |
| FIIDIICollector | `fii_dii_collector.py` | `fii_nsdl_monthly.csv` |
| RBIBalanceSheetCollector | `rbi_balance_sheet_collector.py` | `rbi_wss_monthly.csv` |
| USOILCollector | `usoil_collector.py` | `usoil_daily.csv` |

---

## Scrapers (Run to Refresh Data)

```bash
# Refresh CPI (run on or after 12th of month)
python3 -m src.data_collection.collectors.cpi_mospi_scraper

# Refresh FII (monthly)
python3 -m src.data_collection.collectors.nsdl_fpi_scraper

# Refresh RBI Balance Sheet (takes ~3 min)
python3 -m src.data_collection.collectors.rbi_wss_scraper

# Refresh USOIL (daily)
python3 -m src.data_collection.collectors.usoil_scraper
```

---

## R3 Status (as of May 27, 2026)

| Metric | Value |
|---|---|
| WTI today | $92.85/bbl |
| 12m avg | $70.66/bbl |
| Ratio | 1.31 |
| Status | **CLEAR** |
| Trigger price | $127.19/bbl |

---

## Key Technical Patterns

- **ASP.NET WebForms**: GET → parse `__VIEWSTATE/__VIEWSTATEGENERATOR/__EVENTVALIDATION` → POST with `Referer` + form fields. Use `requests.Session()`.
- **F5 bot detection bypass**: `curl_cffi` with `impersonate='chrome120'` works on RBI's WSS portal POST.
- **rbidocs.rbi.org.in TLS reset**: Fixed by adding `Referer: https://www.rbi.org.in/` to download requests.
- **rateinflation.com**: Simple HTML table, `pd.read_html()`, no bot detection.
- **YFinance**: All market data (equities, FX, commodities) via single consistent interface.

---

## Up Next (Priority Order)

1. **Re-run monthly aggregation** — verify all months complete with real data
2. **Implement 3 pipeline types** from requirements doc:
   - `python -m src.data_collection.refresh --param <name>`
   - `python -m src.data_collection.refresh --all`
   - `python -m src.data_collection.upsert --param <name>`
