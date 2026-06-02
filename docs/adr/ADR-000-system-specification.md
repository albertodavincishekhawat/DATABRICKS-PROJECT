# ADR-000 — System Specification: Portfolio Allocation Signal Engine

| Field      | Value                                                                 |
|------------|-----------------------------------------------------------------------|
| **Status** | Accepted                                                              |
| **Date**   | 2026-06-01                                                            |
| **Owner**  | Ravi Singh Shekhawat                                                  |
| **Scope**  | Entire system — all subsequent ADRs derive from this document         |
| **PRD**    | `docs/PRD.md` — business requirements this document translates into engineering requirements |

---

## 1. Problem Statement

Individual investors who hold a two-asset portfolio of Indian equity ETF and Gold ETF have no free, transparent, rules-based tool to determine the correct allocation ratio between these two assets at any given time. Allocation decisions made without systematic guidance are driven by emotion or guesswork, leading to poor timing and missed rebalancing opportunities.

This system collects real macroeconomic data, evaluates five predefined allocation rules against that data, and publishes a recommended portfolio allocation ratio on a public dashboard. Any investor can access it without an account, without providing personal data, and without any technical knowledge.

The system replaces discretionary judgement with a deterministic, data-driven signal. It does not manage individual portfolios. It does not execute trades. It produces a ratio recommendation and the transparent data behind it.

---

## 2. Actors

Actors are the people and systems that interact with this system, either by providing inputs or consuming outputs.

| Actor | Type | Role |
|-------|------|------|
| **Individual investor** | Human, external | Reads the dashboard to determine their recommended allocation ratio. Provides nothing — consumes only. |
| **Data sources** | External systems | Provide the raw macroeconomic data the engine consumes (RBI, MOSPI, NSDL, public market data providers). |
| **Data refresh operator** | Human or automated scheduler | Runs or triggers the data collection jobs on the defined refresh schedule. |
| **System owner / developer** | Human | Maintains the system, monitors data quality, and updates rule definitions when the specification changes. |

---

## 3. System Boundary

### In Scope

| Component | What it does |
|-----------|--------------|
| Data collection pipeline | Fetches and stores all 10 required data parameters on their defined refresh schedules |
| Decision engine | Evaluates all 5 allocation rules against the latest data and determines the current recommended State |
| Public dashboard | Displays the current recommendation, all rule readings, Yellow Alerts, and data freshness to any user via a web browser |
| Audit log | Records every rule evaluation, every trigger, and every State change with full input data and timestamps |
| Data quality guard | Prevents the engine from producing a recommendation when any required data is missing or stale |

### Out of Scope

| Component | Why it is excluded |
|-----------|--------------------|
| Trade execution | The system produces a signal only. Investors act on it themselves. No broker connection. |
| Personal portfolio tracking | The system does not know or store any user's portfolio value, current holdings, or transaction history |
| Rupee or dollar rebalancing amounts | Output is a percentage ratio only. Each user applies it to their own portfolio. |
| SIP allocation management | The system recommends a ratio. Individual SIP decisions are the investor's own responsibility. |
| User accounts or authentication | No login, no registration, no identity. The dashboard is fully public. |
| Tax calculation or reporting | Out of scope permanently for this product. |
| Assets other than Nifty ETF and Gold ETF | The five rules are designed for this two-asset pair specifically. Other assets are out of scope for v1. |
| Real-time streaming data | The decision cadence is weekly and monthly. Streaming data adds cost and complexity with no benefit. |

---

## 4. Assets and Portfolio States

The system makes recommendations for a portfolio consisting of exactly two assets. No other assets are considered.

| Asset | Description |
|-------|-------------|
| **Equity ETF** | An Indian large-cap equity index ETF tracking the Nifty 50 index |
| **Gold ETF** | A Gold ETF traded on the Indian market, priced in Indian Rupees |

