# Phase 2: Web Scraper Development Status

**Date**: May 25, 2026  
**Overall Status**: 1/4 scrapers working, 3/4 need JS rendering  
**Data Extracted**: 22 RBI Repo Rate entries  
**Time Spent**: ~30 minutes  

---

## Completed ✓

### RBI Repo Rate Scraper
- **URL**: https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx
- **Method**: BeautifulSoup HTML parsing
- **Success**: ✓ YES
- **Rows Extracted**: 22
- **Output File**: `src/data_collection/output/rbi_repo_rate.csv`

**How it works**:
1. Fetches press release page via requests
2. Parses HTML with BeautifulSoup
3. Finds tables containing "repo", "monetary policy", or "mpc" keywords
4. Extracts text and saves to CSV

**Data Sample**:
```
raw_text,fetch_date
"Monetary Policy Rate from MPC Press Release...",2026-05-25
...
```

**Difficulty**: LOW ✓

---

## Blocked 🚫

### 1. FII/DII Activity Scraper
- **URL**: https://trendlyne.com/macro-data/fii-dii/month/snapshot-month/
- **Method Attempted**: BeautifulSoup + pd.read_html
- **Status**: ⚠️ NO USABLE TABLES FOUND

**Issue**:
- TrendLyne loads tables via JavaScript
- Static HTML scraping returns page shell without table data
- Tables rendered client-side only (visible in browser, not in HTML source)

**Solution Required**:
- **Option A**: Use Selenium WebDriver (headless Chrome)
  - Opens real browser
  - Waits for JS to execute
  - Extracts rendered HTML
  - Slower (~5-10 sec per page) but reliable
  
- **Option B**: Reverse-engineer API calls
  - Inspect browser DevTools Network tab
  - Find XHR/fetch calls to API
  - Call API directly (faster, more reliable)
  - May hit rate limits or auth requirements
  
- **Option C**: Look for alternative data sources
  - NSE official data (already tried, returned 404)
  - Financial websites with public APIs
  - CSV downloads from TrendLyne

**Recommendation**: Option B (API reverse-engineering) → Option A (Selenium fallback)

**Difficulty**: MEDIUM-HIGH

---

### 2. RBI Balance Sheet Scraper
- **URL**: https://www.rbi.org.in/scripts/WSSView.aspx
- **Method Attempted**: BeautifulSoup + pd.read_html
- **Status**: ⚠️ NO BALANCE SHEET TABLES FOUND

**Issue**:
- WSS page has dropdown forms to select date/data
- Tables only appear after form submission
- Static request returns form HTML, not data

**Solution Required**:
- **Option A**: Selenium to interact with form
  - Select date from dropdown
  - Click submit
  - Extract table from result
  
- **Option B**: RBI provides ZIP downloads
  - Check if downloadable files available
  - Extract from Excel/CSV
  
- **Option C**: Direct link to specific report
  - Some RBI reports have direct data links
  - May not require form submission

**Recommendation**: Option A (Selenium with form interaction)

**Difficulty**: MEDIUM

---

### 3. MOSPI CPI Scraper
- **URL**: https://mospi.gov.in/consumer-price-index
- **Method Attempted**: BeautifulSoup + pd.read_html
- **Status**: ⚠️ NO CPI TABLES FOUND

**Issue**:
- MOSPI site structure is complex
- Data may be in PDFs, not HTML tables
- Page uses multiple navigation levels

**Solution Required**:
- **Option A**: Parse PDF files
  - Identify PDF download links
  - Use pdfplumber or PyPDF2
  - Extract tables from PDFs
  
- **Option B**: Selenium to navigate menus
  - Click through menu items
  - Find data table page
  - Extract HTML
  
- **Option C**: Direct government API
  - Check if MOSPI has public API
  - Likely more reliable than scraping

**Recommendation**: Option C (Gov API) → Option A (PDF parsing)

**Difficulty**: MEDIUM-HIGH

---

## Implementation Guide for Future Sessions

