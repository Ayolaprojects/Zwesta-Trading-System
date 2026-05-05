"""
Credential encryption-at-rest helpers for the broker_credentials table.

Design goals
------------
- Encrypt `api_key` and `password` (broker secret) using Fernet (AES-128-CBC + HMAC).
- Backward compatible: existing plaintext rows are detected (no marker) and
  returned as-is by `decrypt_secret`. New writes always include marker
  prefix `enc:v1:` so a future migration can identify already-encrypted rows.
- Key sourced from env var `CREDENTIALS_ENCRYPTION_KEY`. If unset, a key is
  auto-generated and persisted to a sidecar file next to the DB so that
  development restarts don't lose access. Production deployments MUST set
  the env var explicitly and back it up — losing the key makes credentials
  unrecoverable.
"""
from __future__ import annotations

import base64
import logging
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_MARKER = 'enc:v1:'
_KEY_FILE_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.credentials_key')

_fernet: Optional[Fernet] = None


def _load_or_create_key() -> bytes:
    raw = os.getenv('CREDENTIALS_ENCRYPTION_KEY', '').strip()
    if raw:
        try:
            Fernet(raw.encode())
            return raw.encode()
        except Exception as e:
            logger.error(
                "[CREDENTIAL CRYPTO] CREDENTIALS_ENCRYPTION_KEY is set but invalid: %s. "
                "Generate one with `python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"`.",
                e,
            )
            raise

    key_file = os.getenv('CREDENTIALS_ENCRYPTION_KEY_FILE', _KEY_FILE_DEFAULT)
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            data = f.read().strip()
        try:
            Fernet(data)
            logger.warning(
                "[CREDENTIAL CRYPTO] Using key from sidecar file %s. "
                "For production, set CREDENTIALS_ENCRYPTION_KEY env var instead and back it up.",
                key_file,
            )
            return data
        except Exception:
            logger.error("[CREDENTIAL CRYPTO] Sidecar key file %s is corrupt; regenerating.", key_file)

    key = Fernet.generate_key()
    try:
        with open(key_file, 'wb') as f:
            f.write(key)
        try:
            os.chmod(key_file, 0o600)
        except Exception:
            pass
        logger.warning(
            "[CREDENTIAL CRYPTO] *** GENERATED NEW ENCRYPTION KEY at %s *** "
            "BACK THIS FILE UP. Losing it will make all stored broker credentials "
            "unrecoverable. Better: copy its contents into CREDENTIALS_ENCRYPTION_KEY env var.",
            key_file,
        )
    except Exception as e:
        logger.error(
            "[CREDENTIAL CRYPTO] Failed to persist generated key to %s: %s.",
            key_file,
            e,
        )
    return key


def _get_cipher() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    if plaintext is None:
        return None
    s = str(plaintext)
    if not s:
        return s
    if s.startswith(_MARKER):
        return s
    token = _get_cipher().encrypt(s.encode('utf-8')).decode('ascii')
    return _MARKER + token


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value)
    if not s.startswith(_MARKER):
        return s
    token = s[len(_MARKER):]
    try:
        return _get_cipher().decrypt(token.encode('ascii')).decode('utf-8')
    except InvalidToken:
        logger.error(
            "[CREDENTIAL CRYPTO] Failed to decrypt a secret — encryption key may have changed."
        )
        return ''


SENSITIVE_FIELDS = ('api_key', 'password')


def decrypt_credential_row(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    try:
        d = dict(row)
    except Exception:
        d = {k: row[k] for k in row.keys()} if hasattr(row, 'keys') else {}
    for field in SENSITIVE_FIELDS:
        if field in d and d[field] is not None:
            d[field] = decrypt_secret(d[field])
    return d


def decrypt_credential_rows(rows):
    return [decrypt_credential_row(r) for r in (rows or [])]

# ==================== Transparent decrypting row factory ====================
class _DecryptedRow:
    """Row-like object that auto-decrypts any string value carrying the
    encryption marker. Supports both string-key (`row['col']`) and integer
    (`row[0]`) access, and is convertible via `dict(row)`.
    """
    __slots__ = ('_cols', '_vals', '_map')

    def __init__(self, cols, vals):
        self._cols = cols
        self._vals = vals
        self._map = dict(zip(cols, vals))

    def keys(self):
        return self._cols

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return self._map[key]

    def get(self, key, default=None):
        return self._map.get(key, default)

    def __iter__(self):
        return iter(self._vals)

    def __len__(self):
        return len(self._vals)

    def __contains__(self, key):
        return key in self._map

    def __repr__(self):
        return f"<_DecryptedRow {self._map!r}>"


def decrypting_row_factory(cursor, row_tuple):
    """sqlite3 row_factory that returns rows with `enc:v1:` values auto-decrypted.

    Marker-based detection means the factory is safe on any table — non-secret
    columns are passed through untouched.
    """
    cols = [c[0] for c in cursor.description]
    out_vals = []
    for v in row_tuple:
        if isinstance(v, str) and v.startswith(_MARKER):
            try:
                v = decrypt_secret(v)
            except Exception:
                pass
        out_vals.append(v)
    return _DecryptedRow(cols, out_vals)