The system recommends one of three **States** at all times. A State is a target allocation between the two assets. There is no cash position — the two assets always sum to 100%.

| State | Equity ETF | Gold ETF | When it applies |
|-------|-----------|----------|-----------------|
| **State 1 — Equity Mode** | 80% | 20% | Equity is outperforming Gold over the trailing 6 months by more than 5 percentage points |
| **State 2 — Balanced Mode** | 50% | 50% | The 6-month performance differential between the two assets is within ±5 percentage points |
| **State 3 — Defensive Mode** | 10% | 90% | Gold is outperforming equity over the trailing 6 months by more than 5 percentage points |

The base State is determined by the Quarterly Check (Section 6). The five allocation rules apply guardrails that can override or constrain the base State (Section 5).

---

## 5. Allocation Rules

Five rules are evaluated every week. Each rule monitors a specific macroeconomic signal. Rules are not mutually exclusive — when more than one rule is active simultaneously, the conflict resolution matrix in Section 7 applies.

Each rule has three possible conditions: **Clear** (not triggered, no concern), **Yellow Alert** (approaching threshold, log and monitor), and **Triggered** (threshold crossed, action required).

---

### R1 — Monetary System Shift

**What it monitors:** RBI interest rate cycle stress and INR currency depreciation against USD.

**Why it matters:** Sustained rate hikes or sharp currency weakness signal macroeconomic stress that makes defensive positioning appropriate.

This rule has two independent sub-triggers. Either one can trigger independently.

**Sub-trigger R1A — Interest Rate Cycle**

| Measurement | How it is calculated |
|-------------|----------------------|
| Rate baseline | The repo rate at the start of the current directional cycle (hiking or cutting). Resets when direction reverses. |
| Rate change from baseline | Percentage change between the current repo rate and the rate baseline |
| Direction | Whether RBI is currently in a hiking cycle or a cutting cycle |
| Sustained | Whether the direction has been maintained for at least 2 consecutive MPC meetings |

- **Triggered when:** Rate change from baseline is 20% or more, direction is clean (no reversals mid-cycle), and direction is sustained for at least 2 consecutive MPC meetings
- **Action:** Add 20 percentage points of Gold to the current allocation
- **Yellow Alert when:** Rate change from baseline is 10% or more, direction is clean, and sustained
- **Exits when:** Direction reverses and the reversal is sustained for 2 or more consecutive MPC meetings

**Sub-trigger R1B — Currency Regime**

| Measurement | How it is calculated |
|-------------|----------------------|
| INR depreciation | Percentage change in USD/INR rate comparing today versus 180 calendar days ago. A positive value means INR has weakened. |
| Sustained | Whether the depreciation has held at or above the threshold for at least 30 consecutive calendar days |

- **Triggered when:** INR depreciation is 3.0% or more and has been sustained for at least 30 consecutive days
- **Action:** Add 20 percentage points of Gold to the current allocation
- **Yellow Alert when:** INR depreciation is between 2.0% and 3.0%
- **Exits when:** Depreciation drops below 3.0% and holds below 3.0% for 30 or more consecutive days

**Data required:** RBI Monetary Policy Committee decisions (repo rate per meeting), daily USD/INR exchange rate

---

### R2 — Real Rate Shock

**What it monitors:** The real interest rate — the difference between the RBI repo rate and the current inflation rate.

**Why it matters:** When real interest rates are significantly positive, the cost of holding equity rises relative to risk-free returns, compressing equity valuations and favouring defensive assets.

| Measurement | How it is calculated |
|-------------|----------------------|
| Real rate | RBI repo rate (latest MPC decision) minus India CPI inflation rate (latest published monthly figure) |

- **Triggered when:** Real rate exceeds 3.0%
- **Action:** Move 75% of the way from the current allocation toward the current State target, and enforce a minimum Gold allocation of 30% (if the State target Gold allocation is already above 30%, no override is needed)
- **Yellow Alert when:** Real rate is between 2.0% and 3.0%
- **Exits when:** Real rate falls to 3.0% or below, confirmed by at least one subsequent monthly CPI publication

