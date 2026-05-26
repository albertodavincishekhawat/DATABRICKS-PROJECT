# Current Session Status

**Last Updated**: May 26, 2026
**Branch**: `ravi-UAT` (pushed to `origin/ravi-UAT`)
**Latest commit**: `dee07ad` — Add NSDL FPI scraper for real historical FII data

---

## TL;DR — Where We Are Right Now

User mandate: **"no synthetic data, get real data from free sources"**

We are systematically replacing every synthetic/hardcoded data source in the pipeline with a real scraper from the canonical official source. NSDL is done (real FII). RBI Balance Sheet is in progress (scraper found the data, download blocked). DII and CPI-recent are still synthetic.

**Currently working on**: RBI Balance Sheet scraper — see "In Progress" section below.

---

## Data Source Status (10 parameters)

| # | Parameter | Status | Source | Notes |
|---|-----------|--------|--------|-------|
| 1 | NIFTY50 | ✅ REAL | YFinance | Live daily |
| 2 | USDINR | ✅ REAL | YFinance | Live daily |
| 3 | Gold INR | ✅ REAL | YFinance | Live daily |
| 4 | Gold USD | ✅ REAL | YFinance | Live daily |
| 5 | Brent Crude | ✅ REAL | YFinance | Live daily |
| 6 | NiftyBees | ✅ REAL | YFinance | Live daily |
| 7 | CPI (Jan 2020 – Mar 2025) | ✅ REAL | FRED API | 63 months |
| 8 | **CPI (Apr 2025 – Apr 2026)** | ⚠️ HARDCODED | `cpi_mospi_fetcher.py` | 13 months hardcoded "known published values" — needs real MOSPI/data.gov.in scrape |
| 9 | Repo Rate | ✅ REAL + forward-fill | RBI MPC decisions | 39 real + legitimate forward-fill (rate constant between MPCs) |
| 10 | **FII (FPI Equity)** | ✅ REAL (NEW) | NSDL ASP.NET scraper | 77 months from official NSDL — committed `dee07ad` |
| 11 | **DII** | ⚠️ SYNTHETIC | `fii_dii_groww_fetcher.py` | Hardcoded approximations — NSDL has no DII (FPI = foreign only) |
| 12 | **RBI Balance Sheet** | ⚠️ SYNTHETIC | `rbi_dbie_scraper.py` | 330 weeks synthetic — DBIE scraper failed previously, RBI WSS scraper now in progress |

---

## Recent Wins (Today's Session)

1. **Real FII data via NSDL** — `src/data_collection/collectors/nsdl_fpi_scraper.py`
   - Uses ASP.NET VIEWSTATE postback to NSDL's Yearwise report
   - 77 months: 2020-01 to 2026-05
   - Verified against published values: March 2020 COVID crash = -₹61,973 Cr (exact match)
   - Output: `src/data_collection/input/fii_nsdl_monthly.csv`
   - Commit: `dee07ad`

2. **CPI aggregation bug fix** — `src/data_collection/collectors/cpi_collector.py`
   - `get_value()` was calling `.values[0]` on a numpy scalar → caught by except → returned None
   - All 76 CPI months were silently returning MISSING despite data being loaded
   - Commit: `be4aac6`

3. **Pipeline architecture added to requirements** — `docs/plan/Implementation_Requirements.md`
   - Three pipeline types defined: per-parameter full refresh, global full refresh, per-parameter monthly upsert
   - Section added before "Processing Requirements"
   - **Not yet committed** — needs commit on next session

---

## In Progress — RBI Balance Sheet Scraper

**Goal**: Replace synthetic 330-week RBI balance sheet data with real weekly Weekly Statistical Supplement (WSS) data from `rbi.org.in`.

### What's been discovered

- RBI WSS portal at `https://www.rbi.org.in/Scripts/BS_ViewWss.aspx` is ASP.NET WebForms (same pattern as NSDL)
- POST with `__VIEWSTATE` + form fields `ddlYear`, `ddlMonth`, `ddlSection=1` (Reserve Bank of India), `btnGo=Go` returns a page listing **all** historical XLSX/PDF download links (regardless of year/month filter — returns 476 total)
- Parsed 331 unique XLSX URLs covering **2020-01-03 to 2026-05-22** (every Friday)
- URL pattern: `https://rbidocs.rbi.org.in/rdocs/Wss/DOCs/1T_DDMMYYYY{hash}.XLSX`
- `1T_` = Table 1 (RBI Liabilities and Assets — exactly what we need)

### What's blocking

- Downloading individual XLSX files from `rbidocs.rbi.org.in` keeps getting **TLS connection reset** (ConnectionResetError errno 54)
- Both `requests` (Python) and `curl` fail
- Likely needs: session cookies from the parent page, slower request rate, or different TLS cipher
- Last attempted URL: `https://rbidocs.rbi.org.in/rdocs/Wss/DOCs/1T_2205202684F8791434164E6BB0FB00645143FF32.XLSX`

