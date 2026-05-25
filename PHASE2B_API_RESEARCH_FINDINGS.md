# Phase 2B: API Research Findings

**Date**: May 25, 2026  
**Status**: ✓ COMPLETE - Implementation ready for 2/3 sources, 1/3 needs further validation

---

## Summary: Good News! 2 Out of 3 Data Sources Have Public APIs

| Data Source | API Available | Type | Auth Required | Difficulty | Next Action |
|-------------|---|---|---|---|---|
| **India CPI** | ✓ YES | Official MOSPI API | Yes (Token) | LOW | Implement immediately |
| **FII/DII** | ✓ YES | Python Library (nsefin) | No | LOW | Implement immediately |
| **RBI Balance Sheet** | ⚠️ PARTIAL | DBIE Platform | Unknown | MEDIUM | Research further or Selenium |

---

## Source 1: India CPI (MOSPI) ✓ READY

**Status**: Official API exists and documented

### API Details
- **Base URL**: https://api.mospi.gov.in
- **Endpoints**:
  - `/api/getCPIIndex` - Get CPI index data
  - `/api/getItemIndex` - Get item-level inflation data
- **Authentication**: Requires signup and access token
- **Data Formats**: JSON, CSV
- **Tools Supported**: Swagger, Postman

### Implementation Path
1. Sign up at https://api.mospi.gov.in
2. Get access token via login
3. Call `/api/getCPIIndex` endpoint with parameters:
   - Group/SubGroup selection
   - Date range
4. Parse JSON response for monthly CPI values

### Data Available
- Monthly CPI Combined (All India)
- YoY % change
- Item-level breakdown available

### Estimated Effort: 1-2 hours

**Next Steps**: 
- [ ] Create MOSPI API account and get access token
- [ ] Build MOSPICPIScraper with API integration
- [ ] Test data retrieval and CSV export

---

## Source 2: FII/DII Activity ✓ READY

**Status**: Python library available with built-in FII/DII methods

### Method 1: nsefin Library (RECOMMENDED)

**Library**: nsefin  
**Link**: https://pypi.org/project/nsefin/  
**Status**: Already installed (nsefin 1.0+)

```python
import nsefin
nse = nsefin.NSEClient()
fii_dii_data = nse.get_fii_dii_activity()  # Returns pandas DataFrame
```

**Features**:
- No authentication required
- Returns clean pandas DataFrames
- Requires Python 3.9+
- Dependencies: pandas, requests

**Data Available**:
- FII/DII net buy/sell in Cash segment
- FII/DII net long/short in Derivatives
- Daily snapshots (after market close)
- Covers NSE, BSE, MSEI

### Method 2: NSE Official CSV (FALLBACK)

NSE publishes daily CSV reports at:
- https://www.nseindia.com/reports/fii-dii

**Format**: CSV download after market close  
**Update Frequency**: Daily (6:30-7:00 PM IST)

### Estimated Effort: 1-2 hours

**Next Steps**:
- [ ] Test nsefin library installation and get_fii_dii_activity()
- [ ] Build FIIDIIScraper wrapping nsefin
- [ ] Test data retrieval and CSV export

---

## Source 3: RBI Balance Sheet (DBIE) ⚠️ NEEDS VALIDATION

**Status**: Multiple access paths available, need to confirm which works

### Option 1: DBIE Platform (OFFICIAL)

**URL**: https://data.rbi.org.in/DBIE/  
**Data Warehouse**: Department of Statistics and Information Management (DSIM), RBI

**Export Formats**: Excel, CSV, PDF  
**Status**: API unclear - need to investigate further

**Data Available**:
- RBI Balance Sheet (weekly, usually Fridays)
- Assets, Liabilities, FCA (Foreign Currency Assets)
- Notes in circulation
- Detailed breakdowns available

### Option 2: data.gov.in (OPEN DATA)

**URL**: https://data.gov.in/keywords/RBI  
**Type**: Open Government Data platform  
**APIs**: Some datasets include REST API access

**Data Formats**: CSV, JSON (if API available)  
**Status**: Need to check if balance sheet included

### Option 3: Alternative Data Platforms

- **RBI Direct**: https://data.rbi.org.in (main RBI data portal)
- **RBIDATA App**: Mobile app for DBIE data download
- **dataful.in**: Third-party aggregator of DBIE data

### Option 4: Selenium Fallback (IF APIs NOT AVAILABLE)

If APIs not available:
- Use Selenium to navigate DBIE form
- Select balance sheet date from dropdown
- Submit form and scrape table
- **Estimated effort**: 2-3 hours

### Estimated Effort

- **API investigation**: 1 hour  
- **If API exists**: 1-2 hours implementation
- **If API missing + Selenium**: 3-4 hours total

**Next Steps**:
- [ ] Query data.gov.in APIs for RBI balance sheet
- [ ] Check DBIE platform for API documentation
- [ ] If no API found, implement Selenium scraper

---

## Implementation Strategy (Recommended Order)

### Phase 2B-1: Implement Easy APIs (IMMEDIATE)
**Time**: 2-4 hours

1. **FII/DII Scraper** (EASIEST - 1-2 hours)
   - Use nsefin library
   - Minimal code needed
   - No authentication

2. **MOSPI CPI Scraper** (EASY - 1-2 hours)
   - Create MOSPI API account
   - Call REST endpoint
   - Parse JSON response

### Phase 2B-2: Investigate RBI Balance Sheet (NEXT)
**Time**: 1 hour research + 1-4 hours implementation

1. Check data.gov.in for APIs
2. If found: Implement API integration (1-2 hours)
3. If not found: Implement Selenium (3-4 hours)

### Blocked Status Resolution

**Current**: 3/10 sources unavailable (CPI, RBI Balance Sheet, FII/DII)  
**After Phase 2B-1**: 1/10 sources unavailable (RBI Balance Sheet only)  
**After Phase 2B-2**: All 10 sources available → Phase 3 can start

---

## Risk Assessment

**Low Risk**:
- ✓ nsefin (established library, no auth required)
- ✓ MOSPI API (official government API)

**Medium Risk**:
- ⚠️ RBI Balance Sheet (API status unclear, may need Selenium)
- Mitigation: Quick 1-hour research to confirm API availability

**Unlikely Issues**:
- API rate limiting (government APIs typically generous)
- Data format changes (stable official sources)
- Authentication problems (MOSPI should be straightforward)

---

## Next Action

**Proceed with Phase 2B-1 immediately**: Implement FII/DII and MOSPI CPI scrapers. These are low-risk, high-impact tasks that will unlock 2 of 3 blocking sources.

**Then**: 1-hour research on RBI Balance Sheet API availability to decide: API integration vs Selenium implementation.

---

## References

- MOSPI API: https://api.mospi.gov.in
- nsefin PyPI: https://pypi.org/project/nsefin/
- RBI DBIE: https://data.rbi.org.in/DBIE/
- Open Data Portal: https://data.gov.in/keywords/RBI
- NSE FII/DII Reports: https://www.nseindia.com/reports/fii-dii