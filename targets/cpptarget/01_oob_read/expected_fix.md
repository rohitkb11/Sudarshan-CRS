# Expected fix

Validate that the declared payload length is no larger than the bytes
available after the 2-byte header.

Required invariant:

`length <= size - 2`

Malformed packets should be rejected rather than silently truncated.
