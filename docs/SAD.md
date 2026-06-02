# SAD — Solution Architecture Document
# Portfolio Allocation Signal Tool

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Date** | 2026-06-01 |
| **Owner** | Ravi Singh Shekhawat |
| **Implements** | `docs/PRD.md`, `docs/adr/ADR-000-system-specification.md` |
| **Governs** | `docs/adr/ADR-001` through `docs/adr/ADR-006` |
| **Format note** | This `.md` file is the working specification. A final formatted document with colour architecture diagrams will be produced once the SAD is accepted. |

---

## 1. Executive Summary

The Portfolio Allocation Signal Tool is a public web application that monitors five macroeconomic indicators and publishes a monthly recommended allocation ratio between a Nifty 50 ETF and a Gold ETF. Any individual investor can open the dashboard in a browser — no login, no account, no personal data required.

The system is built entirely on free-tier infrastructure. AWS Lambda functions fetch raw data from external sources and write it to Amazon S3. A monthly Databricks Job reads from S3 and processes the data through a Bronze → Silver → Gold medallion architecture using Delta tables. The Gold notebook evaluates the five allocation rules, determines the recommended State, and publishes the result as a JSON file to GitHub via the GitHub API. A GitHub Pages site reads that file and displays the public dashboard. A Phase 2 GenAI notebook calls the Gemini API to generate a plain-language explanation of the current recommendation.

**Full technology stack:**

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Data collection | AWS Lambda (one parameterized function, triggered by EventBridge Scheduler or manually) |
| Raw file storage | Amazon S3 |
| Data ingestion trigger | AWS EventBridge Scheduler (scheduled + parameterized manual invocation) |
| Data processing | Delta Lake — Bronze / Silver / Gold medallion architecture |
| Compute | Databricks Community Edition (single-node cluster) |
| Orchestration | Databricks Jobs (monthly cron schedule, configured in Databricks) |
| Output format | JSON (`current_state.json`) |
| Audit log | Delta table (Gold layer, append-only) |
| Dashboard | GitHub Pages (static HTML/CSS/JS) |
| Dashboard data source | `current_state.json` committed to GitHub repo via GitHub API |
| GenAI (Phase 2) | Gemini API free tier, called from a Databricks notebook |

Infrastructure cost: **zero**. All components run on free tiers.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        External Data Sources                          │
│  Yahoo Finance  │  RBI  │  MOSPI  │  NSDL  │  rateinflation.com      │
└──────┬───────────────┬──────────┬──────────┬──────────┬──────────────┘
       │               │          │          │          │
       ▼               ▼          ▼          ▼          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    AWS — Data Collection Layer                         │
│                                                                       │
│  EventBridge Scheduler                                                │
│    scheduled rules (per-source cron) ──┐                             │
│    manual invocation via AWS Console ──┤                             │
│                                        ▼                             │
│  AWS Lambda  (single parameterized function)                          │
│    event: { "scraper": "all|yfinance|usoil|rbi_mmo|                  │
│                          rbi_wss|cpi|nsdl_fpi",                      │
│             "mode":    "upsert|full_refresh" }                        │
│    uses src/data_collection/collectors/ scraper files                 │
│    → writes CSV files to S3                                           │
│                                        │                             │
│  Amazon S3  (raw landing zone)         │                             │
│    s3://portfolio-signal-raw/          │                             │
│      yfinance_daily/yfinance_daily.csv │                             │
│      usoil_daily/usoil_daily.csv       │                             │
│      repo_rate_daily/repo_rate_daily.csv                             │
│      rbi_wss/rbi_wss_monthly.csv       │                             │
│      cpi_monthly/cpi_combined.csv      │                             │
│      fii_monthly/fii_nsdl_monthly.csv  │                             │
│                                        │                             │
└────────────────────────────────────────┼─────────────────────────────┘
                                         │ S3 read
                                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│              DATABRICKS COMMUNITY EDITION WORKSPACE                   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  Databricks Job (monthly cron)                               │     │
