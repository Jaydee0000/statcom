"""Password hashing utility only; authentication endpoints are out of scope."""
from argon2 import PasswordHasher

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)
