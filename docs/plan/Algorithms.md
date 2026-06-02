# Decision Algorithm Documentation - Portfolio Rebalancing System

**Project**: Decision Algo DB Project  
**Version**: May 2026 (Final)  
**Owner**: Ravi Singh Shekhawat  
**Rules Implemented**: R1, R2, R3, R5, R7

---

## Table of Contents

1. [Overview](#overview)
2. [Rule R1 - Monetary System Shift](#rule-r1--monetary-system-shift)
3. [Rule R2 - Real Rate Shock](#rule-r2--real-rate-shock)
4. [Rule R3 - Commodity/Oil Shock](#rule-r3--commodityoil-shock)
5. [Rule R5 - Quantitative Easing Regime](#rule-r5--quantitative-easing-regime)
6. [Rule R7 - Institutional Selling Signal](#rule-r7--institutional-selling-as-a-buy-signal)
7. [Conflict Resolution](#conflict-resolution)
8. [Quarterly Check Algorithm](#quarterly-check-algorithm)
9. [Weekly Decision Tree](#weekly-decision-tree)

---

## Overview

This system manages portfolio allocation between two assets:
- **Nifty ETF**: Equity exposure
- **Gold ETF**: Safe haven asset

The algorithm monitors seven key economic indicators and automatically triggers rebalancing actions based on predefined rules and thresholds. The portfolio operates in three **States**:

| State | Target Allocation | When Active |
|-------|------------------|------------|
| State 1 | 80% Nifty / 20% Gold | Equity favorable conditions |
| State 2 | 50% Nifty / 50% Gold | Neutral/mixed conditions |
| State 3 | 10% Nifty / 90% Gold | Risk-off/commodity spike |

---

## Rule R1 - Monetary System Shift

### Purpose
Monitor RBI monetary policy changes and INR currency movements to detect macroeconomic stress.

### Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| `rate_current` | RBI Repo Rate (latest MPC decision) | https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx |
| `rate_baseline` | Repo rate at START of directional cycle | Auto-reset on direction reversal |
| `direction` | HIKING or CUTTING cycle | Derived from successive MPC meetings |
| `pct_change` | `ABS(rate_current - rate_baseline) / rate_baseline * 100` | Percentage change from baseline |
| `usdinr_today` | USD/INR spot rate (latest daily close) | https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx |
| `usdinr_6m_ago` | USD/INR spot rate from exactly 180 days prior | Same source |
| `inr_depreciation_pct` | `(usdinr_today - usdinr_6m_ago) / usdinr_6m_ago * 100` | Positive = INR weakening |

### Trigger Logic

**SUB-TRIGGER A: Rate Cycle**
```
IF direction_clean == TRUE 
AND pct_change >= 20 
AND sustained == TRUE (2+ consecutive meetings)
THEN R1_RATE_TRIGGERED = TRUE
ACTION: Add +20pp Gold (regardless of current State)
```

**SUB-TRIGGER B: Currency Regime (INR Weakening Only)**
```
IF inr_depreciation_pct >= 3.0% (weakening only)
AND currency_sustained == TRUE (held >= 30 consecutive days from first hitting 3.0%)
THEN R1_CURRENCY_TRIGGERED = TRUE
ACTION: Add +20pp Gold (regardless of current State)
```

**SUB-TRIGGER C: QE Regime**
```
PERMANENTLY SUSPENDED (R5 floor is sufficient)
```

### Yellow Alert

**Rate Cycle Yellow:**
```
IF direction_clean == TRUE 
AND pct_change >= 10 
AND sustained == TRUE
THEN Log (no action)
```

**Currency Yellow:**
```
IF inr_depreciation_pct >= 2.0% 
AND inr_depreciation_pct < 3.0%
THEN Log (no action)
```

### Exit Condition

**Rate Cycle Exit:**
- Direction reverses AND reversal sustained for 2+ consecutive MPC meetings
- Recalculate `pct_change` from new baseline
- If new `pct_change < 20%`: R1_RATE_TRIGGERED = FALSE

**Currency Exit:**
- `inr_depreciation_pct` drops below 3.0% AND holds for 30+ consecutive days
- Remove the +20pp Gold addition

### Example

```
Meeting 1: Rate = 5.00% → baseline = 5.00%
Meeting 2: Rate = 5.25% → HIKING
Meeting 3: Rate = 5.50% → HIKING
Meeting 4: Rate = 5.75% → HIKING
Meeting 5: Rate = 6.00% → pct_change = 20.0%
Direction clean = TRUE, Sustained = TRUE → R1_RATE_TRIGGERED = TRUE
```

---

## Rule R2 - Real Rate Shock

### Purpose
Detect positive real interest rates (nominal rate minus inflation) that compress equity valuations, requiring increased Gold exposure.

### Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| `nominal_rate` | RBI Repo Rate (latest MPC decision) | https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx |
| `inflation_rate` | India Headline CPI YoY % (latest month only) | https://mospi.gov.in/consumer-price-index |
| `real_rate` | `nominal_rate - inflation_rate` | Calculated |

### Trigger Logic

```
real_rate = nominal_rate - inflation_rate

IF real_rate > 3.0%
THEN R2_TRIGGERED = TRUE
ACTION:
  1. Determine current State target from most recent quarterly check
  2. Apply 75% shift rule toward current State target allocation
  3. Enforce MINIMUM 30% Gold floor on top of State target
     - If State target Gold < 30% → override to 30% Gold
     - If State target Gold >= 30% → apply as-is
  4. Hold this floor until EXIT condition is met
ELSE
  R2_TRIGGERED = FALSE
```

### Yellow Alert

```
IF real_rate > 2.0 AND real_rate <= 3.0
THEN Log (monitor monthly on CPI release)
```

### Exit Condition

```
real_rate drops back to <= 3.0%
AND confirmed by at least ONE subsequent monthly CPI release
Until exit confirmed: maintain 30% minimum Gold floor
```

### Example

```
Month 1: repo=6.0%, CPI=4.8% → real_rate=1.2% → CLEAR
Month 2: repo=6.5%, CPI=3.8% → real_rate=2.7% → YELLOW
Month 3: repo=6.5%, CPI=3.0% → real_rate=3.5% → TRIGGERED
Current State = State 1 (target 80:20)
State target Gold = 20% < 30% floor → override to 30% Gold / 70% Nifty
Apply 75% shift toward 70:30 target
Month 5: real_rate=2.8% → confirmed 2nd month below 3.0% → R2 exits
```

---

## Rule R3 - Commodity/Oil Shock

### Purpose
Detect oil price spikes (WTI/USOIL) that create stagflation risk, requiring defensive positioning.

### Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| `usoil_today` | WTI Crude Oil spot price USD/barrel | YFinance CL=F |
| `usoil_12m_avg` | Rolling 12-month average of WTI (USOIL) | Recalculated 1st of month |
| `ratio` | `usoil_today / usoil_12m_avg` | Calculated |

### Trigger Logic

```
ratio = usoil_today / usoil_12m_avg

IF ratio >= 1.80
THEN R3_TRIGGERED = TRUE
ACTION:
  Execute 75% shift rule toward State 3 target (10% Nifty / 90% Gold)
  Act immediately - no waiting period
ELSE
  R3_TRIGGERED = FALSE
```

### Yellow Alert

```
IF ratio >= 1.40 AND ratio < 1.80
THEN:
  Log: set price alert for R3 trigger
  Recompute alert price every 1st of month as usoil_12m_avg updates
```

### Exit Condition

```
ratio < 1.50
AND this condition has held for >= 90 consecutive calendar days
(check monthly, exit clock resets if ratio rises back above 1.50)

MAXIMUM HOLD RULE:
If ratio stays >= 1.50 for 2 continuous years without triggering exit,
force move to State 2 (50:50) regardless of ratio
```

### Example (May 2026)

```
usoil_today = $104.52
usoil_12m_avg = $71.19
ratio = 104.52 / 71.19 = 1.469
STATUS: YELLOW (>= 1.40 but < 1.80)
TRIGGER_PRICE = 71.19 * 1.80 = $128.14
```

---

## Rule R5 - Quantitative Easing Regime

### Purpose
Monitor RBI balance sheet expansion (excluding FX reserves) to detect QE conditions that increase liquidity and inflation risk.

### Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| `bs_current` | RBI Balance Sheet Total Assets (latest weekly) | RBI Weekly Statistical Supplement (WSS), Table 1 |
| `bs_year_ago` | RBI Balance Sheet Total Assets from exactly 52 weeks prior | Same WSS Table |
| `bs_yoy_pct` | YoY balance sheet growth (excluding FCA) | Calculated |

**CRITICAL**: Exclude Foreign Currency Assets (FCA) from both figures before computing YoY

### Trigger Logic

```
bs_yoy_pct = (bs_current_excl_fca - bs_year_ago_excl_fca) / bs_year_ago_excl_fca * 100

IF bs_yoy_pct > 25.0%
THEN R5_TRIGGERED = TRUE
ACTION:
  Maintain MINIMUM 20% Gold allocation at all times
  Do NOT reduce Gold below 20% even if State 1 (Equity Mode) is active
  This is a FLOOR rule only - does not override State targets above 20%
ELSE
  R5_TRIGGERED = FALSE
```

### Yellow Alert

```
IF bs_yoy_pct > 15.0 AND bs_yoy_pct <= 25.0
THEN Log (monitor weekly)
```

### Exit Condition

```
bs_yoy_pct drops back to <= 25.0%
AND this has held for 1 full calendar month
(confirmed at next month-end WSS reading after the drop)
Until exit confirmed: 20% Gold floor remains in force
```

---

## Rule R7 - FII Selling Signal

### Purpose
Detect contrarian buy signal when foreign institutions (FIIs) sell heavily, indicating a potential equity re-entry opportunity on foreign-driven dislocation.

### Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| `fii_net_monthly` | FII Net Equity Investment per calendar month (equity cash only) | NSDL FPI Yearwise report |
| `fii_peak_inflow` | Highest positive monthly FII net inflow in trailing 24 months | Recalculated every month |
| `fii_3m_cumulative` | Sum of FII net flows for most recent 3 complete calendar months | Calculated |
| `outflow_threshold` | `fii_peak_inflow * 0.25` | Recalculated monthly |

### Trigger Logic

```
// Recalculate monthly:
fii_peak_inflow = MAX(fii_net_monthly) over trailing 24 calendar months
outflow_threshold = fii_peak_inflow * 0.25

fii_outflow_check = (fii_3m_cumulative < 0) 
                  AND (ABS(fii_3m_cumulative) >= outflow_threshold)

IF fii_outflow_check == TRUE
THEN R7_TRIGGERED = TRUE
ACTION (depends on current State):
  IF State 3: Do not reduce Nifty further via lump-sum mid-quarter action
             Quarterly rebalance proceeds as scheduled
  IF State 2: SIP goes 100% Nifty ETF while R7 is active
  IF State 1: No change (already in equity)
ELSE
  R7_TRIGGERED = FALSE

// Mid-cycle deactivation:
IF outflow_threshold rises such that 
   ABS(fii_3m_cumulative) < new outflow_threshold
THEN R7_TRIGGERED = FALSE immediately
```

### Yellow Alert

```
IF fii_3m_cumulative < 0 
AND ABS(fii_3m_cumulative) >= (outflow_threshold * 0.60)
THEN Log (no action, monitor monthly)
```

### Exit Condition

R7 exits when ANY of these occur:
1. `fii_3m_cumulative` turns positive (FII becomes net buyer over 3 months)
2. `ABS(fii_3m_cumulative) < outflow_threshold` after monthly recalculation

When R7 exits: return to standard State-based SIP immediately (no waiting period)

---

## Conflict Resolution

### Master Conflict Resolution Table

| Rules in Conflict | Priority | Resolution |
|-------------------|----------|-----------|
| R1 + R2 | R1 | Apply +20pp Gold (R1). R2's 30% floor already exceeded. |
| R1 + R3 | Both apply, cap at 90:10 | R3 drives to State 3 (90% Gold). R1 adds +20pp on top. |
| R1 + R5 | R1 | Apply +20pp Gold (R1). R5's 20% floor already exceeded. |
| R1 + R7 | Split SIP | Lump-sum: +20pp Gold shift. SIP: 50% Nifty / 50% Gold. |
| R2 + R3 | R3 | R3 drives to State 3 (90% Gold). R2's 30% floor irrelevant at 90%. |
| R2 + R5 | R2 | R2's 30% Gold floor more restrictive than R5's 20%. |
| R2 + R7 | Split SIP, maintain ratio | Lump-sum: maintain current ratio. SIP: split proportionally. |
| R3 + R5 | R3 | R3 target (90% Gold) exceeds R5 floor (20%). |
| R3 + R7 | R3 drives all | Quarterly rebalance with full shift. SIP = 100% Gold. |
| R5 + R7 | Independent | R5 sets 20% Gold floor. R7 applies SIP tilt to equity. |

### Three-Way Conflict: R1 + R2 + R7 (Simultaneously Active)

**Market Context:**
- R1 active: Monetary system under stress
- R2 active: Real rates significantly positive, compressing equity valuations
- R7 active: FII selling heavily (3m cumulative outflow ≥ 25% of peak inflow)

**Default Action**: Hold State 2 (50:50 Nifty / Gold)

**Rationale**: R1 pushes toward Gold; R7 pushes toward equity; R2 enforces 30% Gold floor. The competing signals balance to a neutral allocation.

---

## Quarterly Check Algorithm

**Run on**: Jan 1, Apr 1, Jul 1, Oct 1 (or next trading day if holiday)

### Step 1: Calculate 6-Month Returns

```
nifty_6m_return = (nifty_today - nifty_6m_ago) / nifty_6m_ago * 100
gold_inr_6m_return = (gold_inr_today - gold_inr_6m_ago) / gold_inr_6m_ago * 100
differential = nifty_6m_return - gold_inr_6m_return
```

**Data Sources**: YFinance `^NSEI` (Nifty 50), YFinance `GOLD` (Gold INR) — both confirmed, in `yfinance_daily.csv`

### Step 2: Determine State

```
IF differential > +5
  → STATE 1 (target = 80% Nifty / 20% Gold)
ELSE IF -5 <= differential <= +5
  → STATE 2 (target = 50% Nifty / 50% Gold)
ELSE IF differential < -5
  → STATE 3 (target = 10% Nifty / 90% Gold)
```

### Step 3: Run Guardrail Checks

Apply all active guardrails and adjust target:
- R1 active → add +20pp Gold to State target
- R2 active → enforce 30% Gold floor on State target
- R5 active → enforce 20% Gold floor on State target
- R3 active → override to State 3 target (10:90)
- R7 active → block mid-quarter lump-sum Nifty sell

### Step 4: Compute 75% Shift

```
gap = target_pct - current_pct (for each asset)
shift_amount = gap * 0.75
shift_rupees = monthly_NAV * shift_amount / 100

If shift_rupees > 0 for Gold: BUY Gold ETF
If shift_rupees < 0 for Gold: SELL Gold ETF
Mirror for Nifty ETF

If already at target allocation: no action
```

### Step 5: Execute Immediately

No waiting period. Record:
- Which rule fired
- Exact data point
- Amounts
- Date
- Prices

### Step 6: Set SIP Allocation for Next Quarter

```
State 1 → 100% Nifty ETF
State 2 → 50% Nifty / 50% Gold
State 3 → 100% Gold ETF
R7 active in State 2 → 100% Nifty ETF (R7 overrides)

SIP Date: 1st of every month
If holiday: +1 day, repeat until trading day found
```

---

## Weekly Decision Tree

**Run every Monday, ~15 minutes**

| Step | Check | Calculation | Action |
|------|-------|-------------|--------|
| 1 | R3 trigger? | `ratio = usoil_today / usoil_12m_avg` → `ratio >= 1.80` | Shift to State 3 (10:90) immediately |
| 2 | R3 yellow? | `ratio >= 1.40 AND ratio < 1.80` | Log + update trigger price monthly |
| 3 | R1 rate trigger? | `pct_change >= 20% AND direction_clean=TRUE AND sustained=TRUE` | Add +20pp Gold |
| 4 | R1 currency trigger? | `inr_depreciation_pct >= 3.0% AND currency_sustained=TRUE` | Add +20pp Gold |
| 5 | R2 trigger? | `real_rate > 3.0%` | 75% shift to State target + 30% Gold floor |
| 6 | R5 trigger? | `bs_yoy > 25%` | Enforce 20% Gold floor |
| 7 | R7 trigger? | `fii_3m_cumulative < 0 AND ABS(fii_3m) >= peak*0.25` | Block mid-quarter Nifty sells / SIP adjustments |
| 8 | Nothing triggered? | All above = FALSE | Log all readings, wait for quarterly check |

---

## Key Data Sources (Status)

| Data | Source | Status |
|------|--------|--------|
| RBI Repo Rate | https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx | ✓ Confirmed |
| USD/INR Rate | https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx | ✓ Confirmed |
| CPI | https://mospi.gov.in/consumer-price-index | ✓ Confirmed |
| RBI Balance Sheet | RBI Weekly Statistical Supplement (WSS) Table 1 | ✓ Confirmed |
| FII Activity | NSDL FPI Yearwise report (fpi.nsdl.co.in) | ✓ Confirmed |
| USOIL (WTI) Price | YFinance CL=F | ✓ Confirmed |
| Gold INR Price | YFinance `GOLD` | ✓ Confirmed — `yfinance_daily.csv` |
| Nifty Index | YFinance `^NSEI` | ✓ Confirmed — `yfinance_daily.csv` |

---

## Implementation Notes

1. **No 48-Hour Protocol**: Execute immediately on trigger confirmation
2. **Portfolio NAV**: Defined as monthly NAV
3. **SIP Date**: 1st of every month (or next trading day if holiday)
4. **Rebalance**: 75% shift rule applies to all State-based rebalances
5. **Floor Rules**: Always respected; never allow Gold to go below applicable floor
6. **Conflicts**: Apply master table; three-way conflicts default to State 2
7. **Logging**: All rule fires, yellow alerts, and executed actions must be logged with timestamps and data points

---

**Document Version**: May 2026 Final  
**Status**: All owner clarifications applied  
**Last Updated**: May 25, 2026
