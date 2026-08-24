from pathlib import Path
import difflib


def write_patch(before: str, after: str, relative_path: str, output: Path) -> Path | None:
    diff = list(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                     fromfile=f"a/{relative_path}", tofile=f"b/{relative_path}"))
    if not diff:
        return None
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(diff), encoding="utf-8")
    return output
