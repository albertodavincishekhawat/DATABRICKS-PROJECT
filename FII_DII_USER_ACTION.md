# FII/DII Data - User Action Required

**Status**: Real data needed - current system has synthetic data

---

## What You Need to Do

Download **real monthly FII/DII flows** from official NSE source.

### Step 1: Download from NSE (Recommended - Official Source)

**Option A: NSE CSV Reports (Best)**
1. Go to: https://www.nseindia.com/reports/fii-dii
2. Look for: **"FII/FPI & DII Trading Activity"** section
3. Find: **Historical monthly CSV downloads**
4. Download: CSV file with monthly FII/DII flows (2020-2026)
5. Save as: `src/data_collection/input/fii_dii_nse.csv`

**Option B: NSDL Monthly Reports (Alternative)**
1. Go to: https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx
2. Look for: **"Calendar Year Reports"** section
3. Download: FPI net investment monthly data
4. Save as: `src/data_collection/input/fii_dii_nsdl.csv`

**Option C: Manual Month-by-Month (If needed)**
1. Visit: https://www.nseindia.com/reports/fii-dii
2. Extract monthly net flows (FII_Net, DII_Net columns)
3. Create CSV with columns: Date, FII_Net, DII_Net
4. Save as: `src/data_collection/input/fii_dii_manual.csv`

### Step 2: CSV Format

Your downloaded CSV should have these columns:
```
Date,FII_Net,DII_Net
2020-01-31,15000,8000
2020-02-28,-25000,-12000
...
2026-04-30,42000,-17000
```

**Important**:
- Date format: YYYY-MM-DD or YYYY-MM-last-day
- Values in Crores (₹ Cr)
- One row per month (Jan 2020 - Apr 2026 = 76 rows)
- Can be positive (inflow) or negative (outflow)

### Step 3: Place the File

Save the CSV to one of these locations:
```
src/data_collection/input/fii_dii_nse.csv        # Primary
src/data_collection/input/fii_dii_nsdl.csv       # Secondary
src/data_collection/input/fii_dii_manual.csv     # Manual
src/data_collection/input/fii_dii_monthly.csv    # Current (replace)
```

### Step 4: Re-run System

After saving the file:
```bash
python3 src/data_collection/run_monthly_aggregation.py
```

Check results:
```bash
cat src/data_collection/output/monthly/data_quality_report.txt
```

Should still show: **76/76 complete months** (but now with REAL data)

---

## Why This Matters

- **Current state**: Synthetic/fabricated FII/DII data
- **After download**: Real FII/DII flows from NSE (official source)
- **Impact**: Algorithm will train on actual market flows, not fake data
- **Difference**: Results will be meaningful and reliable

---

## NSE Data Field Mapping

The NSE CSV likely has these columns (may vary):

| NSE Column | Map To | Note |
|---|---|---|
| FII Equity Net | FII_Net | Foreign Institutional Investor net flows |
| DII Equity Net | DII_Net | Domestic Institutional Investor net flows |
| Date / Period | Date | Month-end date |
| Net Flow | FII_Net + DII_Net | Combined total |

If column names differ, rename to: **Date, FII_Net, DII_Net**

---

## Timeline

1. **Download CSV**: 5-10 minutes
2. **Format CSV**: 2-3 minutes (if needed)
3. **Place in folder**: 1 minute
4. **Re-run aggregation**: 1-2 minutes
5. **Total**: ~10-15 minutes

---

## Questions?

- **NSE site not working?** Try NSDL at https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx
- **Can't find monthly data?** Use daily CSV and aggregate to monthly (sum all days in each month)
- **Different date format?** Convert to YYYY-MM-DD before saving
- **File size?** Should be ~76 rows (one per month)

---

## After You Download

Once file is in place:
```bash
# System will automatically load from:
# 1. src/data_collection/input/fii_dii_nse.csv
# 2. src/data_collection/input/fii_dii_nsdl.csv  
# 3. src/data_collection/input/fii_dii_manual.csv
# 4. src/data_collection/input/fii_dii_monthly.csv (current synthetic)

# Run aggregation - it will use REAL data instead of synthetic
python3 src/data_collection/run_monthly_aggregation.py

# Verify - should still show 76/76 complete months
cat src/data_collection/output/monthly/data_quality_report.txt
```

---

**Most important**: Use the **official NSE data source**, not synthetic data!