│  │                                                              │     │
│  │  Task 1: Bronze notebook                                     │     │
│  │    reads CSV files from S3 → adds metadata                   │     │
│  │    → Delta bronze tables on DBFS                             │     │
│  │                         │                                    │     │
│  │  Task 2: Silver notebook │                                   │     │
│  │    bronze → cleaned, validated Delta silver tables           │     │
│  │                         │                                    │     │
│  │  Task 3: Gold notebook   │                                   │     │
│  │    silver → rule engine (R3,R1A,R1B,R2,R5,R7)               │     │
│  │    → Delta gold table + current_state.json on DBFS           │     │
│  │                         │                                    │     │
│  │  Task 4: Publish notebook│                                   │     │
│  │    reads current_state.json from DBFS                        │     │
│  │    → pushes current_state.json + historical_states.json      │     │
│  │    → GitHub API → GitHub Pages auto-rebuilds (~2 min)        │     │
│  │                                                              │     │
│  │  Task 5: GenAI notebook (Phase 2)                            │     │
│  │    reads gold table → calls Gemini API                       │     │
│  │    → appends plain-language summary to JSON → push to GitHub │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
│  DBFS Storage:                                                        │
│    /bronze/       ← Delta bronze tables                               │
│    /silver/       ← Delta silver tables                               │
│    /gold/         ← Delta gold tables + current_state.json            │
│                             + historical_states.json                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                               │
                    GitHub API push (Task 4)
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                                 │
│   current_state.json  (updated by Databricks job each month)         │
│   docs/dashboard/     (static HTML/CSS/JS — the public dashboard)    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                    GitHub Pages serves the site
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│              Public Dashboard (GitHub Pages)                          │
│  Static HTML/JS fetches current_state.json → displays recommendation │
│  No login. No account. Accessible to anyone with the URL.            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### 3.1 Language — Python 3.11

All data collection code is already written in Python. The Databricks runtime natively supports Python notebooks. No other language is needed.

**Rejected:** Scala/Java — no advantage for this workload and requires more boilerplate. R — no advantage over Python for this use case.

### 3.2 Compute — AWS Lambda + Databricks Community Edition

Two compute layers serve different roles:

**AWS Lambda** handles all data collection. One parameterized Lambda function runs the scraper code from `src/data_collection/collectors/`. It is triggered by EventBridge Scheduler on a per-source schedule or invoked manually via the AWS Console or CLI. Lambda's permanent free tier (1M requests/month, 400K GB-seconds/month) covers this workload at zero cost.

**Databricks Community Edition** handles all data processing (Bronze → Silver → Gold) and publishing. Community Edition provides a single-node cluster (15 GB RAM, 2 cores), Delta Lake, DBFS, and multi-task Jobs at no cost. The cluster auto-terminates after 2 hours of inactivity and cold-starts in 5–10 minutes when a Job triggers — acceptable for a monthly pipeline.

**Rejected:** Local Python scripts — not reliably scheduled, tied to the developer's machine. Paid Databricks tiers — unnecessary at this data volume.

### 3.3 Data Storage — Amazon S3 (raw) + DBFS + Delta Lake (processed)

Storage is split across two layers:

**Amazon S3** is the raw landing zone. Lambda writes one CSV file per data source. S3 persists across Lambda invocations, is accessible from Databricks via the S3 SDK, and costs less than $0.01/month at under 50 MB total. The S3 free tier (5 GB, first 12 months) covers the initial period; ongoing cost is negligible.

**DBFS + Delta Lake** holds all processed data. Delta tables provide ACID guarantees, time travel for the audit log, and schema enforcement across Bronze, Silver, and Gold layers. Total Delta storage is under 50 MB — well within DBFS limits on Community Edition.

**Rejected:**
- **DBFS for raw storage** — Lambda cannot write to DBFS; S3 is the correct raw landing zone for Lambda-based collection.
- **CSV files only (no Delta)** — no schema enforcement, no time travel, no query capability for the processed layers.
- **PostgreSQL / external database** — requires a running server; incompatible with the zero-cost constraint.

### 3.4 Pipeline Architecture — Medallion (Bronze / Silver / Gold)

Three Delta table layers transform raw scraped data into a clean, rule-evaluated output:

