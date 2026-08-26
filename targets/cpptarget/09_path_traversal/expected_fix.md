# Expected fix

The requested file must remain inside the intended `sandbox_files` directory.

A robust solution should normalize/canonicalize the candidate path and verify
that it remains under the trusted base before opening it. Do not rely only on
removing `"../"` substrings.
