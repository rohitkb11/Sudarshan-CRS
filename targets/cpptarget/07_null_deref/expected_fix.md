# Expected fix

Check the pointer before dereference and return a safe error/value when it is
null. The `USE_VALUE=1` path should continue to print the configured value.
