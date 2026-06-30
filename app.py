from __future__ import annotations

import csv
import io
import json
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, Response, abort, jsonify, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
# Single source of truth for the database location. Everything that touches the
# DB derives from DB_PATH; set DB_DIR (e.g. a mounted Render disk like /var/data)
# to relocate it. Do not hardcode the path anywhere else.
DB_DIR = Path(os.getenv("DB_DIR", str(BASE_DIR / "data")))
DB_PATH = DB_DIR / "predictions.db"
ALLOWED_EMAILS_PATH = Path(os.getenv("ALLOWED_EMAILS_PATH", str(BASE_DIR / "allowed_emails.txt")))

ACCESS_DENIED_MESSAGE = (
    "User not found - Please send the 5€ Bizum to be able to participate "
    "in the prediction contest!"
)

# 12:00 noon Madrid time on 11 June 2026 (CEST = UTC+2)
PICKS_LOCK_AT = os.getenv("PICKS_LOCK_AT", "2026-06-11T10:00:00+00:00").strip()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-before-deploying")

ROUND_POINTS: dict[str, int] = {"r32": 3, "r16": 5, "qf": 8, "sf": 12, "f": 20}
SCORE_BONUS: dict[str, int] = {"r32": 5, "r16": 5, "qf": 5, "sf": 5, "f": 5}
MAX_MATCH_SCORE = 30
KO_ROUND_IDS = ("r32", "r16", "qf", "sf", "f")
GROUP_LETTERS = tuple("ABCDEFGHIJKL")

# Per-match kickoff times in UTC. Indexed in bracket-tree order so they line up
# with the R32/R16_PAIRS/QF_PAIRS/SF_PAIRS/F_PAIRS structure in static/app.js.
# Used to enforce the per-match 30-minute lock server-side.
KO_KICKOFFS: dict[str, tuple[str, ...]] = {
    "r32": (
        "2026-06-29T20:30:00+00:00",  # M74
        "2026-06-30T21:00:00+00:00",  # M77
        "2026-06-28T19:00:00+00:00",  # M73
        "2026-06-30T01:00:00+00:00",  # M75
        "2026-07-02T23:00:00+00:00",  # M83
        "2026-07-02T19:00:00+00:00",  # M84
        "2026-07-02T00:00:00+00:00",  # M81
        "2026-07-01T20:00:00+00:00",  # M82
        "2026-06-29T17:00:00+00:00",  # M76
        "2026-06-30T17:00:00+00:00",  # M78
        "2026-07-01T01:00:00+00:00",  # M79
        "2026-07-01T16:00:00+00:00",  # M80
        "2026-07-03T22:00:00+00:00",  # M86
        "2026-07-03T18:00:00+00:00",  # M88
        "2026-07-03T03:00:00+00:00",  # M85
        "2026-07-04T01:30:00+00:00",  # M87
    ),
    "r16": (
        "2026-07-04T21:00:00+00:00",  # M89
        "2026-07-04T17:00:00+00:00",  # M90
        "2026-07-06T19:00:00+00:00",  # M93
        "2026-07-07T00:00:00+00:00",  # M94
        "2026-07-05T20:00:00+00:00",  # M91
        "2026-07-06T00:00:00+00:00",  # M92
        "2026-07-07T16:00:00+00:00",  # M95
        "2026-07-07T20:00:00+00:00",  # M96
    ),
    "qf": (
        "2026-07-09T20:00:00+00:00",  # M97
        "2026-07-10T19:00:00+00:00",  # M98
        "2026-07-11T21:00:00+00:00",  # M99
        "2026-07-12T01:00:00+00:00",  # M100
    ),
    "sf": (
        "2026-07-14T19:00:00+00:00",  # M101
        "2026-07-15T19:00:00+00:00",  # M102
    ),
    "f": (
        "2026-07-19T19:00:00+00:00",  # M104
    ),
}

# Picks for a knockout match lock this many minutes before kickoff.
KO_LOCK_MINUTES_BEFORE = 30
# In addition, all knockout picks lock no later than this ceiling:
# 19:20 Madrid / CEST on 30 June 2026 (17:20 UTC).
KO_LOCK_CEILING_AT = os.getenv("KO_LOCK_CEILING_AT", "2026-06-30T19:20:00+02:00").strip()

RESULTS_KEY = "wc2026_results"

FOOTBALL_DATA_BASE = os.getenv("FOOTBALL_DATA_BASE", "https://api.football-data.org/v4").rstrip("/")
FOOTBALL_DATA_COMPETITION = os.getenv("FOOTBALL_DATA_COMPETITION", "WC")
FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN", "").strip()
SPORTSDB_BASE = os.getenv("SPORTSDB_BASE", "https://www.thesportsdb.com/api/v1/json/3").rstrip("/")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "12"))
# Corporate networks often intercept TLS with a private CA — set HTTP_VERIFY_SSL=false
# to skip verification when fetching the public sports APIs.
HTTP_VERIFY_SSL = os.getenv("HTTP_VERIFY_SSL", "true").strip().lower() not in {"0", "false", "no"}