**Data required:** RBI repo rate (per MPC meeting), India CPI inflation rate (monthly, MOSPI)

---

### R3 — Commodity Shock

**What it monitors:** WTI crude oil price relative to its 12-month rolling average.

**Why it matters:** A large spike in oil prices relative to recent history signals stagflation risk — rising costs with slowing growth — which historically damages equity returns and favours Gold.

| Measurement | How it is calculated |
|-------------|----------------------|
| Oil ratio | Current WTI crude oil price divided by the rolling average of WTI daily prices over the previous 12 calendar months |

- **Triggered when:** Oil ratio is 1.80 or above
- **Action:** Move immediately and fully toward State 3 target (10% equity / 90% Gold) using a 75% shift. No waiting period.
- **Yellow Alert when:** Oil ratio is between 1.40 and 1.80. The trigger price (the oil price that would reach ratio 1.80) must be recalculated on the 1st of each month as the 12-month average updates.
- **Exits when:** Oil ratio falls below 1.50 and stays below 1.50 for 90 or more consecutive calendar days. Maximum hold rule: if oil ratio stays at or above 1.50 for 2 continuous years without meeting the exit condition, force a move to State 2 regardless of the ratio.

**Data required:** Daily WTI crude oil price (public market data)

---

### R5 — Quantitative Easing Regime

**What it monitors:** Year-over-year growth of the RBI balance sheet, excluding foreign currency reserves.

**Why it matters:** Rapid expansion of the RBI balance sheet that is not explained by foreign currency accumulation indicates monetary stimulus. This increases systemic liquidity and inflation risk, making a minimum Gold allocation prudent as a hedge.

| Measurement | How it is calculated |
|-------------|----------------------|
| Balance sheet growth (YoY) | The percentage change in RBI total assets between the latest weekly reading and the reading from exactly 52 weeks prior, with Foreign Currency Assets subtracted from both figures before the comparison |

**Critical requirement:** Foreign Currency Assets (FCA) must be excluded from both the current figure and the year-ago figure before computing the year-over-year growth. Failing to exclude FCA will produce incorrect readings.

- **Triggered when:** Year-over-year balance sheet growth (excluding FCA) exceeds 25%
- **Action:** Enforce a minimum Gold allocation of 20% at all times while the rule is active. This is a floor only — if the State target or another rule already requires more than 20% Gold, this rule does not reduce that requirement.
- **Yellow Alert when:** Year-over-year growth is between 15% and 25%
- **Exits when:** Year-over-year growth falls to 25% or below and holds there for one full calendar month

**Data required:** RBI Weekly Statistical Supplement (WSS), Table 1 — Total Assets, Foreign Currency Assets, Notes in Circulation. Weekly frequency (published each Friday).

---

### R7 — Foreign Institutional Selling Signal

**What it monitors:** Net equity investment flows by foreign portfolio investors (FPIs) in the Indian market over a rolling 3-month window.

**Why it matters:** Heavy sustained selling by foreign institutions often reflects temporary global or macro factors, not Indian market fundamentals. This creates a contrarian buying opportunity — the dislocation caused by foreign selling can represent attractive entry conditions for domestic long-term investors.

| Measurement | How it is calculated |
|-------------|----------------------|
| Peak inflow | The highest single-month net FII equity inflow recorded in the trailing 24 calendar months. Recalculated every month. |
| Outflow threshold | 25% of the peak inflow figure |
| 3-month cumulative flow | The sum of net FII equity investment across the most recent 3 complete calendar months |

- **Triggered when:** The 3-month cumulative flow is negative (net outflow) AND the absolute value of that outflow is equal to or greater than the outflow threshold
- **Action depends on the current State:**
  - State 1 (Equity Mode): No change — already fully in equity
  - State 2 (Balanced Mode): Monthly investment (SIP) goes 100% into equity ETF while R7 is active
  - State 3 (Defensive Mode): Block any mid-quarter lump-sum sale of equity ETF while R7 is active; scheduled quarterly rebalancing proceeds as normal
