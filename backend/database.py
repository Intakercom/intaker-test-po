"""SQLite setup and per-request connections; no third-party dependencies."""
import sqlite3
from contextlib import closing
from pathlib import Path


def connect(path):
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute('PRAGMA busy_timeout = 10000')
    return connection


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as db, db:
        db.execute('PRAGMA journal_mode = WAL')
        db.executescript(Path(__file__).with_name('schema.sql').read_text())
        if not db.execute('SELECT 1 FROM organizations LIMIT 1').fetchone():
            from .seed import seed
            seed(db)