try:
    import truststore  # type: ignore[import-not-found]
    truststore.inject_into_ssl()
except ImportError:
    pass

if not HTTP_VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db_connection() as conn:
        existing = [
            r[1]
            for r in conn.execute("PRAGMA table_info(submissions)").fetchall()
        ]
        if existing and "email" not in existing:
            conn.execute("ALTER TABLE submissions RENAME TO submissions_v1_backup")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                email      TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                picks_json TEXT NOT NULL,
                score      INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email))


def load_allowed_emails() -> set[str]:
    emails: set[str] = set()

    def _ingest(text: str) -> None:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for token in line.split(","):
                token = token.strip().lower()
                if token:
                    emails.add(token)

    env_value = os.getenv("ALLOWED_EMAILS", "").strip()
    if env_value:
        _ingest(env_value)
        return emails

    try:
        _ingest(ALLOWED_EMAILS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pass
    return emails


def picks_lock_dt() -> datetime | None:
    try:
        dt = datetime.fromisoformat(PICKS_LOCK_AT)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def picks_locked(now: datetime | None = None) -> bool:
    dt = picks_lock_dt()
    if dt is None:
        return False
    return (now or datetime.now(timezone.utc)) >= dt


def ko_match_kickoff(round_id: str, match_idx: int) -> datetime | None:
    kickoffs = KO_KICKOFFS.get(round_id)
    if not kickoffs or match_idx < 0 or match_idx >= len(kickoffs):
        return None
    try:
        dt = datetime.fromisoformat(kickoffs[match_idx])
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ko_lock_ceiling_dt() -> datetime | None:
    try:
        dt = datetime.fromisoformat(KO_LOCK_CEILING_AT)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ko_match_is_closed(round_id: str, match_idx: int, now: datetime | None = None) -> bool:
    """True when picks for this match are no longer accepted.

    Picks lock 30 minutes before kickoff, but never later than the global
    ceiling (KO_LOCK_CEILING_AT), whichever comes first.
    """
    now = now or datetime.now(timezone.utc)
    ceiling = ko_lock_ceiling_dt()
    if ceiling is not None and now >= ceiling:
        return True
    kickoff = ko_match_kickoff(round_id, match_idx)
    if kickoff is None:
        return False
    lock_at = kickoff - timedelta(minutes=KO_LOCK_MINUTES_BEFORE)
    return now >= lock_at


def is_email_allowed(email: str) -> bool:
    allowed = load_allowed_emails()
    # If no allowlist is configured, fall back to letting everyone in so a
    # missing file can't accidentally lock all users out.
    if not allowed:
        return True
    return email.strip().lower() in allowed


def is_valid_match_score(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= MAX_MATCH_SCORE
    )


def get_admin_password() -> str | None:
    pw = os.getenv("ADMIN_PASSWORD", "").strip()
    return pw or None


def admin_is_authenticated() -> bool:
    return bool(session.get("is_admin"))


def require_admin() -> None:
    if not admin_is_authenticated():
        abort(401)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ─── Results storage ──────────────────────────────────────────────────────────

def get_setting(key: str) -> tuple[str | None, str | None]:
    with db_connection() as conn:
        row = conn.execute(
            "SELECT value, updated_at FROM settings WHERE key = ?", (key,)
        ).fetchone()
    if row is None:
        return None, None
    return row["value"], row["updated_at"]


def set_setting(key: str, value: str) -> str:
    timestamp = utc_now_iso()
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, timestamp),
        )
    return timestamp


def get_results() -> dict:
    raw, _ = get_setting(RESULTS_KEY)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_results_meta() -> dict:
    raw, updated_at = get_setting(RESULTS_KEY)
    results = {}
    if raw:
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            parsed = None
        if isinstance(parsed, dict):
            results = parsed
    return {
        "results": results,
        "updated_at": updated_at,
        "has_results": bool(results),
    }


def save_results(results: dict) -> str:
    if not isinstance(results, dict):
        raise ValueError("results must be a JSON object")
    return set_setting(RESULTS_KEY, json.dumps(results))


def recalculate_all_scores() -> int:
    results = get_results()
    affected = 0
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT email, picks_json FROM submissions"
        ).fetchall()
        for row in rows:
            try:
                picks = json.loads(row["picks_json"])
            except (TypeError, ValueError):
                picks = {}
            new_score = calculate_score(picks, results)
            conn.execute(
                "UPDATE submissions SET score = ? WHERE email = ?",
                (new_score, row["email"]),
            )
            affected += 1
    return affected


# ─── Scoring ──────────────────────────────────────────────────────────────────