### Next steps on RBI

1. Try downloading inside the same `requests.Session()` that already visited `BS_ViewWss.aspx` (cookies may be required)
2. Add `Referer` header explicitly to `rbi.org.in`
3. Try `httpx` with HTTP/2 instead of `requests`
4. If still blocked, try fetching from `data.rbi.org.in` (DBIE — different host)
5. Once one XLSX downloads, parse with `pd.read_excel` to find the right cell for "Total Liabilities/Assets"
6. Loop over 331 dates, aggregate to monthly (last Friday of each month)

---

## Up Next (Priority Order)

1. **Finish RBI Balance Sheet** scraper (resolve TLS issue → loop downloads → aggregate to monthly)
2. **DII data** — investigate sources:
   - BSE Historical FII Summary: `https://www.bseindia.com/markets/Derivatives/DeriReports/FIISummaryHistorical.aspx` (got HTTP 301 — needs redirect handling)
   - AMFI monthly mutual fund flows (publicly available, monthly aggregates)
   - Moneycontrol historical archive
   - Trendlyne backend JSON API
3. **CPI Apr 2025+ real data**:
   - Option A: Register free `data.gov.in` API key (requires user action — 5 min signup at https://www.data.gov.in/help/how-use-datasets-apis)
   - Option B: MOSPI's CPI portal at `https://cpi.mospi.gov.in/` (got HTTP 302 — needs redirect)
   - Option C: World Bank API (annual only, not monthly)
4. **Wire real sources into collectors** — once all three above are real, update:
   - `fii_dii_collector.py` to read from new NSDL CSV
   - `rbi_balance_sheet_collector.py` to read from new RBI WSS CSV
   - `cpi_collector.py` to merge FRED + real MOSPI (no hardcoded values)
5. **Re-run monthly aggregation** and verify 76/76 still complete with all-real data
6. **Implement the 3 pipeline types** from requirements:
   - `python -m src.data_collection.refresh --param <name>` (per-parameter full refresh)
   - `python -m src.data_collection.refresh --all` (global full refresh)
   - `python -m src.data_collection.upsert --param <name>` (monthly incremental upsert)
7. **Commit the requirements doc update** (uncommitted right now)

---

## Key Technical Patterns Discovered

- **ASP.NET WebForms scraping**: NSDL and RBI both use this. The recipe:
  1. GET initial page, parse `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION` from hidden inputs
  2. POST back with those fields + form fields + `__EVENTTARGET` (dropdown name) or button name
  3. Use a `requests.Session()` to maintain cookies between GET and POST
  4. Set `Referer` header to the GET URL

- **`pd.read_html(StringIO(html))`**: After ASP.NET postback, the response is HTML with tables — `pandas.read_html` extracts them. Multi-level columns need flattening: `' | '.join(str(c) for c in col if 'Unnamed' not in str(c))`.

- **NSE blocking**: NSE archives (`nsearchives.nseindia.com`) return 503 from Akamai for bare requests. `nse_fiidii()` from `nsepython` works for current day only, ignores date parameter.

---

## Installed Dependencies (Today)

```
nsepython==2.97        # NSE current-day FII/DII (returns latest only)
nselib==2.5.1          # NSE historical (derivatives stats per date)
xlrd==2.0.2            # For reading older .xls files
openpyxl==3.1.5        # For reading .xlsx files
```

---

## Files Created/Modified Today

**New**:
- `src/data_collection/collectors/nsdl_fpi_scraper.py` (NSDL FII scraper) — committed
- `src/data_collection/input/fii_nsdl_monthly.csv` (77 months real FII) — committed

**Modified**:
- `src/data_collection/collectors/cpi_collector.py` — `.values[0]` bug fix — committed
- `docs/plan/Implementation_Requirements.md` — added 3 pipeline architecture section — **NOT yet committed**

**Stale docs (from yesterday — may need rewrite)**:
- `PHASE2_SCRAPER_STATUS.md`
- `PHASE3_STATUS.md`
- `DATA_SOURCES_STATUS.md`
- `FII_DII_USER_ACTION.md` (obsolete — no longer need manual download, NSDL scraper works)
- `CPI_USER_ACTION.md`

---

## How to Resume in a New Session

1. Read this file first
2. Run: `git log --oneline -5` to verify commit state matches
3. Check current state of synthetic sources by running:
   ```bash
   python3 -c "from src.data_collection.collectors.fii_dii_collector import FIIDIICollector; c = FIIDIICollector(); print(c.data.head() if c.data is not None else 'NOT LOADED')"
   ```
4. Pick up at "In Progress — RBI Balance Sheet Scraper" or "Up Next" section
5. The NSDL scraper is the working template — pattern after it for new scrapers
