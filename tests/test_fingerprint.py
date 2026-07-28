from aigit_core.fingerprint import canonical_json, sha256_digest


def test_canonical_json_sorts_keys_and_removes_whitespace():
    assert canonical_json({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


def test_canonical_json_normalizes_unicode_to_nfc():
    decomposed = "Cafe\u0301"
    composed = "Caf\u00e9"
    assert canonical_json({"name": decomposed}) == canonical_json({"name": composed})


def test_sha256_digest_uses_canonical_json_and_sha256_prefix():
    assert sha256_digest({"b": 2, "a": 1}) == "sha256:43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
