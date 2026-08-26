from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass
class MemoryEntry:
    bug_class: str
    root_cause: str
    fix_pattern: str
    crash_signature: str | None = None
    target: str | None = None
    verified_at: str = ""


class PatchMemory:
    """Case-Based Reasoning (CBR) store for verified vulnerability fix patterns (§5.3).
    
    Supports both JSONL and SQLite backends based on file extension.
    """

    def __init__(self, location: Path):
        self.location = location
        self.is_sqlite = location.suffix == ".db"
        location.parent.mkdir(parents=True, exist_ok=True)
        if self.is_sqlite:
            self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.location)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patch_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bug_class TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    fix_pattern TEXT NOT NULL,
                    crash_signature TEXT,
                    target TEXT,
                    verified_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_bug_class ON patch_memory(bug_class)")

    def lookup(self, bug_class: str, crash_signature: str | None = None) -> dict[str, Any] | None:
        """Find the most relevant verified fix precedent.
        
        Matches by bug_class or signature patterns (pattern matching over literal byte matches).
        """
        entries = self.list_all()
        if not entries:
            return None

        # 1. Exact match on bug_class and similar crash signature
        if crash_signature:
            sig_lower = crash_signature.lower()
            for entry in reversed(entries):
                if entry.get("bug_class") == bug_class and entry.get("crash_signature"):
                    if entry["crash_signature"].lower() in sig_lower or sig_lower in entry["crash_signature"].lower():
                        return entry

        # 2. Match on bug_class (e.g. CWE-120)
        for entry in reversed(entries):
            if entry.get("bug_class") == bug_class:
                return entry

        # 3. Fuzzy bug category match (e.g. buffer, format, overflow)
        category = bug_class.lower()
        for entry in reversed(entries):
            entry_bc = entry.get("bug_class", "").lower()
            if category in entry_bc or entry_bc in category:
                return entry

        return None

    def record(
        self,
        bug_class: str,
        root_cause: str,
        fix_pattern: str,
        crash_signature: str | None = None,
        target: str | None = None,
    ) -> None:
        """Record a verified patch pattern into persistent memory.
        
        Only invoked when a patch passes ALL V1-V4 verification gates.
        """
        now = datetime.now(timezone.utc).isoformat()
        if self.is_sqlite:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO patch_memory (bug_class, root_cause, fix_pattern, crash_signature, target, verified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (bug_class, root_cause, fix_pattern, crash_signature, target, now),
                )
        else:
            entry = {
                "bug_class": bug_class,
                "root_cause": root_cause,
                "fix_pattern": fix_pattern,
                "crash_signature": crash_signature,
                "target": target,
                "verified_at": now,
            }
            with self.location.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")

    def list_all(self) -> list[dict[str, Any]]:
        """Retrieve all recorded precedents."""
        if not self.location.exists():
            return []

        if self.is_sqlite:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM patch_memory ORDER BY id ASC")
                return [dict(row) for row in cursor.fetchall()]
            finally:
                conn.close()
        else:
            try:
                lines = self.location.read_text(encoding="utf-8").splitlines()
                return [json.loads(line) for line in lines if line.strip()]
            except Exception:
                return []

    def get_stats(self) -> dict[str, Any]:
        """Summary statistics of stored patch memory."""
        entries = self.list_all()
        by_class: dict[str, int] = {}
        for e in entries:
            bc = e.get("bug_class", "unknown")
            by_class[bc] = by_class.get(bc, 0) + 1
        return {
            "total_verified_fixes": len(entries),
            "by_bug_class": by_class,
            "storage_backend": "sqlite" if self.is_sqlite else "jsonl",
        }
