# Expected fix

Treat the input as data, not a format string.

Use:

`std::printf("%s", message.c_str());`

Ordinary text should retain the same visible output.
