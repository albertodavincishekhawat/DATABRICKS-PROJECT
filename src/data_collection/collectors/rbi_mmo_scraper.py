"""
RBI Money Market Operations (MMO) Scraper

Fetches MSF and SDF rates from RBI's daily Money Market Operations page.
Derives repo rate = (MSF + SDF) / 2 — the RBI corridor is always ±25bps from repo.

Source   : https://www.rbi.org.in/Scripts/BS_ViewMMO.aspx (published every working day)
Output   : src/data_collection/input/repo_rate_daily.csv
Columns  : date (YYYY-MM-DD), msf_rate, sdf_rate, repo_rate
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MMO_URL = "https://www.rbi.org.in/Scripts/BS_ViewMMO.aspx"
OUTPUT_PATH = Path("src/data_collection/input/repo_rate_daily.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.rbi.org.in/",
}


def _extract_rates(soup: BeautifulSoup) -> tuple[float, float] | tuple[None, None]:
    """
    Extract MSF and SDF rates from the MMO page HTML.

    Looks for rows labelled '3. MSF' and '4. SDF' in section C (LAF/MSF/SDF)
    and reads the cut-off rate from the last numeric column.
    """
    msf_rate = None
    sdf_rate = None

    for row in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if not cells:
            continue

        label = cells[0].upper()

        if re.search(r"3\.\s*MSF", label):
            rate = _parse_rate(cells)
            if rate is not None:
                msf_rate = rate

        if re.search(r"4\.\s*SDF", label):
            rate = _parse_rate(cells)
            if rate is not None:
                sdf_rate = rate

    return msf_rate, sdf_rate


def _parse_rate(cells: list[str]) -> float | None:
    """Return first cell that looks like a percentage rate (e.g. 5.50 or 5.50%)."""
    for cell in reversed(cells):
        clean = cell.replace("%", "").strip()
        try:
            value = float(clean)
            if 0.5 <= value <= 20.0:  # sanity: repo rate always in this range
                return value
        except ValueError:
            continue
    return None


def _parse_report_date(soup: BeautifulSoup) -> str | None:
    """Extract the 'as on DATE' date from the page title or header."""
    text = soup.get_text(" ", strip=True)
    match = re.search(r"as on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
    if match:
        raw = match.group(1)
        for fmt in ("%B %d, %Y", "%d %B %Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return datetime.today().strftime("%Y-%m-%d")


def fetch() -> pd.DataFrame | None:
    logger.info("[RepoRate] Fetching RBI Money Market Operations page…")
    try:
        resp = requests.get(MMO_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"[RepoRate] Request failed: {e}")
        return None

    soup = BeautifulSoup(resp.content, "html.parser")
    report_date = _parse_report_date(soup)
    msf_rate, sdf_rate = _extract_rates(soup)

    if msf_rate is None or sdf_rate is None:
        logger.error(f"[RepoRate] Could not extract MSF/SDF rates from page. MSF={msf_rate}, SDF={sdf_rate}")
        return None

    repo_rate = round((msf_rate + sdf_rate) / 2, 2)
    logger.info(f"[RepoRate] Date={report_date}  MSF={msf_rate}%  SDF={sdf_rate}%  → Repo={repo_rate}%")

    return pd.DataFrame([{
        "date": report_date,
        "msf_rate": msf_rate,
        "sdf_rate": sdf_rate,
        "repo_rate": repo_rate,
    }])


def save(df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)
        combined = pd.concat([existing, df]).drop_duplicates(subset=["date"]).sort_values("date")
    else:
        combined = df

    combined.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"[RepoRate] Saved {len(combined)} rows → {OUTPUT_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = fetch()
    if result is not None:
        save(result)
        print(result.to_string(index=False))
    else:
        print("Failed to fetch repo rate.")
