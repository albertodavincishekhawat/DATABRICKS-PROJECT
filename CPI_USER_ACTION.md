# CPI Data - User Action Required

**Status**: Template created, ready for user to fill in

---

## What You Need to Do

### Step 1: Get Latest CPI Data (Apr 2025 - Apr 2026)

Get official CPI values from **RBI** or **MOSPI** (Ministry of Statistics):

**Option A: RBI Website**
- Go to: https://www.rbi.org.in/
- Look for: Consumer Price Index (CPI) section
- Get monthly values: Apr 2025 - Apr 2026

**Option B: MOSPI (Official)**
- Go to: https://mospi.gov.in/
- Download: CPI monthly data
- Get values: Apr 2025 - Apr 2026

### Step 2: Fill in the CSV

Open: `src/data_collection/input/cpi_combined.csv`

You'll see:
```
Date,CPI,Source,Data_Quality
2020-01-01,126.2353,FRED,actual
2020-02-01,125.4702,FRED,actual
...
2025-03-01,157.5517,FRED,actual
2025-04-01,,USER_TO_PROVIDE,missing
2025-05-01,,USER_TO_PROVIDE,missing
2025-06-01,,USER_TO_PROVIDE,missing
...
2026-04-01,,USER_TO_PROVIDE,missing
```

**Fill in the CPI values**:
```
2025-04-01,<CPI_VALUE>,RBI_OR_MOSPI,actual
2025-05-01,<CPI_VALUE>,RBI_OR_MOSPI,actual
...
2026-04-01,<CPI_VALUE>,RBI_OR_MOSPI,actual
```

### Step 3: Run Aggregation Again

After filling in the data:

```bash
python3 src/data_collection/run_monthly_aggregation.py
```

### Step 4: Check Results

```bash
cat src/data_collection/output/monthly/data_quality_report.txt
```

You should see improvement in "Complete Months" count!

---

## What Happens Next

**Before filling CPI**:
- Complete months: 0/76 (CPI missing for Apr 2025+)
- Cannot sync months after 2025-03

**After filling CPI**:
- Complete months: ~50-70/76 (depending on other source availability)
- Algorithm can run on those months!

---

## Timeline

1. **Get CPI data from RBI/MOSPI**: 10-15 min
2. **Fill in CSV**: 2-3 min  
3. **Re-run aggregation**: 1 min
4. **Total**: ~20 min

---

## Questions?

- CPI data sources: RBI or MOSPI official websites
- CSV format: Date, CPI (two columns to fill)
- File location: `src/data_collection/input/cpi_combined.csv`

**Most important**: Get the official, actual CPI values (no estimates or forward-fill)
