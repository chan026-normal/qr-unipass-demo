"""
storage.py — single source of truth for attendance data.

Two interchangeable backends behind ONE interface, chosen by the USE_SHEETS
setting (see secrets.toml.example):

  - Local SQLite file  (USE_SHEETS=false)  -> zero setup, default
  - Google Sheets      (USE_SHEETS=true)   -> persistent, needs a service account

Public interface (this is all the rest of the app should call):
    add_checkin(name, student_id="", source="classroom") -> dict
    get_checkins() -> list[dict]
    reset() -> None
    load_roster() -> list[str]

Every record is a dict with exactly these keys:
    {"name", "student_id", "timestamp", "source"}
"""
from __future__ import annotations

import csv
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

FIELDS = ["name", "student_id", "timestamp", "source"]


# --------------------------------------------------------------------------- #
# Settings — read from st.secrets first, then environment, then default.
# Works even when Streamlit is not installed (falls back to env vars).
# --------------------------------------------------------------------------- #
def get_setting(key: str, default: str = "") -> str:
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


def _flag(key: str, default: str = "false") -> bool:
    return get_setting(key, default).strip().lower() in ("1", "true", "yes", "on")


def use_sheets() -> bool:
    return _flag("USE_SHEETS", "false")


def allow_duplicates() -> bool:
    return _flag("ALLOW_DUPLICATES", "false")


def timezone_name() -> str:
    return get_setting("TIMEZONE", "Asia/Ho_Chi_Minh")


def source_label() -> str:
    return "Google Sheets" if use_sheets() else "Local store"


def now_iso() -> str:
    tz = None
    if ZoneInfo is not None:
        try:
            tz = ZoneInfo(timezone_name())
        except Exception:
            tz = None
    return datetime.now(tz).replace(microsecond=0).isoformat()


def _key(rec: dict) -> str:
    """Identity used for duplicate detection: student_id if given, else name."""
    sid = (rec.get("student_id") or "").strip().lower()
    if sid:
        return "id:" + sid
    return "name:" + (rec.get("name") or "").strip().lower()


class AlreadyCheckedIn(Exception):
    """Raised when the same person checks in twice (and duplicates are off)."""


# ============================== Local SQLite =============================== #
_DB_PATH = Path(__file__).with_name("attendance.db")
_LOCK = threading.Lock()  # serialise writes within this process


def _connect():
    conn = sqlite3.connect(_DB_PATH, timeout=5.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def _sqlite_init():
    conn = _connect()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS attendance (
                   name       TEXT NOT NULL,
                   student_id TEXT,
                   timestamp  TEXT NOT NULL,
                   source     TEXT
               )"""
        )
        conn.commit()
    finally:
        conn.close()


def _sqlite_add(rec: dict):
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO attendance (name, student_id, timestamp, source) "
                "VALUES (?, ?, ?, ?)",
                (rec["name"], rec["student_id"], rec["timestamp"], rec["source"]),
            )
            conn.commit()
        finally:
            conn.close()


def _sqlite_get() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT name, student_id, timestamp, source "
            "FROM attendance ORDER BY timestamp ASC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(zip(FIELDS, row)) for row in rows]


def _sqlite_reset():
    with _LOCK:
        conn = _connect()
        try:
            conn.execute("DELETE FROM attendance")
            conn.commit()
        finally:
            conn.close()


# ============================== Google Sheets ============================= #
def _worksheet():
    """Open (and cache) the 'attendance' worksheet via gspread."""
    import streamlit as st

    @st.cache_resource(show_spinner=False)
    def _open():
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_name = get_setting("SHEET_NAME", "qr-unipass-attendance")
        ws = client.open(sheet_name).worksheet("attendance")
        if ws.row_values(1)[:4] != FIELDS:  # ensure a header row exists
            ws.update("A1:D1", [FIELDS])
        return ws

    return _open()


def _sheets_add(rec: dict):
    import gspread

    ws = _worksheet()
    for attempt in range(2):  # one retry on transient API errors
        try:
            ws.append_row(
                [rec["name"], rec["student_id"], rec["timestamp"], rec["source"]],
                value_input_option="USER_ENTERED",
            )
            return
        except gspread.exceptions.APIError:
            if attempt == 1:
                raise


def _sheets_get() -> list[dict]:
    ws = _worksheet()
    records = ws.get_all_records(expected_headers=FIELDS)
    return [{k: str(r.get(k, "")) for k in FIELDS} for r in records]


def _sheets_reset():
    ws = _worksheet()
    ws.clear()
    ws.update("A1:D1", [FIELDS])


# ============================== Public API ================================ #
def add_checkin(name: str, student_id: str = "", source: str = "classroom") -> dict:
    name = (name or "").strip()
    student_id = (student_id or "").strip()
    if not name:
        raise ValueError("Name is required.")

    rec = {
        "name": name,
        "student_id": student_id,
        "timestamp": now_iso(),
        "source": source or "classroom",
    }

    if not allow_duplicates():
        if _key(rec) in {_key(r) for r in get_checkins()}:
            raise AlreadyCheckedIn(name)

    if use_sheets():
        _sheets_add(rec)
    else:
        _sqlite_init()
        _sqlite_add(rec)
    return rec


def get_checkins() -> list[dict]:
    if use_sheets():
        try:
            return _sheets_get()
        except Exception:
            return []  # never crash the dashboard on a read hiccup
    _sqlite_init()
    return _sqlite_get()


def reset() -> None:
    if use_sheets():
        _sheets_reset()
    else:
        _sqlite_init()
        _sqlite_reset()


def load_roster() -> list[str]:
    """Optional pre-loaded names. Active only if roster.csv exists (column 'name')."""
    path = Path(__file__).with_name("roster.csv")
    if not path.exists():
        return []
    names: list[str] = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                n = (row.get("name") or "").strip()
                if n:
                    names.append(n)
    except Exception:
        return []
    return names


# ====================== Cafeteria module (stretch goal) =================== #
# Virtual balance ONLY — this is a simulation, never a real payment.
# Kept fully separate from attendance so it can never affect that demo.
# Balance is DERIVED from a transaction log, so both backends stay simple
# and there is no mutable balance state to corrupt.
CAFE_FIELDS = ["name", "student_id", "kind", "item", "amount", "timestamp"]


class InsufficientBalance(Exception):
    """Raised when a student tries to pay more than their virtual balance."""


def cafe_start_balance() -> int:
    try:
        return int(get_setting("CAFE_START_BALANCE", "200000"))
    except (TypeError, ValueError):
        return 200000


def fmt_vnd(amount) -> str:
    return f"{int(amount):,} ₫"  # e.g. "35,000 ₫"


# --- local SQLite ---
def _cafe_sqlite_init():
    conn = _connect()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cafeteria (
                   name       TEXT NOT NULL,
                   student_id TEXT,
                   kind       TEXT NOT NULL,
                   item       TEXT,
                   amount     INTEGER NOT NULL,
                   timestamp  TEXT NOT NULL
               )"""
        )
        conn.commit()
    finally:
        conn.close()


