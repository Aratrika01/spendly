import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


def get_db():
    """Return a new SQLite connection with Row access and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables and indexes. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount      REAL    NOT NULL CHECK (amount > 0),
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                description TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses (user_id, date);
        """)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert a demo user and 8 sample expenses. No-op if users already exist."""
    conn = get_db()
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123", method="pbkdf2:sha256")),
        )
        user_id = cur.lastrowid

        # Spread the sample expenses across the current month (days kept <= 28 so every date is valid).
        today = date.today()
        days = [1, 4, 7, 10, 13, 16, 19, 22]
        samples = [
            (42.50, "Food", "Weekly groceries"),
            (18.00, "Transport", "Metro card top-up"),
            (120.00, "Bills", "Electricity bill"),
            (25.00, "Health", "Pharmacy"),
            (30.00, "Entertainment", "Movie tickets"),
            (64.99, "Shopping", "Running shoes"),
            (12.00, "Other", "Gift wrapping"),
            (8.75, "Food", "Coffee and snack"),
        ]
        sample_expenses = [
            (user_id, amount, category, today.replace(day=day).isoformat(), description)
            for day, (amount, category, description) in zip(days, samples)
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            sample_expenses,
        )
        conn.commit()
    finally:
        conn.close()
