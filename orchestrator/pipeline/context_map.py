from pathlib import Path
import re


FUNCTION_RE = re.compile(r"^\s*(?:int|void|char\s*\*)\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)


def build_context_map(target_dir: Path) -> dict[str, dict[str, object]]:
    """Small dependency-free MVP index; swap with tree-sitter in Phase 1."""
    index: dict[str, dict[str, object]] = {}
    for source in target_dir.rglob("*.c"):
        text = source.read_text(encoding="utf-8")
        for match in FUNCTION_RE.finditer(text):
            name = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            index[name] = {"file": str(source), "line": line, "signature": match.group(0).strip()}
    return index


def context_slice(target_dir: Path, filename: str, needle: str, radius: int = 12) -> str:
    path = target_dir / filename
    lines = path.read_text(encoding="utf-8").splitlines()
    hit = next((i for i, line in enumerate(lines) if needle in line), 0)
    start, end = max(0, hit - radius), min(len(lines), hit + radius + 1)
    return "\n".join(f"{i + 1:4}: {line}" for i, line in enumerate(lines[start:end], start))
