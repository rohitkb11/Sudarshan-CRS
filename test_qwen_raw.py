"""Test: Groq LLM patch generation - with robust JSON escape handling."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from groq import Groq
import re
import json

env_dict = dict(
    line.split('=', 1)
    for line in Path('.env').read_text().splitlines()
    if '=' in line and not line.startswith('#')
)
client = Groq(api_key=env_dict['GROQ_API_KEY'].strip())
cpp_code = Path('targets/cpp-target/src/cpp_target.cpp').read_text()

system_msg = 'Output JSON: {"root_cause":"...","fix_pattern":"...","patched_full_file":"..."}'
user_msg = f'Fix the CWE-120 buffer overflow in this C++ file:\n```\n{cpp_code}\n```'

print('Testing openai/gpt-oss-20b...')
resp = client.chat.completions.create(
    model='openai/gpt-oss-20b',
    messages=[
        {'role': 'system', 'content': system_msg},
        {'role': 'user', 'content': user_msg},
    ],
    temperature=0.6,
    max_tokens=4096,
)

text = resp.choices[0].message.content
finish = resp.choices[0].finish_reason
usage = resp.usage
print(f'Finish: {finish} | Prompt: {usage.prompt_tokens} | Completion: {usage.completion_tokens}')

# Strip think tags and markdown fencing
stripped = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
stripped = re.sub(r'```(?:json)?', '', stripped).strip()

# Fix common invalid JSON escapes that LLMs produce
# e.g. \0 (invalid in JSON) -> \\0, \' -> \\'
def fix_json_escapes(s):
    # Fix invalid backslash escapes inside JSON strings
    # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    # Everything else (like \0, \', \s, \c, etc.) is invalid
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
                # Invalid escape - double the backslash
                result.append('\\\\')
                result.append(next_char)
                i += 2
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)

fixed = fix_json_escapes(stripped)

# Parse JSON
decoder = json.JSONDecoder()
idx = fixed.find('{')
data, _ = decoder.raw_decode(fixed, idx)
patched = data.get('patched_full_file') or data.get('patched_code')

print(f'\n{"="*60}')
print('SUCCESS! Groq LLM Generated Patch')
print(f'{"="*60}')
print(f'Root Cause: {data["root_cause"]}')
print(f'Fix Pattern: {data["fix_pattern"]}')
print(f'\n--- Patched C++ Source Code ---')
print(patched)

# Save the patched file for comparison
patched_path = Path('targets/cpp-target/src/cpp_target_patched.cpp')
patched_path.write_text(patched, encoding='utf-8')
print(f'\nPatched file saved to: {patched_path}')

# Show diff
print(f'\n--- DIFF: Original vs Patched ---')
original_lines = cpp_code.splitlines()
patched_lines = patched.splitlines()
for i, (orig, patch) in enumerate(zip(original_lines, patched_lines)):
    if orig != patch:
        print(f'  Line {i+1}:')
        print(f'    - {orig}')
        print(f'    + {patch}')
if len(patched_lines) > len(original_lines):
    for i in range(len(original_lines), len(patched_lines)):
        print(f'  Line {i+1} (NEW):')
        print(f'    + {patched_lines[i]}')
