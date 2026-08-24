import json
from pathlib import Path
from datetime import datetime, timezone


class PatchMemory:
    def __init__(self, location: Path):
        self.location = location
        location.parent.mkdir(parents=True, exist_ok=True)

    def lookup(self, bug_class: str) -> dict | None:
        if not self.location.exists():
            return None
        entries = [json.loads(line) for line in self.location.read_text(encoding="utf-8").splitlines() if line]
        return next((entry for entry in reversed(entries) if entry["bug_class"] == bug_class), None)

    def record(self, bug_class: str, root_cause: str, fix_pattern: str) -> None:
        entry = {"bug_class": bug_class, "root_cause": root_cause, "fix_pattern": fix_pattern,
                 "verified_at": datetime.now(timezone.utc).isoformat()}
        with self.location.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
