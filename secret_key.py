"""Which key signs the session cookies (owner: B). Same idea as in our I2P project.

A student's "My tickets" list lives in their session cookie, signed with this key so nobody
can edit it to see other people's orders. The app uses, in this order:
1. the SECRET_KEY environment variable, if it is set (for a real deployment), or
2. a random key made once and kept in instance/secret_key (git ignores instance/).

choose_secret_key() is plain Python with no Flask, so it is easy to test.
"""

import secrets

KEY_FILE = "secret_key"
MIN_KEY_LENGTH = 32


def new_key():
    """A long random key (64 hex characters)."""
    return secrets.token_hex(32)


def choose_secret_key(env_value, saved_value):
    """Return (key, must_save). must_save is True when a new key was made."""
    if env_value and env_value.strip():
        return env_value.strip(), False
    if saved_value and len(saved_value.strip()) >= MIN_KEY_LENGTH:
        return saved_value.strip(), False
    return new_key(), True
