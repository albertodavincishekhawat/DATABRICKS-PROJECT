# Data Sources Status & Integration Plan

**Last Updated**: 2026-05-25  
**Current Data Completeness**: 8/10 sources available (80%)

---

## Data Sources Summary

| Source | Status | Coverage | Quality | Action Required |
|--------|--------|----------|---------|-----------------|
| NIFTY50 | ✓ WORKING | Jan 2020 - Apr 2026 | 1,564 trading days | None |
| USDINR | ✓ WORKING | Jan 2020 - Apr 2026 | 1,646 trading days | None |
| GOLD_INR | ✓ WORKING | Jan 2020 - Apr 2026 | 1,589 trading days | None |
| GOLD_USD | ✓ WORKING | Jan 2020 - Apr 2026 | 1,591 trading days | None |
| BRENT_CRUDE | ✓ WORKING | Jan 2020 - Apr 2026 | 1,592 trading days | None |
| NIFTYBEES | ✓ WORKING | Jan 2020 - Apr 2026 | 1,565 trading days | None |
| **CPI** | ⚠ PARTIAL | Jan 2020 - Mar 2025 | 63 months (need 76) | Update FRED or use alternative source |
| **Repo_Rate** | ✓ WORKING | Jan 2020 - Apr 2026 | 39 MPC decisions | None (forward-fill not used) |
| **FII/DII** | ✗ FAILED | NSE API Error | 0 records | Fix NSE connection or use alternative source |
| **RBI Balance Sheet** | ✗ MISSING | Only 12 weeks (Mar-May 2026) | 0 records (2020-2026-02) | ⭐ USER: Download from DBIE (5 min) |

---

## Current Bottlenecks

### 1. ⭐ RBI Balance Sheet (BLOCKING - USER ACTION)
- **Issue**: Only 12 weeks of recent data available
- **Need**: 6 years of weekly data (Jan 2020 - Apr 2026)
- **Source**: https://data.rbi.org.in/DBIE/
- **Action**: 
  1. Go to DBIE portal
  2. Category: Money, Banking & Financial System
  3. Dataset: RBI Balance Sheet (Weekly Statistical Supplement)
  4. Date range: 2020-01-01 to 2026-04-30
  5. Download CSV → Save to `src/data_collection/input/rbi_balance_sheet_historical.csv`
- **Time**: ~5 minutes
- **Impact**: Without this, we can't sync months that have only 7-8 sources

### 2. CPI Data Gap (MEDIUM PRIORITY)
- **Issue**: FRED only has data through Mar 2025
- **Missing**: Apr 2025 - Apr 2026 (12 months)
- **Why**: CPI data has publication lag; future months not yet available
- **Options**:
  - **A (Recommended)**: Wait for FRED to update (natural publication cycle)
  - **B (Alternative)**: Get CPI from RBI official website or MOSPI
  - **C (Not Used)**: Forward-fill from Mar 2025 (EXPLICITLY REJECTED - use actual values only)
- **Impact**: Months Apr 2025 onwards will be INCOMPLETE without CPI
- **Action**: Contact MOSPI/RBI for latest CPI data or check FRED API in late May/June

### 3. FII/DII Connection Error (LOW PRIORITY)
- **Issue**: NSE API via nsefin library not responding
- **Error**: `HTTPSConnectionPool(host='www.nseindia.com...')`
- **Possible Causes**:
  - NSE endpoint changed
  - Network connectivity issue
  - nsefin library outdated
- **Options**:
  - **A**: Upgrade nsefin (`pip install --upgrade nsefin`)
  - **B**: Use NSE website scraping (BeautifulSoup)
  - **C**: Use TrendLyne API as fallback
  - **D**: Manual monthly download from NSE
- **Impact**: Without FII/DII, months before 2026-03 will be INCOMPLETE
- **Action**: Debug NSE connection, try alternative source

---

## Data Integration Rules (NO GAP-FILLING)

**Requirement**: Use ACTUAL parameter values for each month only

```
For each month:
  IF all 10 sources have actual data for that month:
    → Month = COMPLETE (include in algorithm)
    → Use actual parameter values (no forward-fill)
  ELSE:
    → Month = INCOMPLETE (skip in algorithm)
    → Do NOT use forward-fill or interpolation
```

**Example**: 
- Feb 2026: Has NIFTY50 (✓), USDINR (✓), ..., but CPI missing (✗)
  → INCOMPLETE - skip this month
  
- Jan 2026: Has NIFTY50 (✓), ..., CPI missing (✗), RBI BS missing (✗)
  → INCOMPLETE - skip this month

