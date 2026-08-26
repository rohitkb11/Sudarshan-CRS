# Expected fix

The program must reject any `length > 16` before reading into the 16-byte
allocation, or instead allocate storage based on a safely validated length.

Do not merely suppress the sanitizer symptom.
