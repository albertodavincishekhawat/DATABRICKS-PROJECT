# PRD — Product Requirements Document
# Portfolio Allocation Signal Tool

| Field        | Value                          |
|--------------|--------------------------------|
| **Status**   | Accepted                       |
| **Date**     | 2026-05-27                     |
| **Owner**    | Ravi Singh Shekhawat           |
| **Governs**  | The full scope of what this product must do and for whom |

---

## 1. Purpose of This Document

This document defines what the product must do, who it is for, and what success looks like. It contains no technology choices. It is written so that any person — technical or not — can read it, confirm it matches the intent, and approve it. All engineering decisions that follow must be consistent with this document. When this document and any other document disagree, this document takes priority.

---

## 2. Problem Statement

Individual investors who hold Indian equity ETFs and Gold ETFs must periodically decide how much of their portfolio should be in each asset. Most investors make this decision based on gut feeling, media noise, or one-sided advice. This leads to poor timing — buying equity when markets are overheated, holding too much gold when equity is the better opportunity, or simply never rebalancing at all.

There is no free, transparent, publicly accessible tool that monitors the real macroeconomic signals relevant to this decision and tells an investor, in plain terms, what the recommended allocation ratio should be right now — and why.

This product solves that problem.

---

## 3. The User

**Who they are**: Any individual investor, anywhere in the world, who holds or is considering a two-asset portfolio of Indian equity ETF (Nifty ETF) and Gold ETF.

**What they know**: They understand what Nifty ETF and Gold ETF are. They do not need to understand macroeconomics, central bank policy, or financial modelling to use this tool.

**What they need**: A clear, trustworthy recommendation — expressed as a percentage allocation — that they can act on. They need to know what the recommendation is and that it is based on real, transparent data.

**What they do not want**: Jargon, hidden assumptions, personal data requests, or a recommendation they cannot verify. They should never have to take the tool's word for something they cannot check.

**What this tool is not for**: Day traders, fund managers, or anyone managing multiple asset classes. This tool is for long-term investors making allocation decisions between exactly two assets.

**No account required. No personal data collected. No portfolio value needed.**

---

## 4. Key Terms

| Term | Meaning |
|------|---------|
| **State** | The recommended allocation between the two assets. There are three States: equity-heavy (80/20), balanced (50/50), and defensive (10/90). The system is always in exactly one State. |
| **Yellow Alert** | A warning that a rule is approaching its activation threshold but has not yet crossed it. Yellow Alerts do not change the current State — they tell the user that a change may be coming. |
| **Allocation ratio** | The percentage split between Nifty ETF and Gold ETF. Expressed as two numbers that sum to 100 — for example, 80% Nifty / 20% Gold. |
| **Rule** | A macroeconomic signal that the system monitors. When a rule's threshold is crossed, it adjusts the recommended State or places a minimum floor on Gold allocation. |

---

## 5. Functional Requirements — What the System Must Do

The following requirements are numbered. All of them must be satisfied for the product to be considered complete.

**FR-01 — Collect real macroeconomic data**
The system must collect real, publicly available data for all required input parameters on their defined refresh schedule. No synthetic, estimated, or fabricated data is permitted for any parameter at any time.

**FR-02 — Evaluate the allocation rules**
The system must evaluate all five allocation rules against the latest data every week. The rules are fully specified in the System Specification (ADR-000). The PRD does not define rule logic — it only requires that the rules be evaluated correctly and completely.

The five rules and what each one monitors:
- **R1 — Monetary System Shift**: Monitors RBI interest rate cycles and INR currency depreciation against the US Dollar
- **R2 — Real Rate Shock**: Monitors the difference between the RBI interest rate and the current inflation rate
- **R3 — Commodity Shock**: Monitors WTI crude oil prices relative to their 12-month average
- **R5 — Quantitative Easing Regime**: Monitors year-over-year expansion of the RBI balance sheet, excluding foreign currency reserves
- **R7 — Foreign Institutional Selling Signal**: Monitors net equity investment flows from foreign portfolio investors over a rolling 3-month window

**FR-03 — Determine the current recommended allocation**
Based on the rule evaluations, the system must determine a single recommended portfolio State:
- **State 1**: 80% Nifty ETF / 20% Gold ETF — equity conditions are favourable
- **State 2**: 50% Nifty ETF / 50% Gold ETF — neutral or mixed conditions
- **State 3**: 10% Nifty ETF / 90% Gold ETF — defensive conditions

**FR-04 — Publish the recommendation on a public web dashboard**
The recommendation must be accessible to any person via a web browser. No login, account, or registration is required. The dashboard must be readable without technical knowledge.

**FR-05 — Show all rule readings transparently**
The dashboard must display the current reading for every rule — the actual numbers, thresholds, and whether each rule is inactive, in Yellow Alert (approaching threshold), or triggered. A user must be able to see exactly why the current State was recommended.

**FR-06 — Show Yellow Alerts**
When a rule is approaching its trigger threshold but has not yet fired, the dashboard must show a Yellow Alert for that rule. Yellow Alerts are informational only — they do not change the recommended State but tell the user that a change may be coming.

