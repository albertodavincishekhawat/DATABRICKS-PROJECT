# Scraper Issues Found - May 25, 2026

## 🔴 CRITICAL ISSUES

### 1. **RBI Repo Rate: Duplicate Data (50% duplicates!)**
**Severity**: HIGH  
**Location**: `RBIRepoRateScraper.scrape()` (line 99-116)

**Problem**: Same announcement appears multiple times across different tables
- **Current**: 22 rows extracted, but **11 are duplicates** (50% duplication rate)
- **Root cause**: Loops through multiple tables without deduplication
- **Impact**: Algorithm will see false signals from duplicate announcements

**Example**:
```
"Money Market Operations as on May 24, 2026" appears 2x
"RBI to conduct 4-day Variable Rate Repo..." appears 2x
```

**Fix**: Add deduplication before returning
```python
# After line 118
df = df.drop_duplicates(subset=['announcement'], keep='first')
```

---

## 🟠 MEDIUM ISSUES

### 2. **Hardcoded Sample Data Dates (Stale)**
**Severity**: MEDIUM  
**Location**: 
- `FIIDIIScraper.get_sample_data()` (line 165-171)
- `RBIBalanceSheetScraper.get_sample_data()` (line 227-234)
- `MOSPICPIScraper.get_sample_data()` (line 310-317)

**Problem**: Sample data has hardcoded dates that will become outdated
- FII/DII: `2026-05-23` (will be stale in production)
- Balance Sheet: `2026-05-23` (will be stale in production)
- MOSPI CPI: `2026-05-01` (will be stale in production)

**Impact**: Algorithm tests will use increasingly outdated sample data

**Fix**: Generate dynamic dates
```python
def get_sample_data(self):
    from datetime import datetime, timedelta
    today = datetime.now().date()
    return pd.DataFrame([
        {'Date': str(today - timedelta(days=i)), ...}
        for i in range(3)
    ])
```

---

### 3. **Column Name Inconsistency**
**Severity**: MEDIUM  
**Location**: All scrapers

**Problem**: Different scrapers use different column names for the same data
```
RBI Repo Rate:      'date'           (lowercase)
FII/DII:            'Date'           (uppercase)
RBI Balance Sheet:  'Date'           (uppercase)
MOSPI CPI:          'Date'           (uppercase)
```

**Impact**: Phase 3 unified pipeline must handle multiple column name formats

**Fix**: Standardize all scrapers to use same column names
```python
# Standardize to: date, source, value, fetch_date
df.rename(columns={'Date': 'date', 'announcement': 'value'}, inplace=True)
```

---

### 4. **fetch_date Added at Different Times**
**Severity**: MEDIUM  
**Location**: Various scrapers

**Problem**: `fetch_date` is added at different stages:
- MOSPI CPI: Added in `scrape()` (line 390)
- Others: Added in `run()` (lines 199, 282)

**Impact**: Inconsistent timing of when fetch_date is recorded

**Fix**: Move fetch_date addition to `run()` method for all scrapers

---

## 🟡 LOW ISSUES

### 5. **Missing Input Directory**
**Severity**: LOW  
**Location**: `RBIBalanceSheetScraper.load_manual_csv()` (line 239)

**Problem**: Looks for `src/data_collection/input/rbi_balance_sheet_manual.csv` but directory doesn't exist
- Directory never created
- Users won't know where to put manual CSV files

**Fix**: Create directory structure
```bash
mkdir -p src/data_collection/input/
echo "# Place RBI Balance Sheet manual CSV files here" > src/data_collection/input/README.md
```

---

### 6. **Data Truncation in RBI Scraper**
**Severity**: LOW  
**Location**: `RBIRepoRateScraper.scrape()` (line 112)

**Problem**: Announcement text truncated to 120 characters
```python
'announcement': title_text[:120],  # Information loss!
```

**Impact**: Long announcements are cut off

**Fix**: Remove arbitrary limit or increase to 500+ characters