def calculate_score(picks: dict[str, Any], results: dict | None = None) -> int:
    """Score user picks against verified actual results.

    Returns 0 until the admin records real results — completeness alone is
    never worth points.
    """
    if not results or not isinstance(results, dict):
        return 0
    if not isinstance(picks, dict):
        return 0

    score = 0
    score += _score_groups(picks.get("groups"), results.get("groups"))
    score += _score_thirds(picks.get("thirds_ranking"), results.get("thirds_advancing"))
    score += _score_ko(picks.get("ko"), results.get("ko"))
    score += _score_podium(_picks_podium(picks), results.get("podium"))
    score += _score_pichichi(picks.get("pichichi"), results.get("pichichi"))
    return score


def _score_pichichi(user: Any, actual: Any) -> int:
    if not isinstance(user, str) or not user:
        return 0
    if not isinstance(actual, str) or not actual:
        return 0
    return PICHICHI_POINTS if user == actual else 0


# Tournament podium scoring (champion / runner-up / 3rd-place playoff winner / loser)
# Points follow the teams' actual finishing slots; users do not lose those
# points just because they put the top-four teams in a different order.
PODIUM_POINTS = {"first": 10, "second": 6, "third": 4, "fourth": 3}
PICHICHI_POINTS = 5


def _picks_podium(picks: dict[str, Any]) -> dict[str, Any]:
    """Read picks.podium; fall back to legacy top-level picks.champion."""
    podium = picks.get("podium")
    if isinstance(podium, dict):
        return podium
    champ = picks.get("champion")
    return {"first": champ} if isinstance(champ, str) and champ else {}


def _score_podium(user: Any, actual: Any) -> int:
    if not isinstance(user, dict) or not isinstance(actual, dict):
        return 0
    predicted_top_four = {
        team
        for team in user.values()
        if isinstance(team, str) and team
    }
    if not predicted_top_four:
        return 0

    score = 0
    for slot, pts in PODIUM_POINTS.items():
        a = actual.get(slot)
        if isinstance(a, str) and a in predicted_top_four:
            score += pts
    return score


def _score_groups(user: Any, actual: Any) -> int:
    if not isinstance(user, dict) or not isinstance(actual, dict):
        return 0
    score = 0
    for group, real in actual.items():
        if not isinstance(real, dict):
            continue
        u = user.get(group)
        if not isinstance(u, dict):
            continue
        if real.get("first") and u.get("first") == real.get("first"):
            score += 3
        if real.get("second") and u.get("second") == real.get("second"):
            score += 2
        if real.get("third") and u.get("third") == real.get("third"):
            score += 1
    return score


def _score_thirds(user: Any, actual: Any) -> int:
    if not isinstance(user, list) or not isinstance(actual, list):
        return 0
    advanced = {t for t in actual if isinstance(t, str) and t}
    if not advanced:
        return 0
    score = 0
    for i, team in enumerate(user[:8]):
        if not isinstance(team, str) or not team:
            continue
        if team in advanced:
            score += 1
            if i < len(actual) and actual[i] == team:
                score += 1
    return score


def _infer_ko_winner(pick: Any, actual_entry: Any) -> str | None:
    """Winner implied by the entered score, using the actual match teams.

    When a respondent gave a score but did not pick a team, the higher-scoring
    side wins. A tie, an incomplete/invalid score, or missing actual teams
    yields None. The actual results provide the team names, so individual
    bracket predictions are not used here.
    """
    if not isinstance(pick, dict) or not isinstance(actual_entry, dict):
        return None
    hs, as_ = pick.get("homeScore"), pick.get("awayScore")
    if not (is_valid_match_score(hs) and is_valid_match_score(as_)) or hs == as_:
        return None
    team = actual_entry.get("homeTeam") if hs > as_ else actual_entry.get("awayTeam")
    return team if isinstance(team, str) and team else None


def _score_ko(user: Any, actual: Any) -> int:
    if not isinstance(user, dict) or not isinstance(actual, dict):
        return 0

    score = 0
    for round_id in KO_ROUND_IDS:
        user_round = user.get(round_id)
        actual_round = actual.get(round_id)
        if not isinstance(user_round, dict) or not isinstance(actual_round, dict):
            continue

        actual_winners: set[str] = set()
        actual_scores: dict[str, list[tuple[int, int]]] = {}
        for entry in actual_round.values():
            if not isinstance(entry, dict):
                continue
            winner = entry.get("winner")
            if not isinstance(winner, str) or not winner:
                continue
            actual_winners.add(winner)
            if is_valid_match_score(entry.get("homeScore")) and is_valid_match_score(entry.get("awayScore")):
                actual_scores.setdefault(winner, []).append(
                    (entry["homeScore"], entry["awayScore"])
                )

        pts = ROUND_POINTS[round_id]
        bonus = SCORE_BONUS[round_id]

        for key, pick in user_round.items():
            if not isinstance(pick, dict):
                continue
            picked = pick.get("winner")
            if not (isinstance(picked, str) and picked):
                # No team selected: infer the winner from the entered score
                # using the actual match teams (higher score wins; tie = none).
                picked = _infer_ko_winner(pick, actual_round.get(key))
            if not (isinstance(picked, str) and picked):
                continue
            if picked not in actual_winners:
                continue
            score += pts
            if (
                is_valid_match_score(pick.get("homeScore"))
                and is_valid_match_score(pick.get("awayScore"))
            ):
                wanted = (pick["homeScore"], pick["awayScore"])
                if wanted in actual_scores.get(picked, []):
                    score += bonus

    return score


