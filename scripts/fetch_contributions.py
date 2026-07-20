#!/usr/bin/env python3
"""Fetch a user's public contribution calendar (no token needed) and write
data/contributions.json with raw days plus derived stats.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "bhavik-singh1")
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_days(username: str):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-art/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        date = cell.get("data-date")
        if not date:
            continue
        # Newer GitHub markup stores the count on data-level and in a tooltip.
        level = int(cell.get("data-level", 0))
        count = 0
        # Try to pull the exact number from the aria/tooltip text.
        tip_id = cell.get("aria-labelledby") or cell.get("id")
        text = cell.get("data-count") or ""
        m = re.search(r"(\d[\d,]*)\s+contribution", text)
        if m:
            count = int(m.group(1).replace(",", ""))
        days.append({"date": date, "count": count, "level": level})

    # Tooltips (separate <tool-tip> elements) carry the real counts in modern markup.
    tips = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for", "")
        m = re.search(r"(\d[\d,]*|No)\s+contribution", tip.get_text())
        if target and m:
            raw = m.group(1)
            tips[target] = 0 if raw == "No" else int(raw.replace(",", ""))
    if tips:
        for cell, day in zip(soup.select("td.ContributionCalendar-day"), days):
            cid = cell.get("id")
            if cid in tips:
                day["count"] = tips[cid]

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)
    # Streaks
    cur = longest = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    # Current streak = trailing run of active days
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break
    best = max(days, key=lambda d: d["count"], default={"date": None, "count": 0})
    # Monthly totals
    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    days = fetch_days(username)
    if not days:
        print("No contribution cells found — check the username / markup.", file=sys.stderr)
        sys.exit(1)
    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": compute_stats(days),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT} ({len(days)} days, {payload['stats']['total']} contributions)")


if __name__ == "__main__":
    main()