**FR-07 — Show data freshness**
The dashboard must display when each data source was last refreshed. If data is stale, this must be visible — not hidden.

**FR-08 — Refuse to show a recommendation when data is missing or stale**
If any required data parameter is missing or has not been refreshed within its defined freshness window, the system must not display a recommendation. It must show a clear, visible data error that identifies which parameter is the problem. A stale recommendation is worse than no recommendation.

**FR-09 — Provide a historical simulation tool**
The dashboard must include an optional simulation tool that allows a user to enter a hypothetical start date, lump sum amount, and monthly SIP amount, and see an illustrative chart of how a portfolio following the strategy would have performed from that date to today using actual historical prices and historically recommended States.

The simulation must:
- Run entirely in the user's browser — no user-entered values are transmitted to any server or stored anywhere
- Use actual historical asset prices and the historically computed States published by the decision engine
- Apply the same rules the live engine uses: split the lump sum at the State recommended on the start date, invest the SIP each month at that month's recommended State, and apply the quarterly rebalancing rule
- Display the result as a chart of portfolio value over time
- Be clearly labelled as an educational illustration only — not a guarantee of future performance

The user-provided lump sum and SIP amounts exist only for the duration of the browser session. They are never stored, never transmitted, and never shared with any server.

---

## 6. Explicit Exclusions — What the System Must NOT Do

These are hard boundaries. They are not deferred to later versions — they are out of scope permanently unless this document is updated.

- **Must not collect or store any user personal data** — no names, emails, or browsing history. User-entered simulation amounts (lump sum, SIP) are processed client-side only and never transmitted or stored.
- **Must not execute trades** — the system produces a signal only; the investor acts on it themselves
- **Must not connect to any broker or trading platform**
- **Must not require a user account, login, or registration of any kind**
- **Must not claim to provide financial advice** — the tool is for educational and informational purposes only
- **Must not use paid data sources** — all input data must come from free, publicly accessible sources
- **Must not produce a personalised rupee or dollar amount** — output is a percentage ratio only; each user applies it to their own portfolio
- **Must not cover any asset classes beyond Nifty ETF and Gold ETF in version 1**

---

## 7. Success Criteria — How We Know the System Is Working

The system is working correctly when all of the following are true simultaneously:

1. Any person can open the dashboard in a browser and see a current recommended State without needing to do anything else
2. Every rule displays its current reading alongside the threshold that would trigger it
3. A person with no financial background can read the dashboard and understand the recommendation and the reason behind it
4. When a data source is missing or overdue for refresh, the system shows a data error rather than a potentially stale recommendation
5. The data freshness timestamps are visible and accurate for every parameter

---

## 8. Constraints — Non-Negotiable Boundaries

These constraints cannot be negotiated away without a new version of this document.

| Constraint | Reason |
|------------|--------|
| All data sources must be free and publicly available | Ensures the tool can run at no recurring cost and remains independent of commercial data providers |
| Educational and informational purpose only — not regulated financial advice | Legal boundary; the tool must not position itself as a regulated advisory service |
| The two assets are fixed at Nifty ETF and Gold ETF | The allocation rules are designed specifically for this two-asset pair; adding other assets changes the rule logic and is out of scope for v1 |
| No user data collection | Privacy boundary; the tool must be usable without any trust relationship between the user and the system |

---

## 9. Assumptions

These are things we are taking as true. If any of them turn out to be false, this document and the engineering decisions that follow from it must be reviewed.

- MOSPI publishes India CPI data by the 12th of the following month
- RBI publishes Monetary Policy Committee (MPC) rate decisions on the day of the meeting
- NSDL publishes FII monthly equity flow data by the 1st of the following month
- RBI publishes weekly balance sheet data (WSS) within 5 days of each Friday
- Public price data for Nifty ETF and Gold ETF is available with a one-day lag from standard market data sources
- The five allocation rules are complete and stable — changes to the rules require a new version of the System Specification (ADR-000) and this document

---

## 10. Open Questions

These questions must be answered before the product can be considered fully specified. They do not block writing the next document but must be resolved before the dashboard is built.

| # | Question | Impact if unresolved |
|---|----------|----------------------|
| OQ-01 | What disclaimer text must appear on the dashboard to correctly communicate that this is educational and not regulated financial advice? | Legal framing of the dashboard |
| OQ-02 | Who is responsible for running the data refresh jobs — is it the developer running a script manually, or does it run automatically on a schedule? | Determines whether automation is a requirement or a convenience |
| OQ-03 | When a user opens the dashboard while a data refresh is in progress, what should they see — the last known State with a "refreshing" notice, or a loading state until the refresh completes? | Dashboard behaviour under refresh conditions |
| OQ-04 | What platform hosts the public dashboard — a web server, a hosted notebook, or a serverless function? | Architecture decision deferred to the Solution Architecture Document |

---

*This document governs the product scope. It is read alongside the System Specification (`docs/adr/ADR-000-system-specification.md`), which translates these business requirements into precise engineering requirements. When this document and ADR-000 disagree, this document takes priority.*
