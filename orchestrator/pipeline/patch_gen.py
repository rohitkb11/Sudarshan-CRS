from dataclasses import dataclass
from pathlib import Path


@dataclass
class PatchOutcome:
    applied: bool
    bug_class: str
    root_cause: str
    fix_pattern: str
    message: str


def apply_rule_patch(target_dir: Path) -> PatchOutcome:
    """Tier 1: bounded copy rule for the included C target. No model required."""
    source = target_dir / "src" / "parser.c"
    original = source.read_text(encoding="utf-8")
    unsafe = 'strcpy(buffer, input);'
    safe = 'if (strlen(input) >= sizeof(buffer)) return 2;\n    strcpy(buffer, input);'
    if unsafe not in original:
        return PatchOutcome(False, "CWE-120", "", "", "No supported unchecked-copy pattern found.")
    source.write_text(original.replace(unsafe, safe, 1), encoding="utf-8")
    return PatchOutcome(True, "CWE-120", "Unbounded input is copied into a 16-byte stack buffer.",
                        "Reject input at or above destination capacity before copying.", "Applied bounded-copy rule.")