---

### 7. **No Data Validation**
**Severity**: LOW  
**Location**: All scrapers

**Problem**: No validation that returned DataFrames have expected columns/types
- Could silently accept invalid data structure
- Algorithm might fail downstream

**Fix**: Add validation method:
```python
def validate_data(self, df):
    """Validate DataFrame has expected structure"""
    required_cols = ['date', 'value']  # or specific columns
    assert all(col in df.columns for col in required_cols), \
        f"Missing required columns. Have: {df.columns}, Need: {required_cols}"
    return df
```

---

### 8. **nsefin URL Malformation**
**Severity**: LOW (informational)  
**Location**: Error logs

**Problem**: nsefin library has a bug with URL construction
```
Actual: https://www.nseindia.comapi/fiidiiTradeReact
Expected: https://www.nseindia.com/api/fiidiiTradeReact
```

**Impact**: nsefin library cannot work until this is fixed upstream
- This is a library bug, not our code
- Alternative: Use NSE CSV download instead

---

## 📊 ISSUE SUMMARY

| Issue | Severity | Type | Easy Fix |
|-------|----------|------|----------|
| RBI duplicates (50%) | 🔴 HIGH | Data quality | ✓ Yes (2 lines) |
| Stale sample dates | 🟠 MEDIUM | Data quality | ✓ Yes (5 lines) |
| Column name inconsistency | 🟠 MEDIUM | Structure | ✓ Yes (rename) |
| fetch_date timing | 🟠 MEDIUM | Consistency | ✓ Yes (move code) |
| Missing input directory | 🟡 LOW | UX | ✓ Yes (mkdir) |
| Text truncation | 🟡 LOW | Data loss | ✓ Yes (remove limit) |
| No data validation | 🟡 LOW | Robustness | ✓ Yes (add function) |
| nsefin URL bug | 🟡 LOW | External | ✗ No (library issue) |

---

## 🔧 RECOMMENDED FIXES (Priority Order)

### Fix 1: RBI Duplicates (CRITICAL) - 2 minutes
```python
# In RBIRepoRateScraper.scrape(), after line 118:
if repo_data:
    df = pd.DataFrame(repo_data)
    df = df.drop_duplicates(subset=['announcement'], keep='first')  # ADD THIS
    print(f"✓ Found {len(df)} unique repo announcements")
```

### Fix 2: Dynamic Sample Data (HIGH) - 5 minutes
```python
def get_sample_data(self):
    """Generate sample data with current dates"""
    from datetime import datetime, timedelta
    today = datetime.now().date()
    return pd.DataFrame([
        {'Date': str(today - timedelta(days=0)), 'FII Equity': 1234.56, ...},
        {'Date': str(today - timedelta(days=1)), 'FII Equity': 2345.67, ...},
        {'Date': str(today - timedelta(days=2)), 'FII Equity': 3456.78, ...},
    ])
```

### Fix 3: Column Standardization (MEDIUM) - 10 minutes
```python
# Create standard column mapping in base scraper
STANDARD_COLUMNS = {'Date': 'date', 'announcement': 'value', 'fetch_date': 'fetch_date'}

def standardize_columns(df):
    """Normalize column names across all scrapers"""
    return df.rename(columns=STANDARD_COLUMNS)
```

### Fix 4: Create Input Directory (LOW) - 1 minute
```bash
mkdir -p src/data_collection/input/
```

---

## 🎯 ACTION ITEMS

- [ ] Fix RBI duplicates (CRITICAL)
- [ ] Fix hardcoded sample dates (HIGH)
- [ ] Standardize column names (MEDIUM)
- [ ] Create input directory (LOW)
- [ ] Remove text truncation (LOW)
- [ ] Add data validation (LOW)

**Estimated total fix time**: 30-45 minutes

**Recommend**: Fix all issues before starting Phase 3, so algorithm testing isn't affected by data quality problems.
