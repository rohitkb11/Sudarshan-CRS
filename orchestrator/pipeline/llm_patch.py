import json
import logging
import re
from typing import NamedTuple
from orchestrator.config import settings

logger = logging.getLogger(__name__)


class LLMPatchResult(NamedTuple):
    patched_content: str
    root_cause: str
    fix_pattern: str


def _build_prompt(
    source_content: str,
    filename: str,
    context_slice: str,
    crash_signature: str | None = None,
    bug_class: str | None = None,
    prior_failure: str | None = None,
    patch_memory_hint: dict | None = None,
) -> tuple[str, str]:
    system_prompt = (
        "You are an autonomous Cyber-Reasoning System (CRS) security engineer specializing in automated vulnerability repair for C/C++ programs. "
        "You analyze sanitizer crash signatures, locate root cause defects, and generate safe, minimal, robust patches that prevent exploits "
        "without causing functional regressions or breaking test suites.\n"
        "Output ONLY a valid JSON object matching the requested schema."
    )

    prompt_parts = [
        f"Target file: `{filename}`",
        f"Vulnerability class: {bug_class or 'Memory corruption / CWE'}",
        f"Sanitizer crash signature: {crash_signature or 'N/A'}",
        "",
        "### Relevant Code Slice:",
        "```c",
        context_slice,
        "```",
        "",
        "### Full Source File:",
        "```c",
        source_content,
        "```",
    ]

    if patch_memory_hint:
        prompt_parts.extend([
            "",
            "### Precedent from Patch Memory (similar past verified fix):",
            f"- Bug class: {patch_memory_hint.get('bug_class')}",
            f"- Root cause: {patch_memory_hint.get('root_cause')}",
            f"- Fix pattern: {patch_memory_hint.get('fix_pattern')}",
        ])

    if prior_failure:
        prompt_parts.extend([
            "",
            "### PREVIOUS ATTEMPT FAILED VERIFICATION:",
            f"Reason: {prior_failure}",
            "Please ensure your new patch addresses this specific failure without causing regressions.",
        ])

    prompt_parts.extend([
        "",
        "Respond ONLY with a valid JSON object. Do not include markdown code block formatting or explanations outside the JSON.",
        "The JSON object must contain exactly these 3 keys:",
        "{",
        '  "root_cause": "One sentence explaining the exact root cause defect",',
        '  "fix_pattern": "One sentence explaining the defensive fix pattern applied",',
        '  "patched_full_file": "Complete contents of the entire patched source file as a single string"',
        "}",
    ])

    return system_prompt, "\n".join(prompt_parts)


def _fix_json_escapes(s: str) -> str:
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            next_char = s[i + 1]
            if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                result.append(s[i])
                result.append(s[i + 1])
                i += 2
            elif next_char == 'u' and i + 5 < len(s):
                result.append(s[i:i+6])
                i += 6
            else:
                result.append('\\\\')
                result.append(next_char)
                i += 2
        else:
            result.append(s[i])
            i += 1
    return "".join(result)

def _parse_llm_json(raw_text: str) -> LLMPatchResult | None:
    content = raw_text.strip()

    # Strip reasoning <think>...</think> blocks from reasoning models (Qwen, DeepSeek, etc.)
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    # Strip markdown code fencing if present
    if "```" in content:
        content = re.sub(r"```(?:json)?", "", content).strip()

    content = _fix_json_escapes(content)

    # Find the starting brace of the JSON object
    start_idx = content.find("{")
    if start_idx == -1:
        logger.warning("No JSON object '{' found in LLM response.")
        return None

    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(content, start_idx)
        patched_code = data.get("patched_full_file") or data.get("patched_code")
        if not patched_code:
            return None

        return LLMPatchResult(
            patched_content=patched_code,
            root_cause=data.get("root_cause", "Identified by LLM reasoning"),
            fix_pattern=data.get("fix_pattern", "Applied LLM-generated patch"),
        )
    except Exception as exc:
        logger.warning("Failed to decode JSON from LLM response: %s (raw snippet: %s)", exc, content[start_idx:start_idx + 200])
        return None


def _call_groq(
    system_prompt: str,
    user_prompt: str,
    model_tier: str = "fast",
) -> LLMPatchResult | None:
    """Invoke Groq API with configured parameters (Qwen / Llama models)."""
    api_key = settings.groq_api_key
    if not api_key:
        return None

    try:
        from groq import Groq
    except ImportError:
        logger.warning("groq package not installed; skipping Groq LLM patch.")
        return None

    model_name = (
        settings.groq_model_strong
        if model_tier == "strong"
        else settings.groq_model_fast
    )

    request_payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.groq_temperature,
        "top_p": settings.groq_top_p,
    }

    try:
        client = Groq(api_key=api_key)
        call_kwargs = dict(request_payload)
        call_kwargs["max_tokens"] = settings.groq_max_completion_tokens

        # Attempt call
        response = client.chat.completions.create(**call_kwargs)
        raw_text = response.choices[0].message.content or ""
        return _parse_llm_json(raw_text)

    except Exception as exc:
        logger.warning("Groq API call failed for model '%s': %s", model_name, exc)
        return None


def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model_tier: str = "fast",
) -> LLMPatchResult | None:
    """Invoke Anthropic Claude API."""
    api_key = settings.anthropic_api_key
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed; skipping Anthropic LLM patch.")
        return None

    model_name = (
        settings.llm_model_strong
        if model_tier == "strong"
        else settings.llm_model_fast
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=0.1,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw_text = response.content[0].text
        return _parse_llm_json(raw_text)
    except Exception as exc:
        logger.warning("Anthropic API call failed: %s", exc)
        return None


def llm_generate_patch(
    source_content: str,
    filename: str,
    context_slice: str,
    crash_signature: str | None = None,
    bug_class: str | None = None,
    prior_failure: str | None = None,
    patch_memory_hint: dict | None = None,
    model_tier: str = "fast",
) -> LLMPatchResult | None:
    """Tier 3: Generate a patch using configured LLM reasoning provider (Groq / Anthropic).
    
    Returns LLMPatchResult if successful, or None if unavailable / failed.
    """
    system_prompt, user_prompt = _build_prompt(
        source_content=source_content,
        filename=filename,
        context_slice=context_slice,
        crash_signature=crash_signature,
        bug_class=bug_class,
        prior_failure=prior_failure,
        patch_memory_hint=patch_memory_hint,
    )

    # Provider prioritization: Groq first (or explicitly chosen), Anthropic fallback
    if settings.llm_provider == "groq" or settings.groq_api_key:
        result = _call_groq(system_prompt, user_prompt, model_tier)
        if result:
            return result
        # If Groq call failed or key was missing, fall through to Anthropic if available
        if settings.anthropic_api_key:
            return _call_anthropic(system_prompt, user_prompt, model_tier)
        return None

    if settings.llm_provider == "anthropic" or settings.anthropic_api_key:
        result = _call_anthropic(system_prompt, user_prompt, model_tier)
        if result:
            return result
        if settings.groq_api_key:
            return _call_groq(system_prompt, user_prompt, model_tier)
        return None

    logger.info("No LLM API keys configured (GROQ_API_KEY or ANTHROPIC_API_KEY). Skipping Tier 3.")
    return None