# ─── External APIs ────────────────────────────────────────────────────────────

FOOTBALL_DATA_STAGE_MAP = {
    "GROUP_STAGE": "group",
    "PLAYOFFS_ROUND_OF_32": "r32",
    "ROUND_OF_32": "r32",
    "LAST_32": "r32",
    "LAST_16": "r16",
    "ROUND_OF_16": "r16",
    "QUARTER_FINALS": "qf",
    "QUARTER_FINAL": "qf",
    "SEMI_FINALS": "sf",
    "SEMI_FINAL": "sf",
    "FINAL": "f",
}


def fetch_football_data_matches() -> list[dict]:
    if not FOOTBALL_DATA_TOKEN:
        raise RuntimeError(
            "FOOTBALL_DATA_TOKEN environment variable is not set. "
            "Get a free token at football-data.org and configure it to enable automatic refresh."
        )
    url = f"{FOOTBALL_DATA_BASE}/competitions/{FOOTBALL_DATA_COMPETITION}/matches"
    resp = requests.get(
        url,
        headers={"X-Auth-Token": FOOTBALL_DATA_TOKEN},
        timeout=HTTP_TIMEOUT,
        verify=HTTP_VERIFY_SSL,
    )
    resp.raise_for_status()
    payload = resp.json()
    matches = payload.get("matches", [])
    if not isinstance(matches, list):
        return []
    return matches


