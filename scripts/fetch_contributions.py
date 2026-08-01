#!/usr/bin/env python3
"""Fetch the public contribution calendar — no token needed.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page uses). Parse the day cells and write data/contributions.json
with raw days plus derived stats.
"""
import datetime as dt
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "dhruvrajkotia"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contributions.json"

# fallback when the per-day tooltip is missing: rough midpoint per level
LEVEL_ESTIMATE = {0: 0, 1: 2, 2: 5, 3: 9, 4: 14}


def fetch_days() -> list[dict]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-readme-art"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    counts = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        m = re.match(r"(\d+|No)\b", tip.get_text(strip=True))
        if target and m:
            counts[target] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0))
        count = counts.get(td.get("id"))
        if count is None:
            count = LEVEL_ESTIMATE[level]
        days.append({"date": date, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found — GitHub markup may have changed")
    return days


def derive_stats(days: list[dict]) -> dict:
    streak = longest = current = 0
    # walk oldest -> newest; today with 0 contributions doesn't break the streak
    for day in days:
        if day["count"] > 0:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0
    current = 0
    for day in reversed(days):
        if day["count"] > 0:
            current += 1
        elif day["date"] == dt.date.today().isoformat():
            continue
        else:
            break

    best = max(days, key=lambda d: d["count"])
    monthly: dict[str, int] = {}
    for day in days:
        monthly[day["date"][:7]] = monthly.get(day["date"][:7], 0) + day["count"]
    return {
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main() -> None:
    days = fetch_days()
    payload = {
        "username": USERNAME,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stats": derive_stats(days),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    s = payload["stats"]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(days)} days, "
          f"{s['total']} contributions, streak {s['current_streak']}/{s['longest_streak']}")


if __name__ == "__main__":
    main()
