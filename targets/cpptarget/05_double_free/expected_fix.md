# Expected fix

Ensure each allocation is released exactly once. A robust repair can use
RAII (`std::unique_ptr<int[]>`) or make ownership explicit and prevent a
second deletion.
