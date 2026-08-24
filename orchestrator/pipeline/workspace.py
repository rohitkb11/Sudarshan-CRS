"""Create per-scan copies so target source is never patched in place."""
from pathlib import Path
from datetime import datetime, timezone
import shutil


def create_workspace(source: Path, runs_dir: Path) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = runs_dir / f"{source.name}-{stamp}"
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("build", "__pycache__", "*.pyc"))
    return destination