### To Complete Phase 2:

**Option 1: Quick Fix (Recommended)**
1. Research APIs for TrendLyne, RBI, MOSPI
2. If APIs exist, integrate them (easiest)
3. If not, proceed to Selenium

**Option 2: Selenium Implementation**
1. Install Selenium WebDriver and ChromeDriver
2. Implement `SeleniumScraper` base class
3. Add subclasses for FII/DII, Balance Sheet, CPI
4. Handle timeouts, waits, and element detection

**Installation**:
```bash
pip install selenium lxml pdfplumber
# Download ChromeDriver from https://chromedriver.chromium.org/
```

**Selenium Template**:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumScraper(BaseScraper):
    def __init__(self, output_dir='src/data_collection/output'):
        super().__init__(output_dir)
        self.driver = webdriver.Chrome()  # or --headless
        
    def scrape(self):
        self.driver.get(self.url)
        # Wait for tables to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )
        # Extract data
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        # ... parse tables
        self.driver.quit()
        return df
```

---

## Alternative Data Sources

| Data | Primary Source | Alternative | Status |
|------|---|---|---|
| FII/DII | TrendLyne.com | NSE API / MoneyControl | To investigate |
| RBI Balance Sheet | RBI WSS | RBI Data releases / FRED | To investigate |
| India CPI | MOSPI | RBI / CEIC | To investigate |

**Action**: Before implementing Selenium, search for:
1. Official REST APIs
2. CSV/Excel downloads
3. Alternative data providers with easier access

---

## Files Created

- `src/data_collection/scrapers.py` (298 lines)
  - BaseScraper class
  - RBIRepoRateScraper ✓
  - FIIDIIScraper (needs JS rendering)
  - RBIBalanceSheetScraper (needs JS rendering)
  - MOSPICPIScraper (needs JS rendering)
  - `run_all_scrapers()` orchestrator function

- `src/data_collection/output/rbi_repo_rate.csv`
  - 22 rows of RBI Repo Rate data
  - Columns: raw_text, fetch_date

---

## Time Estimate for Remaining Work

- **API Integration** (if available): 2-4 hours (fastest path)
- **Selenium Implementation**: 4-6 hours (medium complexity)
- **PDF Parsing for CPI**: 2-3 hours (if PDFs exist)
- **Testing & Validation**: 2-3 hours

**Total for Phase 2 Completion**: 8-12 hours

---

## Blocking vs Moving Forward

### Option 1: Continue with Phase 2
- Implement Selenium for JS-heavy sites
- Complete all 4 scrapers
- Adds 1-2 weeks to timeline

### Option 2: Work Around JS-Heavy Sites
- Skip TrendLyne, use NSE historical data instead
- Skip MOSPI scraping, use manual monthly updates
- Reduce Phase 2 to 1-2 days
- Unblocks Phase 3 sooner

### Option 3: Hybrid Approach (Recommended)
- Complete RBI Repo Rate (already done ✓)
- Research APIs for other 3 sources
- If APIs found: integrate directly
- If APIs not found: mark as "manual monthly updates" for now
- Move to Phase 3 with 1-3 automated scrapers
- Add remaining scrapers in Phase 4 if needed

**Recommendation**: Option 3 - Move to Phase 3 with YFinance + RBI scraper, plan Phase 4 for remaining data sources.

---

## Next Session Checklist

- [ ] Review this document
- [ ] Check if APIs exist for FII/DII, RBI Balance Sheet, MOSPI CPI
- [ ] If APIs exist: Add API integration to scrapers.py (1-2 hours)
- [ ] If APIs don't exist: Decide between Selenium or manual updates
- [ ] Update scrapers.py with API calls or mark sources as manual
- [ ] Run Phase 1 + Phase 2 unified pipeline
- [ ] Proceed to Phase 3: Unified data pipeline + backtesting

---

**Status**: Ready for next session  
**Blocked On**: JavaScript rendering for 3/4 scrapers  
**Unblocked By**: API discovery or Selenium implementation