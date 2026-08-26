from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable

from .context_map import context_slice, get_function_slice
from .llm_patch import llm_generate_patch
from .patch_memory import PatchMemory


@dataclass
class PatchOutcome:
    applied: bool
    bug_class: str
    root_cause: str
    fix_pattern: str
    message: str
    patched_file: str | None = None
    tier: str = "rule"


@dataclass
class PatchRule:
    name: str
    bug_class: str
    root_cause: str
    fix_pattern: str
    detector: Callable[[str], bool]
    applier: Callable[[str], str]


# -----------------------------------------------------------------------------
# Guardrail 8: Structural Patch Verification (Anti-Shallow Patch Check)
# -----------------------------------------------------------------------------

def validate_patch_structure(
    before_source: str,
    after_source: str,
    pov_bytes: bytes | None = None,
) -> tuple[bool, str]:
    """Verify the patch touches actual root-cause defense rather than hiding the crash (Guardrail 8)."""
    if before_source == after_source:
        return False, "Patch is empty (no changes made)."

    # Check 1: Ensure patch doesn't just hardcode the PoV crash string
    if pov_bytes and len(pov_bytes) > 4:
        try:
            ascii_sub = pov_bytes.decode("latin1", errors="ignore").strip()
            if len(ascii_sub) > 6 and ascii_sub in after_source and ascii_sub not in before_source:
                return False, "Patch hardcodes specific PoV input string (shallow suppression)."
        except Exception:
            pass

    # Check 2: Ensure patch doesn't completely gut the function with immediate exit
    if re.search(r"\{\s*exit\(0\);\s*\}", after_source) or re.search(r"\{\s*return\s+0;\s*\}", after_source):
        if not re.search(r"\{\s*exit\(0\);\s*\}", before_source) and not re.search(r"\{\s*return\s+0;\s*\}", before_source):
            return False, "Patch appears to unconditionally terminate execution without processing input."

    # Check 3: Verified structural improvements (bounds checks, safe functions, capacity guards)
    defensive_patterns = (
        r"sizeof\s*\(",
        r"strlen\s*\(",
        r"snprintf\s*\(",
        r"fgets\s*\(",
        r"strncat\s*\(",
        r"strncpy\s*\(",
        r">=\s*\w+",
        r">\s*\w+",
        r"<\s*\w+",
        r"<=\s*\w+",
        r"free\s*\(",
        r"NULL",
    )
    has_defense = any(re.search(pat, after_source) for pat in defensive_patterns)
    if not has_defense:
        return False, "Patch lacks recognizable defensive bounds or memory management logic."

    return True, "Structural validation passed."


# -----------------------------------------------------------------------------
# Tier 1 Rule Registry
# -----------------------------------------------------------------------------

def _detect_strcpy(code: str) -> bool:
    return 'strcpy(buffer, input);' in code


def _apply_strcpy(code: str) -> str:
    unsafe = 'strcpy(buffer, input);'
    safe = 'if (strlen(input) >= sizeof(buffer)) return 2;\n    strcpy(buffer, input);'
    return code.replace(unsafe, safe, 1)


def _detect_sprintf(code: str) -> bool:
    return bool(re.search(r'sprintf\s*\(\s*buffer\s*,\s*"%s"\s*,\s*input\s*\)\s*;', code))


def _apply_sprintf(code: str) -> str:
    pattern = re.compile(r'sprintf\s*\(\s*buffer\s*,\s*"%s"\s*,\s*input\s*\)\s*;')
    safe = 'if (strlen(input) >= sizeof(buffer)) return 2;\n    snprintf(buffer, sizeof(buffer), "%s", input);'
    return pattern.sub(safe, code, count=1)


def _detect_gets(code: str) -> bool:
    return 'gets(buffer);' in code


def _apply_gets(code: str) -> str:
    unsafe = 'gets(buffer);'
    safe = 'if (fgets(buffer, sizeof(buffer), stdin) == NULL) return 1;'
    return code.replace(unsafe, safe, 1)


def _detect_strcat(code: str) -> bool:
    return 'strcat(buffer, input);' in code


def _apply_strcat(code: str) -> str:
    unsafe = 'strcat(buffer, input);'
    safe = 'if (strlen(buffer) + strlen(input) >= sizeof(buffer)) return 2;\n    strncat(buffer, input, sizeof(buffer) - strlen(buffer) - 1);'
    return code.replace(unsafe, safe, 1)


RULE_REGISTRY: list[PatchRule] = [
    PatchRule(
        name="bounded_strcpy",
        bug_class="CWE-120",
        root_cause="Unbounded input is copied into a stack buffer without length check.",
        fix_pattern="Reject input at or above destination capacity before copying.",
        detector=_detect_strcpy,
        applier=_apply_strcpy,
    ),
    PatchRule(
        name="bounded_sprintf",
        bug_class="CWE-120",
        root_cause="Unbounded input is formatted into a fixed-size buffer using sprintf.",
        fix_pattern="Replace sprintf with length check and snprintf.",
        detector=_detect_sprintf,
        applier=_apply_sprintf,
    ),
    PatchRule(
        name="safe_gets",
        bug_class="CWE-676",
        root_cause="Inherently dangerous gets() function used without boundary constraints.",
        fix_pattern="Replace gets() with fgets() specifying destination buffer size.",
        detector=_detect_gets,
        applier=_apply_gets,
    ),
    PatchRule(
        name="bounded_strcat",
        bug_class="CWE-120",
        root_cause="Unbounded concatenation into destination buffer without remaining capacity check.",
        fix_pattern="Check combined length and use bounded strncat.",
        detector=_detect_strcat,
        applier=_apply_strcat,
    ),
]


