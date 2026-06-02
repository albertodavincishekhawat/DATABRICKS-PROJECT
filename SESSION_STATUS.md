# Current Session Status

**Last Updated**: June 2, 2026
**Branch**: `ravi-UAT` (synced with `origin/ravi-UAT`)
**Latest commits**:
- `11fb86e` — Switch R3 data source from Brent to USOIL (WTI, YFinance CL=F)
- `fa6b93b` — Codebase cleanup — remove dead code, stale docs, legacy directories
- `e6c7bba` — Wire FII collector to NSDL monthly CSV — drop DII and nsefin
- `4fe04f1` — Remove DII clause from R7 — FII-only selling signal

---

## TL;DR — Where We Are Right Now

SAD is in Draft. Two major architectural corrections applied this session. SAD review is in progress — next step is to continue section-by-section review and accept it so ADR-001–006 can be written.

**Correction 1 — Frequency is monthly, not weekly.**
**Correction 2 — Data collection runs on AWS Lambda + S3, not Databricks scrapers + DBFS.**

---

## Data Source Status

| # | Parameter | Status | Source | Notes |
|---|-----------|--------|--------|-------|
| 1 | NIFTY50 | ✅ REAL | YFinance `^NSEI` | `yfinance_daily.csv`, 1675 rows |
| 2 | USDINR | ✅ REAL | YFinance `USDINR=X` | `yfinance_daily.csv`, 1675 rows |
| 3 | Gold INR | ✅ REAL | YFinance `GOLD` | `yfinance_daily.csv`, 1675 rows |
| 4 | Gold USD | ✅ REAL | YFinance `GC=F` | `yfinance_daily.csv`, 1675 rows |
| 5 | USOIL (WTI) | ✅ REAL | YFinance CL=F | 1,609 days Jan 2020–May 2026, current to prev trading day |
| 6 | NiftyBees | ✅ REAL | YFinance `NIFTYBEES.NS` | `yfinance_daily.csv`, 1675 rows |
| 7 | CPI | ✅ REAL | MOSPI via rateinflation.com | 160 months Jan 2013–Apr 2026, base 2024=100 |
| 8 | Repo Rate | ✅ REAL + scraped daily | RBI MMO page (BS_ViewMMO.aspx) | repo = (MSF+SDF)/2, 15 entries Jan 2020–May 2026, `rbi_mmo_scraper.py` |
| 9 | FII (FPI Equity) | ✅ REAL | NSDL ASP.NET scraper | 77 months Jan 2020–May 2026 |
| 10 | ~~DII~~ | ✅ REMOVED | — | R7 redesigned as FII-only signal; DII dropped from algo |
| 11 | RBI Balance Sheet | ✅ REAL | RBI WSS XLSX scraper | 331 weekly / 77 monthly, Jan 2020–May 2026 |

---

## Active Collectors + Scrapers

| Collector | Scraper | Data File | Refresh frequency |
|---|---|---|---|
| `yfinance_collector.py` | `yfinance_scraper.py` | `yfinance_daily.csv` | Daily |
| `usoil_collector.py` | `usoil_scraper.py` | `usoil_daily.csv` | Daily |
| `repo_rate_collector.py` | `rbi_mmo_scraper.py` | `repo_rate_daily.csv` | Weekly (MMO page) |
| `cpi_collector.py` | `cpi_mospi_scraper.py` | `cpi_combined.csv` | Monthly (on/after 12th) |
| `fii_dii_collector.py` | `nsdl_fpi_scraper.py` | `fii_nsdl_monthly.csv` | Monthly (on/after 1st) |
| `rbi_balance_sheet_collector.py` | `rbi_wss_scraper.py` | `rbi_wss_monthly.csv` | Weekly (~3 min) |

