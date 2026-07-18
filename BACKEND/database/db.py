"""
BACKEND/database/db.py
----------------------
The ONLY module that talks directly to SQLite.
No other file should import sqlite3 or issue SQL statements.

Public API
----------
get_connection()    -> sqlite3.Connection
init_db()           -> None
seed_db()           -> None
get_one(sql, params) -> dict | None
execute_write(sql, params) -> None
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime, timezone

# Resolve the path to config without importing the full Flask app (avoids
# circular imports when db.py is used in tests before app.py is initialised).
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_DIR)

from config import DATABASE_PATH  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Open and return a new SQLite connection.

    Rows are returned as dict-like objects (accessible by column name).
    The caller is responsible for closing the connection — use try/finally.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    NOT NULL,
    balance       REAL    NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    type        TEXT    NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
    amount      REAL    NOT NULL,
    timestamp   TEXT    NOT NULL
);
"""


def init_db() -> None:
    """
    Create tables (if they do not already exist) and seed initial data.
    Call once at application startup.
    """
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
        logger.info("Database schema initialised at: %s", DATABASE_PATH)
    finally:
        conn.close()

    seed_db()


# ---------------------------------------------------------------------------
# Seed data — one test customer inserted only when the table is empty
# ---------------------------------------------------------------------------

def seed_db() -> None:
    """
    Insert a default test customer if the customers table is empty.
    Credentials:  username=admin  password=password123
    """
    from werkzeug.security import generate_password_hash  # local import to keep module lightweight

    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM customers").fetchone()
        if row["cnt"] == 0:
            hashed = generate_password_hash("password123")
            conn.execute(
                "INSERT INTO customers (username, password_hash, full_name, balance) VALUES (?,?,?,?)",
                ("admin", hashed, "Admin User", 1000.00),
            )
            conn.commit()
            logger.info("Seeded default test customer: admin / password123")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Generic query helpers
# ---------------------------------------------------------------------------

def get_one(sql: str, params: tuple = ()) -> dict | None:
    """
    Execute a SELECT statement and return the first row as a plain dict,
    or None if no rows were found.
    """
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None
    except sqlite3.Error as exc:
        logger.error("get_one failed — sql=%s  params=%s  error=%s", sql, params, exc)
        raise
    finally:
        conn.close()


def get_many(sql: str, params: tuple = ()) -> list[dict]:
    """
    Execute a SELECT statement and return all matching rows as a list of dicts.
    """
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_many failed — sql=%s  params=%s  error=%s", sql, params, exc)
        raise
    finally:
        conn.close()


def execute_write(sql: str, params: tuple = ()) -> None:
    """
    Execute a single INSERT/UPDATE/DELETE statement and commit.
    """
    conn = get_connection()
    try:
        conn.execute(sql, params)
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("execute_write failed — sql=%s  params=%s  error=%s", sql, params, exc)
        raise
    finally:
        conn.close()


def execute_transaction(operations: list[tuple]) -> None:
    """
    Execute multiple (sql, params) pairs atomically inside a single transaction.
    If any statement fails the whole transaction is rolled back.

    operations: list of (sql_string, params_tuple) pairs
    """
    conn = get_connection()
    try:
        for sql, params in operations:
            conn.execute(sql, params)
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("execute_transaction failed — error=%s", exc)
        raise
    finally:
        conn.close()
