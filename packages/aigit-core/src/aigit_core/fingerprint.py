from __future__ import annotations

import hashlib
import json
import unicodedata
from decimal import Decimal
from typing import Any


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): _normalize(value[key])
            for key in sorted(value.keys(), key=lambda k: str(k))
        }
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def canonical_json(value: Any) -> bytes:
    """Return stable canonical JSON bytes for hashing.

    This is the v0 implementation aligned with the design goal: sorted keys,
    no insignificant whitespace, UTF-8 bytes, and NFC-normalized strings.
    Full RFC 8785 number conformance will be covered by conformance vectors.
    """

    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()