| Layer | What it contains | Written by |
|-------|-----------------|-----------|
| **Bronze** | Raw ingested data with source metadata and ingestion timestamp. No transformation beyond parsing. | Bronze notebook |
| **Silver** | Cleaned, validated, type-cast data. Nulls handled. Date formats standardised. Ranges validated. | Silver notebook |
| **Gold** | Rule evaluations, State determination, conflict resolution output, current recommendation. | Gold notebook |

**Rejected:** Delta Live Tables (DLT) — not available on Community Edition. Plain notebooks writing Delta tables directly achieve the same medallion structure without DLT.

### 3.5 Orchestration — EventBridge Scheduler + Databricks Jobs

Two orchestration mechanisms operate independently:

**AWS EventBridge Scheduler** triggers the Lambda function on a per-source cron schedule. Each schedule passes a fixed JSON payload (`scraper` + `mode`) to the Lambda. Multiple schedules can point to the same Lambda with different parameters — no code changes needed to adjust timing or scope. EventBridge's permanent free tier (14M invocations/month) covers this at zero cost.

**Databricks Jobs** orchestrates the medallion pipeline. A single multi-task Job runs on a monthly cron schedule, configured entirely within the Databricks workspace. Tasks run in sequence: Bronze → Silver → Gold → Publish → (Phase 2) GenAI. Each task depends on the previous one succeeding.

**Rejected:** GitHub Actions — adds an external trigger mechanism and REST API complexity. Local cron — unreliable, tied to developer machine.

### 3.6 Dashboard — GitHub Pages

The Gold notebook writes `current_state.json` to DBFS. The Publish notebook reads it and commits it to the GitHub repository via the GitHub Contents API. GitHub Pages serves a static HTML/CSS/JS site from the same repository. The dashboard JavaScript fetches `current_state.json` from the repository's raw content URL and renders the recommendation.

**Why GitHub Pages:** Free, no server, no build pipeline, truly public with no login requirement. The dashboard is a static file that any browser can load.

**Rejected:**
- **Databricks legacy dashboards** — require a Databricks account to view. Not compatible with the no-login requirement.
- **Vercel + Next.js** — adds a build pipeline and deployment configuration. GitHub Pages with plain HTML/JS is simpler and equally capable for this dashboard's needs.
- **Streamlit** — requires a persistent server; not reliably free.

### 3.7 GenAI — Gemini API Free Tier (Phase 2)

A Gemini API call from within a Databricks notebook generates a plain-language explanation of the current recommendation — why the current State was selected, which rules are active, and what the data readings mean in plain English. The response is appended to `current_state.json` under a `summary` field before the Publish step commits the file to GitHub.

**Why Gemini API free tier:** The free tier supports sufficient call volume for a weekly job. No model serving infrastructure is required — the notebook makes an outbound HTTP call and processes the response. Databricks Model Serving is not needed.

**Rejected:** Databricks Model Serving — not available on Community Edition. OpenAI API — paid from the start; Gemini free tier meets the zero-cost constraint.

---

## 4. Component Design

### 4.1 Lambda Data Collection Function

> **⚠ Implementation TODO** — Lambda code not yet written. Full specification below.

A single AWS Lambda function handles all data collection. It is parameterized via its event payload so that EventBridge schedules and manual invocations can each target any subset of scrapers in either ingestion mode.

**Event payload schema:**
```json
{ "scraper": "all | yfinance | usoil | rbi_mmo | rbi_wss | cpi | nsdl_fpi",
  "mode":    "upsert | full_refresh" }
```

**Scraper → S3 output mapping:**

| `scraper` value | Source file in `collectors/` | S3 output path |
|---|---|---|
| `yfinance` | `yfinance_scraper.py` | `s3://portfolio-signal-raw/yfinance_daily/yfinance_daily.csv` |
| `usoil` | `usoil_scraper.py` | `s3://portfolio-signal-raw/usoil_daily/usoil_daily.csv` |
| `rbi_mmo` | `rbi_mmo_scraper.py` | `s3://portfolio-signal-raw/repo_rate_daily/repo_rate_daily.csv` |
| `rbi_wss` | `rbi_wss_scraper.py` | `s3://portfolio-signal-raw/rbi_wss/rbi_wss_monthly.csv` |
| `cpi` | `cpi_mospi_scraper.py` | `s3://portfolio-signal-raw/cpi_monthly/cpi_combined.csv` |
| `nsdl_fpi` | `nsdl_fpi_scraper.py` | `s3://portfolio-signal-raw/fii_monthly/fii_nsdl_monthly.csv` |

