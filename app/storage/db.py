import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.settings import env

SCHEMA = """
CREATE TABLE IF NOT EXISTS arbitrations (
  id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, input_text TEXT, prompt TEXT,
  verdict_json TEXT, score INTEGER, confidence REAL, degraded INTEGER, latency_ms INTEGER,
  prompt_version TEXT);
CREATE TABLE IF NOT EXISTS critiques (
  id INTEGER PRIMARY KEY AUTOINCREMENT, arbitration_id TEXT, dimension TEXT, model TEXT,
  score INTEGER, confidence REAL, latency_ms INTEGER, raw_json TEXT);
CREATE TABLE IF NOT EXISTS issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT, arbitration_id TEXT, critique_id INTEGER, category TEXT,
  severity INTEGER, quote TEXT, status TEXT CHECK(status IN ('confirmed','dismissed','pending')));
CREATE TABLE IF NOT EXISTS disagreements (
  id INTEGER PRIMARY KEY AUTOINCREMENT, arbitration_id TEXT, type TEXT, resolution TEXT);
CREATE TABLE IF NOT EXISTS batches (
  id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, total INTEGER, done INTEGER, status TEXT);
"""


@contextmanager
def connect():
    path = Path(env().arbiter_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.executescript(SCHEMA)