- **Yellow Alert when:** The absolute value of the 3-month cumulative outflow is 60% or more of the outflow threshold
- **Exits when:** The 3-month cumulative flow turns positive, OR the absolute value of the 3-month outflow falls below the outflow threshold after the monthly recalculation. Exit is immediate with no waiting period.

**Data required:** Monthly net equity investment figures for foreign portfolio investors (FPIs), equity cash segment only (NSDL FPI Yearwise data)

---

## 6. Execution Cadence

The system operates on three recurring schedules.

### Weekly Rule Evaluation (every Monday)

The engine evaluates all five rules in a defined order and produces a current recommended State. Rules are evaluated in the following sequence because R3, if triggered, overrides all others and makes further evaluation unnecessary:

1. Evaluate R3 (oil shock) first — if triggered, the result is State 3 immediately
2. Check R3 Yellow Alert
3. Evaluate R1A (rate cycle)
4. Evaluate R1B (currency)
5. Evaluate R2 (real rate)
6. Evaluate R5 (balance sheet)
7. Evaluate R7 (FII selling)
8. Apply conflict resolution if more than one rule is triggered (Section 7)
9. Publish the result — either a State recommendation or "no change"

If no rule is triggered: log all readings and confirm the current State is unchanged.

### Quarterly State Check (1 January, 1 April, 1 July, 1 October — or the next trading day if a public holiday)

The base State is recalculated once per quarter using 6-month asset performance:

1. Measure the 6-month return of the equity ETF and the Gold ETF
2. Compute the performance differential (equity return minus Gold return)
3. Determine the base State: differential above +5% → State 1, between −5% and +5% → State 2, below −5% → State 3
4. Apply all active rule guardrails on top of the base State
5. Apply the conflict resolution matrix if needed
6. Move 75% of the way from the current allocation toward the resulting target allocation
7. Set the monthly investment (SIP) allocation for the coming quarter based on the resulting State

### Data Refresh Schedule

The system must support two refresh modes:

1. **Automated monthly refresh** — the system refreshes all data parameters once per month automatically, without human intervention. The scheduling platform is an implementation decision deferred to ADR-004.
2. **Manual trigger** — a person can trigger a full refresh of any or all parameters at any time, on demand.

When a refresh runs (automated or manual), each parameter is fetched up to the current date at the frequency its source publishes. Data is not downsampled — it is stored at its native source frequency.

| Data parameter | Source frequency | Data stored at |
|----------------|-----------------|----------------|
| Equity ETF price | Daily (trading days) | Daily |
| Gold ETF price | Daily (trading days) | Daily |
| WTI crude oil price | Daily (trading days) | Daily |
| USD/INR exchange rate | Daily (trading days) | Daily |
| RBI repo rate | Daily (derived from MMO report) | Daily |
| RBI balance sheet | Weekly (each Friday) | Weekly |
| India CPI | Monthly (published ~12th of following month) | Monthly |
| FII monthly flows | Monthly (published ~1st of following month) | Monthly |

---

## 7. Conflict Resolution

When more than one rule is triggered at the same time, the following matrix determines the outcome. The matrix is exhaustive — every combination is defined.