**Ingestion modes:**

*Upsert* — incremental refresh:
1. Read existing CSV from S3 for this scraper.
2. Find the last date in that file.
3. Fetch only data from `last_date + 1` to today from the external source.
4. Append new rows to the existing data.
5. Write the merged CSV back to S3.

*Full refresh* — smart historical merge:
1. Fetch all data from January 2020 to today from the external source.
2. Read existing CSV from S3.
3. Merge on date using these rules:
   - Date only in existing → keep existing row.
   - Date only in new fetch → add new row (fills historical gaps).
   - Date in both → keep existing values; fill only null/missing columns from new fetch.
4. Write the merged CSV back to S3 (never blindly overwrites — existing data is never lost).

**`scraper: "all"`** runs all six scrapers sequentially in the order above using the specified mode.

**EventBridge schedule design:**

| Schedule name | Cron | Payload | Purpose |
|---|---|---|---|
| `monthly-full-run` | `cron(0 2 1 * ? *)` | `{"scraper":"all","mode":"upsert"}` | Normal monthly data refresh |
| `monthly-cpi` | `cron(0 2 14 * ? *)` | `{"scraper":"cpi","mode":"upsert"}` | CPI published ~12th; fetch on 14th |

**Manual invocation (AWS Console → Lambda → Test, or CLI):**
```bash
aws lambda invoke --function-name portfolio-scraper \
  --payload '{"scraper":"rbi_wss","mode":"full_refresh"}' response.json
```

**Lambda configuration:**
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 10 minutes (covers all 6 scrapers sequentially)
- Dependencies (Lambda layer or deployment package): `pandas`, `yfinance`, `requests`, `beautifulsoup4`, `curl-cffi`, `openpyxl`, `boto3`
- IAM permissions: `s3:GetObject`, `s3:PutObject` on `s3://portfolio-signal-raw/*`

**Inputs:** Public web endpoints (same as existing scraper files).
**Outputs:** CSV files written to S3. One file per scraper, overwritten in place each run.
**Failure behaviour:** Exception logged to CloudWatch. S3 is not written if the scraper fails — existing S3 file is preserved. Databricks Bronze will read the last successfully written file on its next run.

### 4.2 Bronze Notebook (Task 1 in Databricks Job)

Reads all raw CSV files from Amazon S3, adds metadata columns (`ingested_at`, `source`), enforces schema, and writes to Delta tables at `/bronze/` on DBFS.

**Inputs:** CSV files from `s3://portfolio-signal-raw/` — one file per data source.
**Outputs:** Delta tables at `/bronze/` on DBFS — one table per data source.
**Failure behaviour:** Exits with exception on schema mismatch or missing S3 file. Job stops.

### 4.3 Silver Notebook (Task 3)

Reads Bronze Delta tables. Applies cleaning per parameter: type casting, null handling, date standardisation, out-of-range validation. Writes to Delta tables at `/silver/`.

**Inputs:** Delta tables at `/bronze/`.
**Outputs:** Delta tables at `/silver/` — cleaned and validated.
**Failure behaviour:** Exits with exception on failed validation. Job stops.

### 4.4 Gold Notebook (Task 4)

The decision engine. Reads Silver Delta tables. Runs the data quality guard, then evaluates all five rules in the defined order, applies the conflict resolution matrix, determines the recommended State, and produces two outputs.

