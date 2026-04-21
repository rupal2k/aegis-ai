"""User store — loads from config/users.json, verifies with bcrypt."""
import json
import os
import bcrypt

_USERS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "users.json"
)


def _load_users() -> dict:
    with open(_USERS_FILE) as f:
        return {u["email"]: u for u in json.load(f)}


def authenticate_user(email: str, password: str) -> dict | None:
    users = _load_users()
    user = users.get(email.lower().strip())
    if not user:
        return None
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return None
    return user