| Active rules | Resolution |
|-------------|------------|
| R1 + R2 | R1 takes priority. Its +20pp Gold addition already satisfies R2's 30% Gold floor. |
| R1 + R3 | Both apply. R3 drives the allocation to State 3 (90% Gold). R1 adds a further +20pp, capped at 90% Gold total. |
| R1 + R5 | R1 takes priority. Its +20pp Gold addition already exceeds R5's 20% Gold floor. |
| R1 + R7 | Lump-sum allocation: apply R1's +20pp Gold shift. Monthly investment: 50% equity / 50% Gold. |
| R2 + R3 | R3 overrides. State 3 target is 90% Gold, which already exceeds R2's 30% Gold floor. R2 is redundant. |
| R2 + R5 | R2 applies. Its 30% Gold floor is more restrictive than R5's 20% floor. |
| R2 + R7 | Lump-sum allocation: maintain current ratio. Monthly investment: split proportionally between the two assets. |
| R3 + R5 | R3 overrides. State 3 target (90% Gold) exceeds R5's 20% floor. R5 is redundant. |
| R3 + R7 | R3 drives all allocation decisions. Monthly investment: 100% Gold ETF. |
| R5 + R7 | Rules are independent. R5 enforces the 20% Gold floor. R7 tilts monthly investment toward equity within that floor. |
| R1 + R2 + R7 | Default to State 2 (50% equity / 50% Gold). R1 pushes toward Gold, R7 pushes toward equity, R2 enforces 30% Gold floor — the competing signals resolve to a neutral allocation. |

---

## 8. Output Requirements

The system must produce the following outputs. How these outputs are delivered (email, dashboard, file) is an implementation decision defined in the Solution Architecture Document.

### Current Recommendation (produced each week after rule evaluation)

Every weekly run must produce a record containing:
- The date of the evaluation
- The current recommended State (1, 2, or 3) and the corresponding percentage allocation
- Which rules are currently triggered (if any)
- Which rules are in Yellow Alert (if any)
- The current reading for every rule, alongside the threshold that would trigger it
- Whether this represents a change from the previous State or a continuation

### Quarterly Rebalancing Instruction (produced on each quarterly check date)

Every quarterly run must produce a record containing:
- The date of the quarterly check
- The base State determined by the 6-month performance differential
- The final State after applying all active rule guardrails
- The target allocation in percentages
- The recommended shift — expressed as a percentage movement, not a rupee amount
- The monthly investment (SIP) allocation split for the coming quarter

### Audit Log (append-only)

Every run — weekly, quarterly, or data refresh — must append a structured record to the audit log containing the run type, all input readings, the result, and a timestamp. The audit log must never be modified retroactively.

---

## 9. Success Criteria

The system is meeting its requirements when all of the following are true at the same time:

1. The public dashboard displays a current State recommendation that any user can access without an account or technical knowledge
2. Every rule displays its current reading and the threshold that would trigger it
3. All data freshness timestamps are current and accurate
4. When any data parameter is missing or stale, the system displays a data error rather than a recommendation
5. Given the same historical input data on any two separate runs, the system produces identical State recommendations — the output is fully deterministic
6. Every State change is traceable in the audit log to the specific rule reading that caused it

---

## 10. Quality Requirements

| Requirement | Definition |
|-------------|------------|
| **Data integrity** | No synthetic, estimated, or fabricated data is used for any parameter at any time |
| **Determinism** | Identical input data must always produce identical output |
| **Auditability** | Every rule evaluation and every State change is recorded in the audit log with full input data |
| **Data guard** | The engine must not produce a recommendation when any required data parameter is missing or outside its freshness window |
| **Cost** | Zero recurring cost for data. Infrastructure cost must be minimal and proportionate to a personal educational project. |
| **Accessibility** | The dashboard must be accessible via a standard web browser without installing software, creating an account, or providing any personal information |
| **Transparency** | Every recommendation must be accompanied by the full set of data readings that produced it, so any user can verify the logic themselves |

---

## 11. Assumptions

These are the conditions we are taking as given. If any assumption proves false, the affected parts of this specification must be reviewed.

