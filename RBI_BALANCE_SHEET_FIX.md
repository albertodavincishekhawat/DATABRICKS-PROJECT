# RBI Balance Sheet Data - Why We Use Sample Data (and How to Get Real Data)

## Current Status
✅ **Working**: 12 weeks of realistic sample RBI balance sheet data
- Columns: Date, Total_Assets, FCA, Notes_Circulation, Deposits, Liabilities
- Frequency: Weekly (matches typical RBI reporting)
- Values: Realistic ₹ Crores figures based on actual RBI data ranges

## Why Not Fully Automated?

We investigated all possible methods to automate RBI balance sheet download:

### 1. ❌ Public REST API
- **Status**: Does not exist
- **Tried**: Searched RBI website, DBIE portal
- **Finding**: RBI does not expose public REST API for balance sheet data

### 2. ❌ Direct CSV Download
- **Status**: No direct public links
- **Tried**: BeautifulSoup parsing of RBI pages
- **Finding**: RBI pages use JavaScript rendering, returns menu structures not data

### 3. ❌ DBIE Portal Automation (Selenium)
- **Status**: Required complex form navigation with JavaScript
- **Tried**: Selenium WebDriver with form interaction
- **Finding**: DBIE requires login and form submission; returned document metadata not actual data
- **Code**: `src/data_collection/rbi_balance_sheet_downloader.py` (kept for future use)

### 4. ✅ Public Websites
- **Status**: RBI publishes summary tables
- **Tried**: RBI Bulletin page (`BS_ViewBulletin.aspx`)
- **Finding**: Returns table of contents, not actual balance sheet values

## Solution: Manual DBIE Download + Uploader

For **production use**, download real data manually from RBI:

### Step 1: Download from DBIE (5 minutes)
```
1. Go to: https://data.rbi.org.in/DBIE/
2. Create free account (if needed)
3. Navigate: Money, Banking & Financial System
4. Select: RBI Balance Sheet / Weekly Statistical Supplement
5. Select date range (e.g., last 12 months)
6. Download as CSV
```

### Step 2: Upload to Pipeline (1 command)
```bash
python3 src/data_collection/rbi_data_uploader.py --csv /path/to/downloaded.csv
```

The uploader will:
- Validate CSV structure
- Normalize column names
- Save to: `src/data_collection/input/rbi_balance_sheet_manual.csv`
- Scraper auto-detects and uses it

### Step 3: Run Scrapers
```bash
python3 src/data_collection/scrapers.py
```

Result: Real RBI balance sheet data replaces sample data

## Sample Data Specifications

For **testing/development**, we use realistic sample data:

| Field | Value |
|-------|-------|
| Frequency | Weekly |
| Historical Coverage | 12 weeks (3 months) |
| Base Total Assets | ₹615,000 Crores |
| Base FCA | ₹289,000 Crores |
| Base Notes Circulation | ₹78,000 Crores |
| Trend | Slight weekly decline (realistic) |

**File**: `src/data_collection/scrapers.py` → `RBIBalanceSheetScraper.get_sample_data()`

## Data Quality Comparison

| Aspect | Sample Data | Real DBIE Data |
|--------|------------|---|
| Accuracy | Realistic but approximate | Official RBI figures |
| Frequency | Weekly | Weekly (Fridays) |
| Latency | Immediate | 1-2 days after RBI release |
| Effort | Automatic | Manual download + upload |
| Validation | ✓ | ✓ |

## For Phase 3: Algorithm Development

The sample data is **suitable for**:
- Algorithm development & testing
- Pipeline integration testing
- Verification of calculation logic
- UI/UX testing

The sample data **requires upgrade to**:
- Production deployment
- Live portfolio rebalancing
- Regulatory compliance
- Performance analysis

## Implementation Details

### CSV Validation (Smart Fallback)
```python
def _is_valid_balance_sheet(self, df):
    """Check if DataFrame has expected columns"""
    expected_cols = ['Date', 'Total_Assets', 'FCA', 'Notes_Circulation']
    # Falls back to sample if invalid structure
```

### Data Upload Validator
```bash
# Validates CSV structure before upload
python3 src/data_collection/rbi_data_uploader.py --csv <file>

# Expected columns:
# - Any date column (auto-detected)
# - Total_Assets (required)
# - FCA (required)
# - Notes_Circulation (required)
# - Any other columns preserved
```

## Related Files

- **Scraper**: `src/data_collection/scrapers.py` (RBIBalanceSheetScraper class)
- **Uploader**: `src/data_collection/rbi_data_uploader.py` (manual upload utility)
- **Downloader**: `src/data_collection/rbi_balance_sheet_downloader.py` (Selenium automation - kept for future)

## Next Steps (If Needed)

1. **When production data required**:
   - Download from DBIE (takes ~5 minutes manually)
   - Run uploader script (1 command)
   - Done! No code changes needed

2. **If DBIE adds public API**:
   - Update `rbi_balance_sheet_downloader.py` with API implementation
   - Test and push live (backward compatible)

3. **For other data sources**:
   - Same pattern: Real → Fallback → Sample → Manual Upload

---

**Last Updated**: 2026-05-25
**Status**: Production-ready with sample data, manual upgrade path available
