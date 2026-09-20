"""Canonical JSON and content digest primitives."""

from __future__ import annotations

import hashlib
import json


class CanonicalJSONError(ValueError):
    """A machine-readable canonicalization rejection."""

    def __init__(self, code: str, message: str, path: str = "$") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path


def _check_value(value: object, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{path}.{key}" if isinstance(key, str) else path
            if not isinstance(key, str):
                raise CanonicalJSONError("NON_STRING_OBJECT_KEY", f"object key at {path} must be a string", path)
            _check_value(item, key_path)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check_value(item, f"{path}[{index}]")


def canonical_json(value: object) -> bytes:
    """Return deterministic UTF-8 JSON bytes for *value*.

    Object keys are recursively required to be strings and are sorted. NaN and
    infinity are rejected rather than emitted as non-standard JSON tokens.
    """

    _check_value(value, "$")
    try:
        return json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        code = "TYPE_INVALID" if isinstance(error, TypeError) else "NON_FINITE_NUMBER"
        raise CanonicalJSONError(code, f"value cannot be represented as canonical JSON: {error}") from error


def sha256_digest(data: bytes) -> str:
    """Return the canonical GAUNTLET SHA-256 digest for exact *data* bytes."""

    return f"sha256:{hashlib.sha256(data).hexdigest()}"