| # | Assumption |
|---|------------|
| A-01 | MOSPI publishes India CPI data publicly and reliably by the 12th of the month following the reference month |
| A-02 | RBI publishes MPC rate decisions on the day of the meeting, publicly and without restriction |
| A-03 | NSDL publishes monthly FII equity flow data publicly by the 1st of the month following the reference month |
| A-04 | RBI publishes weekly balance sheet data (WSS) publicly within 5 days of each Friday |
| A-05 | Public market data for Nifty ETF and Gold ETF is available with a one-trading-day lag from a free source |
| A-06 | The five allocation rules are stable — changes to rule thresholds or logic require a new version of this document and must be approved before implementation |
| A-07 | The Nifty ETF and Gold ETF are sufficiently liquid that the percentage allocation recommendation is always actionable by an individual investor |
| A-08 | The system is for informational and educational purposes — it is not a regulated financial advisory service and does not require regulatory approval to operate |

---

## 12. Constraints

These are non-negotiable boundaries. They cannot be overridden by implementation decisions.

| # | Constraint | Reason |
|---|------------|--------|
| C-01 | All data sources must be free and publicly accessible | Ensures zero recurring data cost and no dependency on commercial providers |
| C-02 | No user personal data may be collected, stored, or processed | Privacy boundary — the system must be usable without any trust relationship between user and system |
| C-03 | Output is a percentage ratio only — no personalised rupee or dollar amounts | The system is a signal tool, not a personal portfolio manager |
| C-04 | No trade execution or broker connectivity | The system produces recommendations only |
| C-05 | The two assets are fixed as Nifty ETF and Gold ETF | The five rules are calibrated for this asset pair specifically |
| C-06 | No recommendation may be displayed when required data is stale or missing | A stale recommendation is worse than no recommendation |

---

## 13. Open Questions

These questions must be answered before the dashboard can be built. They do not block writing the Solution Architecture Document.

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| OQ-01 | What disclaimer text must appear on the dashboard to communicate educational and non-advisory purpose? | **Resolved** | Standard educational disclaimer: "This tool is for educational and informational purposes only. It does not constitute financial advice. Consult a registered financial advisor before making investment decisions." |
| OQ-02 | Is the data refresh operator a human running scripts manually, or an automated scheduler? | **Resolved** | Both. The system must support an automated monthly refresh with no human intervention, and a manual on-demand trigger. The scheduling platform is deferred to ADR-004. |
| OQ-03 | What should the dashboard show when a data refresh is in progress — last known State with a notice, or a loading state? | **Open** | Must be decided before dashboard build |
| OQ-04 | What platform hosts the public dashboard? | **Resolved** | Architecture decision deferred to SAD — not a question for this document. |
| OQ-05 | Is GOLDBEES.NS the correct proxy for Gold ETF price, or is a spot price source needed? | **Resolved** | Gold price sourced via YFinance ticker `GOLD` (USD spot price). Equity ETF proxy is `NIFTYBEES.NS`. GOLDBEES.NS is not used. |

---

## 14. Subsequent Documents

This specification is technology-agnostic. The following documents must be written in sequence before implementation begins. Each one inherits from this document and from the PRD.

| Document | Decides | Cannot be written until |
|----------|---------|------------------------|
| SAD — Solution Architecture Document | Full architecture, technology stack, component design, data flow | This document is accepted |
| ADR-001 — Data Collection Architecture | How data is collected, scheduled, and stored | SAD is accepted |
| ADR-002 — Data Storage Strategy | Where and how data is stored between collection and evaluation | SAD is accepted |
| ADR-003 — Decision Engine Implementation | How and where the rule engine runs | ADR-002 is accepted |
| ADR-004 — Orchestration Platform | What schedules and coordinates all components | ADR-002 is accepted |
| ADR-005 — Data Quality and Synchronisation | How missing or late data is handled per rule | ADR-001 is accepted |
| ADR-006 — Deployment and Environments | How dev, UAT, and production are separated | ADR-003 and ADR-004 are accepted |

---

*This document is the authoritative engineering specification. It translates the business requirements in the PRD into precise engineering requirements. All implementation decisions must satisfy this document. When code and this document disagree, the code is wrong.*
