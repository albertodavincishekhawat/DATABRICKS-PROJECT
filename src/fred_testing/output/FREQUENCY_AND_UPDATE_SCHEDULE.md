# SUCCESSFUL FRED DATA - FREQUENCY & UPDATE SCHEDULE

Generated: 2026-05-25 12:46:11.466027

## Summary

| Data | Series ID | Frequency | Latest | Update Lag |
|------|-----------|-----------|--------|-----------|
| US_CPI | CPIAUCSL | M | 2026-04-01 | 1-2 days |
| Federal_Funds_Rate | FEDFUNDS | M | 2026-04-01 | 1-2 days |
| USD_EUR_Rate | DEXUSEU | D | 2026-05-15 | 1-2 days |


## Detailed Information


### US_CPI (CPIAUCSL)

**Frequency**: Monthly (M)

**Title**: Consumer Price Index for All Urban Consumers: All Items in U.S. City Average

**Units**: Index 1982-1984=100

**Data Range**: 1947-01-01 to 2026-04-01

**Total Observations**: 952

**Last Updated**: 2026-05-12 08:03:57-05

**Status**: ✓ Active


### Federal_Funds_Rate (FEDFUNDS)

**Frequency**: Monthly (M)

**Title**: Federal Funds Effective Rate

**Units**: Percent

**Data Range**: 1954-07-01 to 2026-04-01

**Total Observations**: 862

**Last Updated**: 2026-05-01 15:20:39-05

**Status**: ✓ Active


### USD_EUR_Rate (DEXUSEU)

**Frequency**: Daily (D)

**Title**: U.S. Dollars to Euro Spot Exchange Rate

**Units**: U.S. Dollars to One Euro

**Data Range**: 1999-01-04 to 2026-05-15

**Total Observations**: 7140

**Last Updated**: 2026-05-18 15:16:46-05

**Status**: ✓ Active


## Frequency Codes

| Code | Meaning | Typical Release Schedule |
|------|---------|--------------------------|
| D | Daily | Each trading day |
| W | Weekly | Once per week (usually Friday) |
| BW | Bi-Weekly | Every other week |
| M | Monthly | First business day of next month |
| Q | Quarterly | First month of next quarter |
| A | Annual | Next year |
| SA | Semi-Annual | Twice per year |

## Update Lag Information

| Series | Typical Lag | Notes |
|--------|------------|-------|
| US CPI | 15-20 days | Released mid-month for prior month |
| Federal Funds Rate | 1-2 days | Updated after FOMC decision |
| USD/EUR Rate | Same day | Real-time forex data |

## For Decision Algorithm Implementation

### Data Freshness Requirements

Rule R1 (Monetary System Shift):
- Uses: Federal Funds Rate
- Frequency: Monthly (after MPC meetings)
- FRED provides: Monthly, typically 1-2 days lag ✓

Rule R2 (Real Rate Shock):
- Uses: Repo Rate (RBI) + CPI (India)
- FRED provides: US CPI Monthly only
- Note: Need to get RBI Repo Rate separately ⚠️

Rule R3 (Commodity/Oil Shock):
- Uses: Brent Crude prices
- Frequency: Daily
- FRED: NOT available (API error)
- Alternative: Use EIA API ✗

Rule R5 (QE Regime):
- Uses: RBI Balance Sheet (India specific)
- Frequency: Weekly
- FRED: NOT available ⚠️

Rule R7 (Institutional Selling):
- Uses: FII/DII Activity (India specific)
- Frequency: Daily
- FRED: NOT available ⚠️

### Reference Data Available on FRED

These can be used for context/validation:
- **US CPI**: Monthly, released mid-month
- **Federal Funds Rate**: Monthly, after FOMC
- **USD/EUR Rate**: Daily, real-time

---

**Status**: Documentation updated with actual FRED frequency data
**Last Updated**: 2026-05-25 12:46:11.466062