**Execution steps:**
1. **Data quality guard** — Check freshness of each parameter against the SLA in ADR-000 Section 6. If any parameter is stale or missing, write a `data_error` record and exit.
2. **Load data** — Read relevant Silver tables into DataFrames.
3. **Evaluate rules** — R3 first (immediate State 3 if triggered), then R1A, R1B, R2, R5, R7.
4. **Conflict resolution** — Apply the matrix from ADR-000 Section 7.
5. **State determination** — Combine quarterly check base State with active rule guardrails.
6. **Write outputs** — Append a record to the `/gold/rule_evaluations/` Delta table. Write `current_state.json` to DBFS `/gold/output/`.

**Inputs:** Delta tables at `/silver/`.
**Outputs:** Delta table at `/gold/rule_evaluations/` (append-only, audit log); `current_state.json` on DBFS `/gold/output/`; `historical_states.json` on DBFS `/gold/output/`.
**Failure behaviour:** Any unhandled exception writes an error record to `current_state.json` with `has_recommendation: false` and an `error_reason` field.

### 4.5 Publish Notebook (Task 5)

Reads `current_state.json` and `historical_states.json` from DBFS `/gold/output/`. Calls the GitHub Contents API (`PUT /repos/{owner}/{repo}/contents/{file}`) to commit both files to the repository. GitHub Pages automatically rebuilds and serves the updated files within ~2 minutes of the commit.

**Inputs:** `current_state.json` and `historical_states.json` from DBFS.
**Outputs:** Both files committed to the GitHub repository → GitHub Pages rebuilt → dashboard live.
**Credentials:** GitHub Personal Access Token stored as a Databricks Secret. Never committed to the repository.
**Failure behaviour:** Retries once on HTTP error. Exits with exception on second failure.

### 4.6 GenAI Notebook (Task 6 — Phase 2)

Reads the current gold table record. Constructs a prompt describing the current State, active rules, and key data readings. Calls the Gemini API (`generativelanguage.googleapis.com`). Appends the response as a `summary` string field to `current_state.json` before the Publish step commits it.

**Inputs:** Current record from the gold Delta table; `current_state.json` on DBFS.
**Outputs:** Updated `current_state.json` with `summary` field added.
**Credentials:** Gemini API key stored as a Databricks Secret.
**Failure behaviour:** On API error, skips the summary field gracefully — `current_state.json` is published without a summary rather than blocking the entire job.

### 4.7 Output: current_state.json

The primary output read by the dashboard.

```json
{
  "generated_at": "2026-06-02T08:00:00Z",
  "has_recommendation": true,
  "recommended_state": 1,
  "allocation": { "nifty_etf_pct": 80, "gold_etf_pct": 20 },
  "rules": {
    "R1A": { "status": "clear", "pct_change": 0.0, "threshold": 20.0 },
    "R1B": { "status": "clear", "inr_depreciation_pct": 1.2, "threshold": 3.0 },
    "R2":  { "status": "clear", "real_rate": 0.25, "threshold": 3.0 },
    "R3":  { "status": "yellow", "ratio": 1.31, "trigger_threshold": 1.80, "yellow_threshold": 1.40, "trigger_price_usd": 127.19 },
    "R5":  { "status": "clear", "bs_yoy_pct": 8.3, "threshold": 25.0 },
    "R7":  { "status": "clear", "fii_3m_cumulative": 12400, "outflow_threshold": 8750 }
  },
  "data_freshness": {
    "yfinance_daily":   { "last_date": "2026-05-30", "status": "fresh" },
    "usoil_daily":      { "last_date": "2026-05-30", "status": "fresh" },
    "repo_rate_daily":  { "last_date": "2026-05-30", "status": "fresh" },
    "rbi_wss":          { "last_date": "2026-05-23", "status": "fresh" },
    "cpi_combined":     { "last_date": "2026-04-01", "status": "fresh" },
    "fii_nsdl_monthly": { "last_date": "2026-05-01", "status": "fresh" }
  },
  "quarterly_check": {
    "last_run": "2026-04-01",
    "nifty_6m_return_pct": 12.4,
    "gold_6m_return_pct": 5.1,
    "differential": 7.3,
    "base_state": 1
  },
  "summary": "Markets are in equity-favourable conditions. No macro stress signals are active. Oil prices are elevated but have not reached the trigger threshold. (Phase 2 — Gemini API)"
}
```