def _safe_score(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_MATCH_SCORE:
        return value
    return None


def _decide_winner(match: dict) -> str | None:
    score = match.get("score") or {}
    winner_flag = score.get("winner")
    home = ((match.get("homeTeam") or {}).get("name") or "").strip()
    away = ((match.get("awayTeam") or {}).get("name") or "").strip()
    if winner_flag == "HOME_TEAM":
        return home or None
    if winner_flag == "AWAY_TEAM":
        return away or None
    return None


def _known_team_name(team: Any) -> str | None:
    if not isinstance(team, dict):
        return None
    name = (team.get("name") or "").strip()
    if not name or name.lower() in {"tbd", "to be determined", "unknown"}:
        return None
    return name


def _match_utc_timestamp(match: dict) -> float | None:
    value = match.get("utcDate")
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _ko_index_for_match(round_id: str, match: dict, counters: dict[str, int]) -> int:
    match_ts = _match_utc_timestamp(match)
    kickoffs = KO_KICKOFFS.get(round_id) or ()
    if match_ts is not None:
        for idx, kickoff in enumerate(kickoffs):
            try:
                kickoff_ts = datetime.fromisoformat(kickoff).timestamp()
            except ValueError:
                continue
            if abs(match_ts - kickoff_ts) < 60:
                counters[round_id] = max(counters[round_id], idx + 1)
                return idx

    idx = counters[round_id]
    counters[round_id] += 1
    return idx


def parse_football_data_results(matches: list[dict]) -> dict:
    groups: dict[str, dict[str, dict[str, int]]] = {}
    ko: dict[str, dict[str, dict[str, Any]]] = {r: {} for r in KO_ROUND_IDS}

    ko_counters = {r: 0 for r in KO_ROUND_IDS}

    for match in matches:
        stage = (match.get("stage") or "").upper()
        bucket = FOOTBALL_DATA_STAGE_MAP.get(stage)
        if bucket is None:
            continue

        home_name = _known_team_name(match.get("homeTeam"))
        away_name = _known_team_name(match.get("awayTeam"))
        full_time = (match.get("score") or {}).get("fullTime") or {}
        home_score = _safe_score(full_time.get("home"))
        away_score = _safe_score(full_time.get("away"))

        if bucket == "group":
            if match.get("status") != "FINISHED":
                continue
            group_letter = (match.get("group") or "").replace("GROUP_", "").strip().upper()
            if not group_letter or home_name is None or away_name is None or home_score is None or away_score is None:
                continue
            tbl = groups.setdefault(group_letter, {})
            for team in (home_name, away_name):
                tbl.setdefault(team, {"pts": 0, "gf": 0, "ga": 0, "gd": 0, "name": team})
            tbl[home_name]["gf"] += home_score
            tbl[home_name]["ga"] += away_score
            tbl[away_name]["gf"] += away_score
            tbl[away_name]["ga"] += home_score
            if home_score > away_score:
                tbl[home_name]["pts"] += 3
            elif home_score < away_score:
                tbl[away_name]["pts"] += 3
            else:
                tbl[home_name]["pts"] += 1
                tbl[away_name]["pts"] += 1
        else:
            if home_name is None and away_name is None and match.get("status") != "FINISHED":
                continue
            idx = _ko_index_for_match(bucket, match, ko_counters)
            entry: dict[str, Any] = {}
            if home_name is not None:
                entry["homeTeam"] = home_name
            if away_name is not None:
                entry["awayTeam"] = away_name
            winner = _decide_winner(match)
            if winner is not None:
                entry["winner"] = winner
            if home_score is not None and away_score is not None:
                entry["homeScore"] = home_score
                entry["awayScore"] = away_score
            if entry:
                ko[bucket][str(idx)] = entry

    standings: dict[str, dict[str, str]] = {}
    third_pool: list[tuple[int, int, int, str, str]] = []
    for letter, tbl in groups.items():
        ranked = sorted(
            tbl.values(),
            key=lambda t: (t["pts"], (t["gf"] - t["ga"]), t["gf"]),
            reverse=True,
        )
        slot: dict[str, str] = {}
        if len(ranked) >= 1:
            slot["first"] = ranked[0]["name"]
        if len(ranked) >= 2:
            slot["second"] = ranked[1]["name"]
        if len(ranked) >= 3:
            slot["third"] = ranked[2]["name"]
            third_pool.append(
                (ranked[2]["pts"], ranked[2]["gf"] - ranked[2]["ga"], ranked[2]["gf"], letter, ranked[2]["name"])
            )
        standings[letter] = slot

    third_pool.sort(reverse=True)
    thirds_advancing = [name for *_rest, name in third_pool[:8]]

    out: dict[str, Any] = {"groups": standings, "thirds_advancing": thirds_advancing, "ko": ko}
    return out


# FIFA-style names → names indexed by TheSportsDB for the corresponding national team.
COUNTRY_API_NAMES = {
    "USA": "United States",
    "Türkiye": "Turkey",
    "Curaçao": "Curacao",
    "Cabo Verde": "Cape Verde",
    "Bosnia & Herz.": "Bosnia and Herzegovina",
    "DR Congo": "DR Congo",
    "South Korea": "South Korea",
    "Czechia": "Czech Republic",
    "Ivory Coast": "Ivory Coast",
}

# Strings that strongly suggest a strLeague belongs to a national-team competition.
_NATIONAL_LEAGUE_HINTS = (
    "international", "friendly", "friendlies", "world", "uefa nations",
    "nations league", "euro", "copa", "africa", "asia", "concacaf",
    "qualif", "afcon", "afc ", "caf ", "fifa",
)

# Strings that strongly suggest a strLeague belongs to a CLUB competition.
_CLUB_LEAGUE_HINTS = (
    "premier league", "championship", "la liga", "serie a", "bundesliga",
    "ligue 1", "eredivisie", "primeira liga", "saudi pro", "j1", "j2",
    "mls", "liga mx", "champions league", "europa league",
)

# Strings that flag an event as a non-official friendly.
_FRIENDLY_LEAGUE_HINTS = (
    "friendly", "friendlies", "exhibition", "club friendly",
    "international friendly", "international friendlies",
)


def _is_friendly_event(event: dict) -> bool:
    league = (event.get("strLeague") or "").lower()
    return any(hint in league for hint in _FRIENDLY_LEAGUE_HINTS)


def _pick_official_event(events: list) -> dict | None:
    for event in events:
        if isinstance(event, dict) and not _is_friendly_event(event):
            return event
    return None


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _looks_like_national_team(team: dict, target_norm: str) -> bool:
    team_norm = _normalize_name(team.get("strTeam"))
    if team_norm != target_norm:
        return False
    league = (team.get("strLeague") or "").lower()
    if not league:
        return True
    if any(hint in league for hint in _CLUB_LEAGUE_HINTS):
        return False
    if any(hint in league for hint in _NATIONAL_LEAGUE_HINTS):
        return True
    # Empty-ish league with a matching name is likely a national team.
    return league.strip() in {"", "no league", "international"}


def _pick_national_team(teams: list, target_norm: str) -> dict | None:
    soccer = [t for t in teams if isinstance(t, dict) and (t.get("strSport") or "").lower() == "soccer"]
    if not soccer:
        return None
    # 1) Exact-name match that smells like a national team.
    for team in soccer:
        if _looks_like_national_team(team, target_norm):
            return team
    # 2) Exact-name match with an empty league.
    for team in soccer:
        if _normalize_name(team.get("strTeam")) == target_norm and not (team.get("strLeague") or "").strip():
            return team
    # 3) Any exact-name match (better than nothing — caller may show whatever it returns).
    for team in soccer:
        if _normalize_name(team.get("strTeam")) == target_norm:
            return team
    return None


def fetch_team_last_match(team_name: str) -> dict | None:
    """Return the most recent match for a national team via TheSportsDB."""
    raw = (team_name or "").strip()
    if not raw:
        return None
    search_term = COUNTRY_API_NAMES.get(raw, raw)
    target_norm = _normalize_name(search_term)

    search = requests.get(
        f"{SPORTSDB_BASE}/searchteams.php",
        params={"t": search_term},
        timeout=HTTP_TIMEOUT,
        verify=HTTP_VERIFY_SSL,
    )
    search.raise_for_status()
    teams = (search.json() or {}).get("teams") or []
    chosen = _pick_national_team(teams, target_norm)

    # Fallback: try the FIFA-style name itself if the normalized lookup found nothing.
    if chosen is None and search_term.lower() != raw.lower():
        search = requests.get(
            f"{SPORTSDB_BASE}/searchteams.php",
            params={"t": raw},
            timeout=HTTP_TIMEOUT,
            verify=HTTP_VERIFY_SSL,
        )
        search.raise_for_status()
        teams = (search.json() or {}).get("teams") or []
        chosen = _pick_national_team(teams, _normalize_name(raw))

    if chosen is None:
        return None

    team_id = chosen.get("idTeam")
    if not team_id:
        return None

    events: list[dict] = []
    try:
        last = requests.get(
            f"{SPORTSDB_BASE}/eventslast.php",
            params={"id": team_id},
            timeout=HTTP_TIMEOUT,
            verify=HTTP_VERIFY_SSL,
        )
        last.raise_for_status()
        raw_events = (last.json() or {}).get("results") or []
        events.extend(e for e in raw_events if isinstance(e, dict))
    except requests.RequestException:
        events = []

    # Walk prior seasons until we find an official (non-friendly) match.
    # eventsseason.php is paid-tier on TheSportsDB — failures are swallowed.
    if not _pick_official_event(events):
        current_year = datetime.now(timezone.utc).year
        for offset in range(0, 8):
            season = f"{current_year - offset - 1}-{current_year - offset}"
            try:
                resp = requests.get(
                    f"{SPORTSDB_BASE}/eventsseason.php",
                    params={"id": team_id, "s": season},
                    timeout=HTTP_TIMEOUT,
                    verify=HTTP_VERIFY_SSL,
                )
                resp.raise_for_status()
                season_events = (resp.json() or {}).get("events") or []
            except requests.RequestException:
                break
            if not season_events:
                continue
            valid = [e for e in season_events if isinstance(e, dict) and (e.get("strStatus") or "").lower() in {"match finished", "ft", ""}]
            valid.sort(key=lambda e: (e.get("dateEvent") or ""), reverse=True)
            events.extend(valid)
            if _pick_official_event(events):
                break

    event = _pick_official_event(events) or (events[0] if events else None)
    if not isinstance(event, dict):
        return None
    return {
        "home": event.get("strHomeTeam"),
        "away": event.get("strAwayTeam"),
        "homeScore": event.get("intHomeScore"),
        "awayScore": event.get("intAwayScore"),
        "league": event.get("strLeague"),
        "date": event.get("dateEvent"),
        "time": event.get("strTime"),
        "venue": event.get("strVenue"),
        "season": event.get("strSeason"),
        "thumb": event.get("strThumb"),
        "team_resolved": chosen.get("strTeam"),
    }


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def index() -> str:
    return render_template("index.html", picks_lock_at=PICKS_LOCK_AT)


@app.get("/health")
def healthcheck():
    return jsonify({"ok": True})


@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard() -> str:
    configured_password = get_admin_password()
    auth_error = None

    if configured_password is None:
        auth_error = "Set the ADMIN_PASSWORD environment variable to use the admin page."
    elif request.method == "POST" and not admin_is_authenticated():
        if str(request.form.get("password", "")) == configured_password:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        auth_error = "Incorrect password."

    if not admin_is_authenticated():
        return render_template(
            "admin.html",
            is_authenticated=False,
            error=auth_error,
            submissions=[],
            results_meta={"has_results": False, "updated_at": None, "results": {}},
            results_json="",
            football_data_token_configured=bool(FOOTBALL_DATA_TOKEN),
        )

    with db_connection() as conn:
        rows = conn.execute(
            "SELECT email, name, picks_json, score, updated_at FROM submissions "
            "ORDER BY score DESC, updated_at ASC"
        ).fetchall()

    submissions = [
        {
            "email": r["email"],
            "name": r["name"],
            "score": r["score"],
            "updated_at": r["updated_at"],
            "picks": json.loads(r["picks_json"]),
        }
        for r in rows
    ]
    meta = get_results_meta()
    return render_template(
        "admin.html",
        is_authenticated=True,
        error=None,
        submissions=submissions,
        results_meta=meta,
        results_json=json.dumps(meta["results"], indent=2) if meta["results"] else "",
        football_data_token_configured=bool(FOOTBALL_DATA_TOKEN),
    )


@app.post("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_dashboard"))


