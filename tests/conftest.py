"""
Pytest session bootstrap — runs before any test module is imported.

Root cause being fixed:
  ingestion/database.py calls load_dotenv() at import time, which reads .env
  and sets AEGIS_USERS_JSON with $$-escaped bcrypt hashes (Docker Compose escaping
  convention). python-dotenv does NOT unescape $$->$, so bcrypt.checkpw fails for
  every user, auth returns 401, and the rate-limit cascade 429s the rest of the suite.

Fix: pre-set the critical env vars using os.environ.setdefault() BEFORE any app
module is imported. load_dotenv() uses override=False by default, so it silently
skips vars that are already set.
"""
import os

os.environ.setdefault("ENV", "development")
# Minimum 32-char key so jwt.py doesn't raise RuntimeError in development mode.
os.environ.setdefault(
    "SECRET_KEY",
    "aegis-ai-test-only-key-not-for-production-xxxxxxxxxxxxxxxxxxxxxxxx",
)
# Empty string is falsy → _load_users() falls back to config/users.json (correct hashes).
# This prevents load_dotenv() from injecting the $$-corrupted hashes from .env.
os.environ.setdefault("AEGIS_USERS_JSON", "")
