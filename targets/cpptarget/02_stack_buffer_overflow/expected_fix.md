# Expected fix

Do not copy attacker-controlled input unboundedly into a 16-byte stack
array.

A good fix is to use `std::string` directly, or enforce a strict maximum
length before copying. Normal names of length <= 15 must still work.