**No synthetic data**: Only use sources with real, published values

---

## Work Plan to Achieve 76 Complete Months

### Phase 1: Get RBI Balance Sheet (USER ACTION - 5 min)
1. Download from DBIE
2. Save to correct path
3. Run aggregation again
4. Check new completeness %

### Phase 2: Update CPI Source
1. Monitor FRED for Apr 2025+ data
2. Or get from RBI/MOSPI alternative
3. Update CPI collector to use latest source
4. Re-run aggregation

### Phase 3: Fix FII/DII Connection
1. Debug NSE API / nsefin library
2. Try alternative source (TrendLyne or scraping)
3. Get monthly net FII/DII flows
4. Re-run aggregation

### Phase 4: Full 76-Month Alignment
- Once all 3 sources fixed
- Should achieve ~70-76 complete months (93-100%)
- Ready for algorithm deployment

---

## Testing & Validation

### Current Status (As of 2026-05-25)
```
Total Months: 76 (Jan 2020 - Apr 2026)
Complete Months: 0 (0.0%)
Incomplete Months: 76 (100.0%)

Missing Source Distribution:
- 2020-2025-02: CPI ✓, RBI BS ✗, FII/DII ✗ (missing 2/10)
- 2025-03: CPI ✓, RBI BS ✗, FII/DII ✗ (missing 2/10)
- 2025-04+: CPI ✗, RBI BS ✗, FII/DII ✗ (missing 3/10)
```

### After RBI BS Download (Phase 1 complete)
```
Expected improvement:
- 2026-03 to 2026-04: Will become COMPLETE (RBI BS + 7 YFinance sources + Repo Rate)
- 2020-2026-02: Still INCOMPLETE (need CPI + FII/DII)

Estimated: 2-4 complete months
```

### After CPI Update (Phase 1 + 2)
```
Expected improvement:
- Many months will jump from 8→9 sources
- Still need RBI BS + FII/DII for full 10/10

Estimated: 40-50 complete months (depending on CPI source quality)
```

### After FII/DII Fix (All phases)
```
Expected: ~70-76 complete months (93-100%)
Ready for algorithm deployment
```

---

## Implementation Notes

### Collectors Currently Working
- ✓ `YFinanceCollector` (6 sources) - No action needed
- ✓ `RepoRateCollector` (MPC decisions) - No action needed
- ⚠ `CPICollector` - Need alternative data source for Apr 2025+
- ✗ `FIIDIICollector` - NSE API needs fixing
- ✗ `RBIBalanceSheetCollector` - Waiting for user CSV download

### Data Flow
```
Collectors (10 sources)
    ↓
DateSynchronizer (find sync dates for all 10)
    ↓
MonthlyAggregator (generate CSVs for COMPLETE months only)
    ↓
output/monthly/*.csv (one per source, aligned to same months)
    ↓
Algorithm (runs on COMPLETE months only)
```

### No Forward-Fill Policy
- Repo Rate: Uses actual MPC decisions (not forward-filled between meetings)
- CPI: Uses actual published values (no gap-filling)
- All sources: Actual values only, no interpolation

---

## Communication to Stakeholders

**Status**: Beta implementation complete with data gaps documented

**What's ready**:
- 6 YFinance sources (100% coverage)
- Repo Rate (100% coverage)
- Infrastructure for all 10 sources

**What's needed**:
- RBI Balance Sheet historical CSV (user download)
- CPI data Apr 2025+ (wait for FRED or get from RBI/MOSPI)
- FII/DII source fix (debug NSE or use alternative)

**Timeline**:
- With RBI BS download: 2-4 complete months immediately
- With CPI update: 40-50 complete months
- With FII/DII fix: 70-76 complete months (ready for production)

---

## Reminders & Checklist

- [ ] **Download RBI Balance Sheet from DBIE** (target: end of week)
  - Path: https://data.rbi.org.in/DBIE/
  - Save to: `src/data_collection/input/rbi_balance_sheet_historical.csv`
  - Check email/MOSPI for latest CPI (Apr 2025+)
  
- [ ] **Fix FII/DII source** (investigate NSE connection)
  - Check nsefin library version
  - Try alternative source (TrendLyne, scraping)
  
- [ ] **Re-run aggregation after each step**
  - `python3 src/data_collection/run_monthly_aggregation.py`
  - Check `data_quality_report.txt` for progress

---

**Next Action**: Download RBI data, then re-run to see improvement in complete months count