KO_EXPORT_COUNTS = (("r32", 16), ("r16", 8), ("qf", 4), ("sf", 2), ("f", 1))


def _build_submissions_csv() -> str:
    header: list[str] = ["email", "name", "score", "updated_at"]
    for slot in ("first", "second", "third", "fourth"):
        header.append(f"podium_{slot}")
    header.append("pichichi")
    for letter in GROUP_LETTERS:
        for pos in ("first", "second", "third"):
            header.append(f"group_{letter}_{pos}")
    for i in range(1, 13):
        header.append(f"thirds_rank_{i}")
    for round_id, count in KO_EXPORT_COUNTS:
        for i in range(count):
            header.append(f"{round_id}_M{i + 1}_winner")
            header.append(f"{round_id}_M{i + 1}_score")

    with db_connection() as conn:
        rows = conn.execute(
            "SELECT email, name, picks_json, score, updated_at FROM submissions "
            "ORDER BY score DESC, updated_at ASC"
        ).fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)

    results = get_results()
    actual_ko = results.get("ko") if isinstance(results.get("ko"), dict) else {}

    for row in rows:
        try:
            picks = json.loads(row["picks_json"])
        except (TypeError, ValueError):
            picks = {}
        if not isinstance(picks, dict):
            picks = {}

        out = [row["email"], row["name"], row["score"], row["updated_at"]]

        podium = picks.get("podium") if isinstance(picks.get("podium"), dict) else {}
        for slot in ("first", "second", "third", "fourth"):
            out.append(podium.get(slot) or "")
        pichichi = picks.get("pichichi") if isinstance(picks.get("pichichi"), str) else ""
        out.append(pichichi or "")

        groups = picks.get("groups") if isinstance(picks.get("groups"), dict) else {}
        for letter in GROUP_LETTERS:
            gp = groups.get(letter) if isinstance(groups.get(letter), dict) else {}
            for pos in ("first", "second", "third"):
                out.append(gp.get(pos) or "")

        thirds = picks.get("thirds_ranking") if isinstance(picks.get("thirds_ranking"), list) else []
        for i in range(12):
            out.append(thirds[i] if i < len(thirds) and isinstance(thirds[i], str) else "")

        ko = picks.get("ko") if isinstance(picks.get("ko"), dict) else {}
        for round_id, count in KO_EXPORT_COUNTS:
            round_data = ko.get(round_id) if isinstance(ko.get(round_id), dict) else {}
            actual_round = actual_ko.get(round_id) if isinstance(actual_ko.get(round_id), dict) else {}
            for i in range(count):
                match = round_data.get(str(i))
                if not isinstance(match, dict):
                    match = round_data.get(i) if isinstance(round_data.get(i), dict) else {}
                winner = match.get("winner")
                if not (isinstance(winner, str) and winner):
                    actual_entry = actual_round.get(str(i)) or actual_round.get(i)
                    winner = _infer_ko_winner(match, actual_entry)
                out.append(winner or "")
                hs = match.get("homeScore")
                aw = match.get("awayScore")
                if is_valid_match_score(hs) and is_valid_match_score(aw):
                    out.append(f"{hs}-{aw}")
                else:
                    out.append("")

        writer.writerow(out)

    return buf.getvalue()