When `has_recommendation` is `false`, the JSON contains `error_reason` and `stale_parameters` instead of rule and allocation fields.

### 4.7b Output: historical_states.json

Published alongside `current_state.json`. Contains one record per trading day from January 2020 to the current date. Used exclusively by the browser-side simulation tool — never processed server-side.

```json
{
  "generated_at": "2026-06-02T08:00:00Z",
  "history": [
    {
      "date": "2020-01-02",
      "nifty_price": 12282.2,
      "gold_inr_price": 39480.0,
      "recommended_state": 2,
      "active_rules": []
    },
    ...
  ]
}
```

Estimated file size: ~700 KB for ~1,700 trading days. A browser loads and parses this in under one second.

### 4.8 Public Dashboard (GitHub Pages)

A static HTML/CSS/JS site served from the `docs/dashboard/` folder of the GitHub repository. JavaScript libraries used: Plotly.js (charts), no framework required.

**Section 1 — Current recommendation (reads `current_state.json`):**
- Current recommended State and allocation ratio
- Rule-by-rule readings (current value, threshold, status: clear / yellow / triggered)
- Data freshness timestamp for every parameter
- Plain-language GenAI summary (Phase 2)
- Educational disclaimer

**Section 2 — Historical simulation tool (reads `historical_states.json`, FR-09):**
- User enters: start date, lump sum (₹), monthly SIP (₹)
- JavaScript simulates the portfolio day by day using actual historical prices and States:
  - Start date → lump sum split at the recommended State on that date
  - First of each month → SIP invested at that month's recommended State
  - Each quarter → 75% rebalancing rule applied using actual prices
- Plotly.js renders a line chart of portfolio value over time
- User values are never transmitted or stored — computation is entirely in the browser session

**When `has_recommendation` is `false`:** Section 1 shows a data error banner identifying the stale parameter(s). Section 2 remains available as it uses historical data only.

---

## 5. Data Flow

### 5.1 Monthly Run

```
EventBridge Scheduler fires (1st of month, cron per-source schedules)
  │
  └─ AWS Lambda  {"scraper": "all", "mode": "upsert"}
        yfinance_scraper → s3://.../yfinance_daily/yfinance_daily.csv
        usoil_scraper    → s3://.../usoil_daily/usoil_daily.csv
        rbi_mmo_scraper  → s3://.../repo_rate_daily/repo_rate_daily.csv
        rbi_wss_scraper  → s3://.../rbi_wss/rbi_wss_monthly.csv
        cpi_scraper      → s3://.../cpi_monthly/cpi_combined.csv     (14th of month)
        nsdl_fpi_scraper → s3://.../fii_monthly/fii_nsdl_monthly.csv
  │
  └─ Databricks Job triggers (monthly cron)
        │
        ├─ Task 1: Bronze notebook
        │     reads S3 CSVs → adds metadata → writes Delta to /bronze/
        │
        ├─ Task 2: Silver notebook
        │     reads /bronze/ → cleans + validates → writes Delta to /silver/
        │
        ├─ Task 3: Gold notebook
        │     reads /silver/ → data quality guard → rule evaluation
        │     → writes Delta to /gold/rule_evaluations/ (audit log)
        │     → writes current_state.json to /gold/output/
        │
        ├─ Task 4: Publish notebook
        │     reads /gold/output/current_state.json
        │     → GitHub Contents API → commits file to GitHub repo
        │     → GitHub Pages serves updated dashboard
        │
        └─ Task 5: GenAI notebook (Phase 2)
              reads gold table → Gemini API
              → appends summary → re-commits current_state.json + historical_states.json
```

### 5.2 Manual / Targeted Refresh

When a single data source needs updating outside the normal schedule:

```
Developer invokes Lambda manually (AWS Console → Test, or CLI)
  payload: {"scraper": "rbi_wss", "mode": "upsert"}  ← or full_refresh
  │
  └─ Lambda runs only rbi_wss_scraper → overwrites S3 file
        (all other S3 files untouched)
  │
  └─ Databricks Job triggered manually if pipeline re-run is needed
```

### 5.3 Format at Each Boundary

