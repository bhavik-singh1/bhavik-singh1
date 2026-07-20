#!/usr/bin/env python3
"""Fetch a user's contribution calendar and write data/contributions.json with
raw days plus derived stats.

Primary source: GitHub's GraphQL API, which returns exact per-day counts. It
requires a token — in GitHub Actions the built-in GITHUB_TOKEN works; locally
export GH_TOKEN (a classic/fine-grained PAT with default public scope is fine).

Fallback: scrape the public contributions HTML at
https://github.com/users/<username>/contributions — used only when no token is
available. Counts are read from the modern <tool-tip> elements.
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
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

GRAPHQL = "https://api.github.com/graphql"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

# GraphQL returns a named level; map it to the 0-4 scale the renderer expects.
LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_days_graphql(username: str, token: str):
    resp = requests.post(
        GRAPHQL,
        json={"query": QUERY, "variables": {"login": username}},
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": "profile-art/1.0",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append(
                {
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "level": LEVELS.get(d["contributionLevel"], 0),
                }
            )
    days.sort(key=lambda d: d["date"])
    return days


def fetch_days_html(username: str):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-art/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    days = []
    by_id = {}
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue
        day = {
            "date": date,
            "count": 0,
            "level": int(cell.get("data-level", 0)),
        }
        days.append(day)
        cid = cell.get("id")
        if cid:
            by_id[cid] = day

    # Modern markup: <tool-tip for="<cell id>">N contributions on <date></tool-tip>
    for tip in soup.select("tool-tip"):
        target = tip.get("for", "")
        if target not in by_id:
            continue
        m = re.search(r"(\d[\d,]*|No)\s+contribution", tip.get_text())
        if m:
            raw = m.group(1)
            by_id[target]["count"] = 0 if raw == "No" else int(raw.replace(",", ""))

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break
    best = max(days, key=lambda d: d["count"], default={"date": None, "count": 0})
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
    source = "html"
    if TOKEN:
        try:
            days = fetch_days_graphql(username, TOKEN)
            source = "graphql"
        except Exception as e:  # noqa: BLE001 — fall back to scraping
            print(f"GraphQL fetch failed ({e}); falling back to HTML.", file=sys.stderr)
            days = fetch_days_html(username)
    else:
        print("No GH_TOKEN/GITHUB_TOKEN set; scraping public HTML "
              "(counts may be less reliable).", file=sys.stderr)
        days = fetch_days_html(username)

    if not days:
        print("No contribution cells found — check the username / markup.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "days": days,
        "stats": compute_stats(days),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT} via {source} "
          f"({len(days)} days, {payload['stats']['total']} contributions)")


if __name__ == "__main__":
    main()
