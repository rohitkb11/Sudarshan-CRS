# Expected fix

Do not concatenate untrusted input into a shell command.

Prefer a direct C++ API. If a subprocess is genuinely required, use an API
that passes arguments without invoking a shell and validate the argument.

The repair should preserve ordinary echo-like functionality while preventing
shell interpretation of attacker-controlled characters.