def apply_rule_patch(target_dir: Path) -> PatchOutcome:
    """Tier 1: Search all .c files in target_dir and apply the first matching rule."""
    c_files = sorted(target_dir.rglob("*.c"))
    for file_path in c_files:
        if ".crs" in file_path.parts or "build" in file_path.parts:
            continue
        try:
            original = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        for rule in RULE_REGISTRY:
            if rule.detector(original):
                patched = rule.applier(original)
                valid, reason = validate_patch_structure(original, patched)
                if not valid:
                    continue

                file_path.write_text(patched, encoding="utf-8")
                rel_path = str(file_path.relative_to(target_dir))
                return PatchOutcome(
                    applied=True,
                    bug_class=rule.bug_class,
                    root_cause=rule.root_cause,
                    fix_pattern=rule.fix_pattern,
                    message=f"Applied rule '{rule.name}' on {rel_path}.",
                    patched_file=rel_path,
                    tier="rule",
                )

    return PatchOutcome(
        applied=False,
        bug_class="CWE-120",
        root_cause="",
        fix_pattern="",
        message="No supported deterministic patch rule found in target source.",
        tier="rule",
    )


# -----------------------------------------------------------------------------
# Tiered Patch Waterfall: Tier 1 (Rules) -> Tier 2 (Memory) -> Tier 3 (LLM)
# -----------------------------------------------------------------------------

def generate_patch(
    target_dir: Path,
    crash_signature: str | None = None,
    patch_memory: PatchMemory | None = None,
    attempt: int = 1,
    prior_failure: str | None = None,
    pov_bytes: bytes | None = None,
) -> PatchOutcome:
    """Apply tiered patch generation:
    1. Tier 1: Deterministic rule library.
    2. Tier 2: Patch Memory precedent guidance.
    3. Tier 3: LLM fallback (Anthropic Claude), escalating model on retry.
    """
    # Tier 1: Rule Library
    if attempt == 1:
        rule_outcome = apply_rule_patch(target_dir)
        if rule_outcome.applied:
            return rule_outcome

    # Locate candidate C/C++ source file to patch
    valid_exts = (".c", ".cpp", ".cc", ".cxx")
    c_files = [
        f for f in sorted(target_dir.rglob("*"))
        if f.is_file() and f.suffix.lower() in valid_exts
        and ".crs" not in f.parts and "build" not in f.parts and "fuzz" not in f.parts
    ]
    if not c_files:
        c_files = [
            f for f in sorted(target_dir.rglob("*"))
            if f.is_file() and f.suffix.lower() in valid_exts
            and ".crs" not in f.parts and "build" not in f.parts
        ]
    if not c_files:
        return PatchOutcome(
            applied=False,
            bug_class="unknown",
            root_cause="",
            fix_pattern="",
            message="No candidate C/C++ source files found in target workspace.",
        )

    target_file = c_files[0]
    rel_path = str(target_file.relative_to(target_dir))
    source_content = target_file.read_text(encoding="utf-8")

    # Tier 2: Patch Memory Lookup
    bug_class_guess = "CWE-120"
    if crash_signature:
        sig_lower = crash_signature.lower()
        if "buffer-overflow" in sig_lower:
            bug_class_guess = "CWE-120"
        elif "use-after-free" in sig_lower:
            bug_class_guess = "CWE-416"
        elif "null-dereference" in sig_lower:
            bug_class_guess = "CWE-476"
        elif "format" in sig_lower:
            bug_class_guess = "CWE-134"

    memory_precedent = None
    if patch_memory:
        memory_precedent = patch_memory.lookup(bug_class_guess)

    # Build context slice around likely defect location
    slice_text = context_slice(target_dir, rel_path, "buffer", radius=15)
    if not slice_text or slice_text.strip() == "":
        slice_text = source_content[:1500]

    # Tier 3: LLM Fallback
    model_tier = "strong" if attempt > 1 else "fast"
    llm_result = llm_generate_patch(
        source_content=source_content,
        filename=rel_path,
        context_slice=slice_text,
        crash_signature=crash_signature,
        bug_class=bug_class_guess,
        prior_failure=prior_failure,
        patch_memory_hint=memory_precedent,
        model_tier=model_tier,
    )

    if llm_result:
        valid, reason = validate_patch_structure(source_content, llm_result.patched_content, pov_bytes)
        if not valid:
            return PatchOutcome(
                applied=False,
                bug_class=bug_class_guess,
                root_cause=llm_result.root_cause,
                fix_pattern=llm_result.fix_pattern,
                message=f"LLM patch rejected by structural validation: {reason}",
                patched_file=rel_path,
                tier="llm",
            )

        target_file.write_text(llm_result.patched_content, encoding="utf-8")
        tier_used = "memory+llm" if memory_precedent else "llm"
        return PatchOutcome(
            applied=True,
            bug_class=bug_class_guess,
            root_cause=llm_result.root_cause,
            fix_pattern=llm_result.fix_pattern,
            message=f"Applied {tier_used} patch on {rel_path} (model: {model_tier}, attempt: {attempt}).",
            patched_file=rel_path,
            tier=tier_used,
        )

    return PatchOutcome(
        applied=False,
        bug_class=bug_class_guess,
        root_cause="",
        fix_pattern="",
        message=f"No patch could be generated (attempt {attempt}).",
        patched_file=rel_path,
        tier="none",
    )
