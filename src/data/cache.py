"""Data cache layer — SQLite-based cache for API responses."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class DataCache:
    """SQLite cache for API responses to avoid redundant network calls."""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "api_cache.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    ttl INTEGER NOT NULL DEFAULT 86400
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created ON cache(created_at)
            """)

    def _make_key(self, provider: str, endpoint: str, params: dict) -> str:
        """Create a deterministic cache key."""
        raw = json.dumps([provider, endpoint, params], sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, provider: str, endpoint: str, params: dict) -> Any | None:
        """Retrieve from cache if fresh."""
        key = self._make_key(provider, endpoint, params)
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT data, created_at, ttl FROM cache WHERE cache_key = ?",
                (key,)
            ).fetchone()

        if row is None:
            return None

        data_blob, created_at, ttl = row
        if time.time() - created_at > ttl:
            self._delete(key)
            return None

        return json.loads(data_blob)

    def set(self, provider: str, endpoint: str, data: Any, params: dict, ttl: int = 86400):
        """Store data in cache."""
        key = self._make_key(provider, endpoint, params)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (cache_key, data, created_at, ttl) VALUES (?, ?, ?, ?)",
                (key, json.dumps(data), time.time(), ttl)
            )

    def _delete(self, key: str):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))

    def clear_expired(self):
        """Remove expired entries."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM cache WHERE created_at + ttl < ?", (time.time(),))
