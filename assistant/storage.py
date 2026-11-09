"""Numbered booking requests in SQLite (minimal personal data, retention limit)."""
from __future__ import annotations

import json
import sqlite3
import time


class RequestStore:
    def __init__(self, path: str = "requests.db"):
        self._db = sqlite3.connect(path)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   created_at INTEGER NOT NULL,
                   tg_user_id INTEGER NOT NULL,
                   kind TEXT NOT NULL,              -- booking | escalation
                   payload TEXT NOT NULL,
                   status TEXT NOT NULL DEFAULT 'new')"""
        )
        self._db.commit()

    def add(self, tg_user_id: int, kind: str, payload: dict) -> int:
        cur = self._db.execute(
            "INSERT INTO requests (created_at, tg_user_id, kind, payload) VALUES (?, ?, ?, ?)",
            (int(time.time()), tg_user_id, kind, json.dumps(payload, ensure_ascii=False)),
        )
        self._db.commit()
        return cur.lastrowid

    def purge_older_than(self, days: int) -> int:
        cur = self._db.execute("DELETE FROM requests WHERE created_at < ?", (int(time.time()) - days * 86400,))
        self._db.commit()
        return cur.rowcount
