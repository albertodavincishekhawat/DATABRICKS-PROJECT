"""
RBI Repo Rate Historical Seed — One-time backfill script.

Creates repo_rate_daily.csv with one entry per MPC rate-change event
from Jan 2020 to present. The daily scraper (rbi_mmo_scraper.py) appends
going forward. The collector forward-fills between entries.

Sources and confidence:
  - 2020–2024 rates: match public RBI MPC record; Sep 2024 entry
    confirmed independently via MMO scrape (repo=6.50%)
  - 2025 rates: researched — 125bps cumulative cut Feb–Dec 2025
    confirmed; Oct 2025 hold at 5.50% confirmed via MMO scrape
  - 2026 rates: Apr 2026 hold at 5.25% confirmed; current scrape
    May 2026 confirmed 5.25%
  - MSF = repo + 0.25%, SDF = repo − 0.25% (RBI corridor, fixed)

Run once:
    python3 -m src.data_collection.collectors.rbi_mmo_backfill
"""

from pathlib import Path
import pandas as pd

OUTPUT_PATH = Path("src/data_collection/input/repo_rate_daily.csv")


def build_seed() -> pd.DataFrame:
    # (date, repo_rate, note)
    # Only rate-change events — collector forward-fills between them.
    decisions = [
        # 2020: Pre-COVID rate, then emergency COVID cuts
        ("2020-01-01", 5.15, "historical_seed"),   # start of 2020 (set Dec 2019)
        ("2020-03-27", 4.40, "historical_seed"),   # emergency off-cycle cut (75bps)
        ("2020-05-22", 4.00, "historical_seed"),   # cut (40bps)
        # Held at 4.00% through 2020 and 2021

        # 2022: Hiking cycle begins with off-cycle emergency meeting
        ("2022-05-04", 4.40, "historical_seed"),   # off-cycle hike (40bps)
        ("2022-06-08", 4.90, "historical_seed"),   # hike (50bps)
        ("2022-08-05", 5.40, "historical_seed"),   # hike (50bps)
        ("2022-09-30", 5.90, "historical_seed"),   # hike (50bps)
        ("2022-12-07", 6.25, "historical_seed"),   # hike (35bps)

        # 2023: Final hike, then long hold
        ("2023-02-08", 6.50, "historical_seed"),   # hike (25bps) — peak
        # Held at 6.50% through all of 2023 and 2024
        # Sep 2024 independently confirmed at 6.50% via MMO scrape

        # 2025: Cutting cycle — 5 cuts of 25bps, Oct hold
        # Cumulative 125bps Feb–Dec 2025 confirmed by multiple sources
        ("2025-02-07", 6.25, "historical_seed"),   # cut (25bps)
        ("2025-04-09", 6.00, "historical_seed"),   # cut (25bps)
        ("2025-06-06", 5.75, "historical_seed"),   # cut (25bps)
        ("2025-08-07", 5.50, "historical_seed"),   # cut (25bps)
        # Oct 1 2025: hold at 5.50% — confirmed by MMO scrape (Oct 27: MSF=5.75%, SDF=5.25%)
        ("2025-12-05", 5.25, "historical_seed"),   # cut (25bps)

        # 2026: Holding at 5.25%
        # Feb 6 and Apr 8 holds confirmed; May 2026 scrape confirms 5.25%
    ]

    rows = []
    for date_str, repo_rate, source in decisions:
        rows.append({
            "date": date_str,
            "msf_rate": round(repo_rate + 0.25, 2),
            "sdf_rate": round(repo_rate - 0.25, 2),
            "repo_rate": repo_rate,
            "source": source,
        })

    return pd.DataFrame(rows)


def save(seed_df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)
        # Merge: seed fills history, existing scraped data takes precedence
        combined = (
            pd.concat([seed_df, existing])
            .drop_duplicates(subset=["date"], keep="last")
            .sort_values("date")
            .reset_index(drop=True)
        )
    else:
        combined = seed_df.sort_values("date").reset_index(drop=True)

    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(combined)} rows → {OUTPUT_PATH}")
    print(combined.to_string(index=False))


if __name__ == "__main__":
    seed = build_seed()
    save(seed)