```bash
# Daily
python3 -m src.data_collection.collectors.yfinance_scraper
python3 -m src.data_collection.collectors.usoil_scraper

# Weekly
python3 -m src.data_collection.collectors.rbi_mmo_scraper
python3 -m src.data_collection.collectors.rbi_wss_scraper

# Monthly
python3 -m src.data_collection.collectors.cpi_mospi_scraper
python3 -m src.data_collection.collectors.nsdl_fpi_scraper
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

## Ordered Task List

### Phase A — Documentation Cleanup ✅ COMPLETE
- [x] Delete `docs/APIs/` — FRED API, never used
- [x] Delete `docs/DATA_COLLECTION_STRATEGY.md` — stale, wrong sources
- [x] Rename `docs/plan/APIs.md` → `docs/plan/DataSources.md` — rewritten with all 10 real sources
- [x] `docs/plan/Algorithms.md` — kept and updated (owner fixed, PENDING sources resolved to YFinance)
- [x] `docs/plan/Implementation_Requirements.md` — deleted (stale, contradicted PRD, superseded by ADR-000)
- [x] `docs/plan/Decision_Algo_DB_Project_May2026.docx` — deleted (superseded by accepted PRD + ADR-000)
- [x] Update `docs/Bureaucracy/README.md` status column — PRD shows "To be written" but is Accepted

### Phase B — ADR-000 → Accepted ✅ COMPLETE
- [x] Fix backtest contradiction in Section 3 — removed "backtest results" from In Scope
- [x] Fix item numbering gap in Section 9 — renumbered 6→5, 7→6
- [x] OQ-01 resolved — standard educational disclaimer text confirmed
- [x] OQ-02 resolved — automated monthly refresh + manual trigger; scheduling platform to ADR-004
- [x] OQ-03 resolved — last known state + notice during refresh
- [x] OQ-04 resolved — platform deferred to SAD
- [x] OQ-05 resolved — Gold uses YFinance `GOLD` ticker; equity uses `NIFTYBEES.NS`
- [x] Section 6 updated — data refresh policy: automated monthly + manual on-demand; data at source frequency
- [x] Rules (R1A, R1B, R2, R3, R5, R7) and conflict matrix confirmed correct — locked
- [x] ADR-000 status → **Accepted** (June 1, 2026)
- [x] Bureaucracy README updated — PRD and ADR-000 both Accepted

### Phase C — SAD (in progress, section-by-section review)
- [ ] Review and accept `docs/SAD.md`
  - Draft written 2026-06-01. Review started 2026-06-02. **Not yet Accepted.**
  - Reviewed so far: §1 Executive Summary (corrections applied)
  - Still to review: §2 diagram, §3 stack, §4 components, §5 data flow, §6 infra, §7 security, §8 open questions

  **Corrections applied this session (all written to SAD):**
  - Frequency changed from weekly → monthly throughout
  - Data collection layer replaced: Databricks scraper notebooks + DBFS raw → AWS Lambda + Amazon S3
  - Architecture: EventBridge Scheduler triggers one parameterized Lambda function; Lambda writes CSVs to S3; Bronze notebook reads from S3
  - Lambda event payload: `{"scraper": "all|yfinance|usoil|rbi_mmo|rbi_wss|cpi|nsdl_fpi", "mode": "upsert|full_refresh"}`
  - Upsert mode: find last date in S3 → fetch only new rows → append
  - Full refresh mode: fetch Jan 2020 → today → smart merge with existing S3 data (old values kept; new data fills nulls and missing dates only; nothing overwritten)
  - §4.1 rewritten as Lambda implementation spec with ⚠ TODO marker — Lambda code not yet written
  - §6 Infrastructure: Lambda, EventBridge, S3 rows added; cost confirmed zero
  - §7 Security: S3 bucket policy + Lambda IAM role added
  - Header format note added: `.md` is working spec; formatted document with colour diagrams to be produced on acceptance

  **Lambda code — not yet written. Full spec in SAD §4.1.**
  - File to create: `src/data_collection/lambda_function.py`
  - Uses existing scraper files from `src/data_collection/collectors/`
  - Each scraper gets a `run(s3_client, bucket, mode)` interface
  - Dependencies: pandas, yfinance, requests, beautifulsoup4, curl-cffi, openpyxl, boto3

### Phase D — ADRs (blocked until SAD Accepted)
- [ ] ADR-001 — Data Collection Architecture
- [ ] ADR-002 — Data Storage Strategy
- [ ] ADR-003 — Decision Engine Implementation
- [ ] ADR-004 — Orchestration Platform
- [ ] ADR-005 — Data Quality & Synchronisation
- [ ] ADR-006 — Deployment & Environments

### Phase E — ROADMAP (blocked until all ADRs Accepted)
- [ ] Write `docs/ROADMAP.md`

### Phase F — Data Pipeline (can run in parallel with Phase B)
- [ ] Re-run monthly aggregation — verify all months complete with real data
- [ ] Implement 3 pipeline entry points:
  - `python -m src.data_collection.refresh --param <name>`
  - `python -m src.data_collection.refresh --all`
  - `python -m src.data_collection.upsert --param <name>`

### Phase G — Decision Engine (blocked until Phase D complete)
- [ ] Implement rule evaluator (R1A, R1B, R2, R3, R5, R7)
- [ ] Implement quarterly State check
- [ ] Implement conflict resolution matrix
- [ ] Implement audit log

### Phase H — Dashboard (blocked until Phase G complete)
- [ ] Build public web dashboard

---

## Session Continuity Rule

**Always update this file** before ending a session — add what changed, what was decided, and what is next. This file is the single source of truth for resuming work in a new session. Every plan, decision, and next step goes here.
