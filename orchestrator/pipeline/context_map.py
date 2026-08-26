from dataclasses import dataclass, field
from pathlib import Path
import re


FUNCTION_DEF_RE = re.compile(
    r"^\s*(?:(?:static|inline|extern)\s+)?(?:int|void|char\s*\*|size_t|bool|uint\w+_t)\s+(\w+)\s*\(([^)]*)\)\s*\{",
    re.MULTILINE,
)
CALL_RE = re.compile(r"\b([a-zA-Z_]\w*)\s*\(")


@dataclass
class FunctionInfo:
    name: str
    file: str
    start_line: int
    end_line: int
    signature: str
    callees: list[str] = field(default_factory=list)


def _find_matching_brace(text: str, start_index: int) -> int:
    depth = 0
    in_string = False
    in_char = False
    escape = False

    for i in range(start_index, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"' and not in_char:
            in_string = not in_string
            continue
        if ch == "'" and not in_string:
            in_char = not in_char
            continue
        if in_string or in_char:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


def build_context_map(target_dir: Path) -> dict[str, dict[str, object]]:
    """Build a lightweight AST/symbol index with call relationships for C target codebases."""
    index: dict[str, dict[str, object]] = {}

    for source in sorted(target_dir.rglob("*.[ch]")):
        if ".crs" in source.parts or "build" in source.parts:
            continue
        try:
            text = source.read_text(encoding="utf-8")
        except Exception:
            continue

        for match in FUNCTION_DEF_RE.finditer(text):
            func_name = match.group(1)
            sig = match.group(0).rstrip("{").strip()
            start_pos = match.start()
            brace_pos = text.find("{", match.end() - 1)
            if brace_pos == -1:
                continue

            end_pos = _find_matching_brace(text, brace_pos)
            body = text[brace_pos : end_pos + 1]

            # Extract calls inside body
            callees = [
                m.group(1)
                for m in CALL_RE.finditer(body)
                if m.group(1) not in ("if", "while", "for", "switch", "sizeof", "return", func_name)
            ]

            start_line = text.count("\n", 0, start_pos) + 1
            end_line = text.count("\n", 0, end_pos) + 1

            index[func_name] = {
                "file": str(source.relative_to(target_dir)),
                "start_line": start_line,
                "end_line": end_line,
                "signature": sig,
                "callees": list(dict.fromkeys(callees)),
            }

    return index


def context_slice(target_dir: Path, filename: str, needle: str, radius: int = 12) -> str:
    """Extract a window of lines surrounding a needle within a file."""
    path = target_dir / filename
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return ""

    hit = next((i for i, line in enumerate(lines) if needle in line), 0)
    start = max(0, hit - radius)
    end = min(len(lines), hit + radius + 1)
    return "\n".join(f"{i + 1:4}: {line}" for i, line in enumerate(lines[start:end], start))


def get_function_slice(target_dir: Path, function_name: str) -> str:
    """Retrieve full body of a indexed function with surrounding context."""
    cmap = build_context_map(target_dir)
    func_info = cmap.get(function_name)
    if not func_info:
        return ""

    file_path = target_dir / str(func_info["file"])
    if not file_path.is_file():
        return ""

    lines = file_path.read_text(encoding="utf-8").splitlines()
    start = max(0, int(func_info["start_line"]) - 1)
    end = min(len(lines), int(func_info["end_line"]))
    return "\n".join(f"{i + 1:4}: {line}" for i, line in enumerate(lines[start:end], start))
