# Expected fix

Never dereference `item` after `delete`.

Prefer restructuring ownership/use order or RAII/smart pointers so a dangling
raw pointer cannot be used.