| Boundary | Format |
|----------|--------|
| Scraper → S3 | CSV files, date column `YYYY-MM-DD`, numeric value columns |
| S3 → Bronze Delta | Delta table, added columns: `ingested_at` (timestamp), `source` (string) |
| Bronze → Silver Delta | Delta table, cleaned types, validated ranges, standardised dates |
| Silver → Gold Delta | Delta table, computed rule metrics, status fields, State determination |
| Gold → JSON | UTF-8 JSON, ISO 8601 timestamps |
| JSON → GitHub API | Base64-encoded file content in JSON request body |
| GitHub → Dashboard | HTTP GET of raw file URL, parsed as JSON by browser JavaScript |

---

## 6. Infrastructure

| Component | Runs on | Cost |
|-----------|---------|------|
| Data collection (scrapers) | AWS Lambda | Free (permanent free tier) |
| Collection scheduling | AWS EventBridge Scheduler | Free (permanent free tier) |
| Raw file storage | Amazon S3 | Free (12-month free tier); <$0.01/month after |
| Bronze / Silver / Gold notebooks | Databricks Community Edition cluster | Free |
| Delta table storage | DBFS (included with Community Edition) | Free |
| Databricks Job scheduling | Databricks Community Edition | Free |
| `current_state.json` + dashboard files | GitHub repository | Free |
| Public dashboard | GitHub Pages | Free |
| GenAI summaries (Phase 2) | Gemini API free tier | Free (within quota) |

**Cluster cold-start:** ~5–10 minutes per monthly run on Community Edition. Acceptable for a monthly signal tool.

**Data volume:** Total S3 raw storage under 5 MB. Total Delta table storage across all layers under 50 MB. Both well within free tier limits.

**Scaling:** No scaling consideration required. Lambda runs at most a handful of times per month. The Databricks pipeline runs once per month. GitHub Pages handles any number of concurrent dashboard readers via CDN.

---

## 7. Security

| Asset | Readable by | Written by | How managed |
|-------|-------------|-----------|-------------|
| Source code | Public (GitHub repo) | Repository owner | GitHub branch protection on `main` |
| S3 raw CSV files | Lambda function, Databricks Bronze notebook | Lambda function | S3 bucket policy — private, no public access |
| DBFS Delta files | Databricks workspace owner only | Databricks Job | Community Edition workspace is single-user |
| `current_state.json` (GitHub) | Public | Databricks Publish notebook | Via GitHub Personal Access Token |
| Dashboard HTML/JS | Public | Repository owner | GitHub branch protection |
| AWS IAM role (Lambda) | Lambda function only | Repository owner | Least-privilege: S3 read/write on raw bucket only |
| GitHub Personal Access Token | Databricks Publish notebook only | Repository owner | Stored as Databricks Secret — never committed |
| Gemini API key (Phase 2) | Databricks GenAI notebook only | Repository owner | Stored as Databricks Secret — never committed |

**No credentials in code or CSV files.** Lambda uses an IAM role (no hardcoded keys). Databricks secrets are accessed via `dbutils.secrets.get()` at runtime.

**No user data.** The dashboard collects nothing from visitors — no cookies, no analytics, no identifiers.

---

## 8. Open Questions Resolved

All open questions from ADR-000 Section 13 are resolved here.

### OQ-03 — What should the dashboard show when a data refresh is in progress?

**Resolved.** The Databricks Job commits `current_state.json` to GitHub at the end of Task 5, after all computation is complete. GitHub Pages serves the last committed file. There is no partial or in-progress state visible to users — the file shows either the previous run's output or the new output after the commit. The data freshness timestamps on the dashboard communicate the age of the current data at all times.

### OQ-04 — What platform hosts the public dashboard?

**Resolved.** GitHub Pages, serving a static HTML/CSS/JS site from the `docs/dashboard/` folder of the repository. Free, no server management, publicly accessible to anyone with the URL, no login required.

---

*This document translates the requirements in ADR-000 into specific technology choices. All subsequent ADRs (001–006) provide detailed justification for the individual decisions made here, including alternatives considered and trade-offs accepted. When this document and ADR-000 disagree, ADR-000 takes priority.*