def _cafe_sqlite_add(rec: dict):
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO cafeteria (name, student_id, kind, item, amount, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rec["name"], rec["student_id"], rec["kind"], rec["item"],
                 rec["amount"], rec["timestamp"]),
            )
            conn.commit()
        finally:
            conn.close()


def _cafe_sqlite_get() -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT name, student_id, kind, item, amount, timestamp "
            "FROM cafeteria ORDER BY timestamp ASC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(zip(CAFE_FIELDS, row)) for row in rows]


def _cafe_sqlite_reset():
    with _LOCK:
        conn = _connect()
        try:
            conn.execute("DELETE FROM cafeteria")
            conn.commit()
        finally:
            conn.close()


# --- Google Sheets ---
def _cafe_ws():
    import streamlit as st

    @st.cache_resource(show_spinner=False)
    def _open():
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        info = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open(get_setting("SHEET_NAME", "qr-unipass-attendance"))
        try:
            ws = sh.worksheet("cafeteria")
        except Exception:
            ws = sh.add_worksheet("cafeteria", rows=2000, cols=10)
        if ws.row_values(1)[:6] != CAFE_FIELDS:
            ws.update("A1:F1", [CAFE_FIELDS])
        return ws

    return _open()


def _cafe_sheets_add(rec: dict):
    import gspread

    ws = _cafe_ws()
    for attempt in range(2):
        try:
            ws.append_row(
                [rec["name"], rec["student_id"], rec["kind"], rec["item"],
                 rec["amount"], rec["timestamp"]],
                value_input_option="USER_ENTERED",
            )
            return
        except gspread.exceptions.APIError:
            if attempt == 1:
                raise


def _cafe_sheets_get() -> list[dict]:
    ws = _cafe_ws()
    out = []
    for r in ws.get_all_records(expected_headers=CAFE_FIELDS):
        d = {k: r.get(k, "") for k in CAFE_FIELDS}
        try:
            d["amount"] = int(d["amount"] or 0)
        except (TypeError, ValueError):
            d["amount"] = 0
        out.append(d)
    return out


def _cafe_sheets_reset():
    ws = _cafe_ws()
    ws.clear()
    ws.update("A1:F1", [CAFE_FIELDS])


# --- public cafeteria API ---
def _cafe_add(rec: dict):
    if use_sheets():
        _cafe_sheets_add(rec)
    else:
        _cafe_sqlite_init()
        _cafe_sqlite_add(rec)


def get_cafeteria() -> list[dict]:
    if use_sheets():
        try:
            return _cafe_sheets_get()
        except Exception:
            return []
    _cafe_sqlite_init()
    return _cafe_sqlite_get()


def cafe_balance(name: str, student_id: str = "") -> int:
    key = _key({"name": name, "student_id": student_id})
    bal = cafe_start_balance()
    for r in get_cafeteria():
        if _key(r) != key:
            continue
        amt = int(r.get("amount") or 0)
        if r.get("kind") == "pay":
            bal -= amt
        elif r.get("kind") == "topup":
            bal += amt
    return bal


def cafe_pay(name: str, item: str, amount: int, student_id: str = "") -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("Name is required.")
    amount = int(amount)
    if cafe_balance(name, student_id) < amount:
        raise InsufficientBalance(name)
    _cafe_add({
        "name": name, "student_id": (student_id or "").strip(), "kind": "pay",
        "item": item, "amount": amount, "timestamp": now_iso(),
    })
    return cafe_balance(name, student_id)


def cafe_topup(name: str, amount: int, student_id: str = "") -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("Name is required.")
    _cafe_add({
        "name": name, "student_id": (student_id or "").strip(), "kind": "topup",
        "item": "", "amount": int(amount), "timestamp": now_iso(),
    })
    return cafe_balance(name, student_id)


def cafe_reset() -> None:
    if use_sheets():
        _cafe_sheets_reset()
    else:
        _cafe_sqlite_init()
        _cafe_sqlite_reset()