@app.get("/admin/export.csv")
def admin_export_csv():
    require_admin()
    payload = _build_submissions_csv()
    return Response(
        payload,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="wc2026-submissions.csv"'},
    )


@app.get("/api/picks/<string:email>")
def get_picks(email: str):
    email = email.strip().lower()
    if not email:
        return jsonify({"ok": False, "error": "Email required."}), 400

    if not is_email_allowed(email):
        return jsonify({"ok": False, "error": ACCESS_DENIED_MESSAGE}), 403

    with db_connection() as conn:
        row = conn.execute(
            "SELECT name, picks_json FROM submissions WHERE email = ?", (email,)
        ).fetchone()

    if row is None:
        return jsonify({"ok": True, "picks": None, "name": None})
    return jsonify({"ok": True, "picks": json.loads(row["picks_json"]), "name": row["name"]})


@app.get("/api/leaderboard")
def get_leaderboard():
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT email, name, score, updated_at FROM submissions "
            "ORDER BY score DESC, updated_at ASC"
        ).fetchall()
    return jsonify(
        {
            "ok": True,
            "entries": [
                {
                    "email": r["email"],
                    "name": r["name"],
                    "score": r["score"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ],
        }
    )


@app.post("/api/save")
def save_picks():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    name = str(payload.get("name", "")).strip()
    picks = payload.get("picks")

    if not email or not validate_email(email):
        return jsonify({"ok": False, "error": "A valid email address is required."}), 400
    if not is_email_allowed(email):
        return jsonify({"ok": False, "error": ACCESS_DENIED_MESSAGE}), 403
    if not name:
        return jsonify({"ok": False, "error": "Name is required."}), 400
    if len(name) > 50:
        return jsonify({"ok": False, "error": "Name must be 50 characters or fewer."}), 400
    if not isinstance(picks, dict):
        return jsonify({"ok": False, "error": "Invalid picks payload."}), 400

    # Load the player's previous submission once so we can fall back to it for
    # any field that's locked (globally or per-match within 30 min of kickoff).
    stored: dict = {}
    with db_connection() as conn:
        row = conn.execute(
            "SELECT picks_json FROM submissions WHERE email = ?", (email,)
        ).fetchone()
    if row:
        try:
            existing = json.loads(row["picks_json"])
        except (TypeError, ValueError):
            existing = {}
        if isinstance(existing, dict):
            stored = existing

    locked = picks_locked()
    if locked:
        stored_groups = stored.get("groups") if isinstance(stored.get("groups"), dict) else {}
        stored_thirds = stored.get("thirds_ranking") if isinstance(stored.get("thirds_ranking"), list) else []
        picks["groups"] = stored_groups
        picks["thirds_ranking"] = stored_thirds

    # Pre-tournament predictions (podium / pichichi / champion) are locked: always
    # keep whatever was previously stored and ignore any incoming changes.
    picks["podium"] = stored.get("podium") if isinstance(stored.get("podium"), dict) else {}
    picks["pichichi"] = stored.get("pichichi") if isinstance(stored.get("pichichi"), str) else ""
    if isinstance(stored.get("champion"), str):
        picks["champion"] = stored["champion"]
    else:
        picks.pop("champion", None)

    # Per-match KO lock: once a knockout match is within 30 minutes of kickoff,
    # ignore any incoming changes for that slot and keep whatever was last stored.
    incoming_ko = picks.get("ko") if isinstance(picks.get("ko"), dict) else {}
    stored_ko = stored.get("ko") if isinstance(stored.get("ko"), dict) else {}
    merged_ko: dict[str, dict] = {}
    for round_id in KO_ROUND_IDS:
        incoming_round = incoming_ko.get(round_id) if isinstance(incoming_ko.get(round_id), dict) else {}
        stored_round = stored_ko.get(round_id) if isinstance(stored_ko.get(round_id), dict) else {}
        round_out: dict = {}
        match_keys = set(incoming_round.keys()) | set(stored_round.keys())
        for key in match_keys:
            try:
                match_idx = int(key)
            except (TypeError, ValueError):
                continue
            if ko_match_is_closed(round_id, match_idx):
                if key in stored_round:
                    round_out[key] = stored_round[key]
            else:
                if key in incoming_round:
                    round_out[key] = incoming_round[key]
                elif key in stored_round:
                    round_out[key] = stored_round[key]
        if round_out:
            merged_ko[round_id] = round_out
    picks["ko"] = merged_ko

    score = calculate_score(picks, get_results())
    timestamp = utc_now_iso()

    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO submissions (email, name, picks_json, score, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                name       = excluded.name,
                picks_json = excluded.picks_json,
                score      = excluded.score,
                updated_at = excluded.updated_at
            """,
            (email, name, json.dumps(picks), score, timestamp),
        )

    return jsonify({"ok": True, "score": score, "locked": locked})


@app.get("/api/results")
def api_get_results():
    return jsonify({"ok": True, **get_results_meta()})


@app.get("/api/champion-latest")
def api_champion_latest():
    team = (request.args.get("team") or "").strip()
    if not team:
        return jsonify({"ok": False, "error": "team query param is required"}), 400
    try:
        info = fetch_team_last_match(team)
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": f"Network error: {exc}"}), 502
    if not info:
        return jsonify({"ok": True, "team": team, "match": None})
    return jsonify({"ok": True, "team": team, "match": info})


@app.post("/admin/results")
def admin_set_results():
    require_admin()
    payload = request.get_json(silent=True) or {}
    results = payload.get("results")
    if results is None and "raw" in payload:
        try:
            results = json.loads(payload["raw"]) if payload["raw"] else {}
        except (TypeError, ValueError) as exc:
            return jsonify({"ok": False, "error": f"Invalid JSON: {exc}"}), 400
    if not isinstance(results, dict):
        return jsonify({"ok": False, "error": "results must be a JSON object"}), 400

    save_results(results)
    affected = recalculate_all_scores()
    meta = get_results_meta()
    return jsonify({"ok": True, "updated_at": meta["updated_at"], "recalculated": affected})


@app.post("/admin/results/refresh")
def admin_refresh_results():
    require_admin()
    try:
        raw_matches = fetch_football_data_matches()
    except requests.RequestException as exc:
        return jsonify({"ok": False, "error": f"API request failed: {exc}"}), 502
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    results = parse_football_data_results(raw_matches)
    save_results(results)
    affected = recalculate_all_scores()
    meta = get_results_meta()
    return jsonify(
        {
            "ok": True,
            "updated_at": meta["updated_at"],
            "recalculated": affected,
            "results": results,
        }
    )


@app.post("/admin/results/clear")
def admin_clear_results():
    require_admin()
    save_results({})
    affected = recalculate_all_scores()
    return jsonify({"ok": True, "recalculated": affected})


if __name__ == "__main__":
    init_db()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
else:
    init_db()
