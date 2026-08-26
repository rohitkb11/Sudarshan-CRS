# Expected fix

Perform checked arithmetic before `count * sizeof(uint32_t)`.

A robust repair should reject values that exceed the maximum representable
allocation size, ideally using `size_t` and a guard such as:

`count <= SIZE_MAX / sizeof(uint32_t)`

The calculation must not wrap.
