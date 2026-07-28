from pathlib import Path

import pytest
import yaml

from aigit_core.locking import LockError, load_manifest, resolve_lock


def write_manifest(root: Path, extra_top_level: str = "") -> None:
    (root / "prompts").mkdir()
    (root / "prompts" / "system.md").write_text("You are helpful.\n", encoding="utf-8")
    (root / "intelligence.yaml").write_text(
        """
apiVersion: aigit.dev/v1
kind: IntelligenceSystem
metadata:
  name: demo-agent
components:
  main_model:
    kind: model
    provider: openai
    model: gpt-4.1-2025-04-14
    params:
      temperature: 0
  system_prompt:
    kind: prompt
    file: prompts/system.md
    role: system
behavior_keys:
  include:
    - components.*.model
    - components.*.params.*
    - components.*.file_digest
  exclude:
    - metadata.*
"""
        + extra_top_level,
        encoding="utf-8",
    )


def test_load_manifest_rejects_unknown_top_level_keys(tmp_path: Path):
    write_manifest(tmp_path, "unexpected: true\n")

    with pytest.raises(LockError, match="unknown top-level key"):
        load_manifest(tmp_path / "intelligence.yaml")


def test_resolve_lock_hashes_file_components_and_computes_fingerprints(tmp_path: Path):
    write_manifest(tmp_path)

    lock = resolve_lock(tmp_path / "intelligence.yaml")

    assert lock["lockfileVersion"] == 1
    assert lock["components"]["system_prompt"]["file_digest"].startswith("sha256:")
    assert lock["components"]["system_prompt"]["digest"].startswith("sha256:")
    assert lock["exact_fingerprint"].startswith("sha256:")
    assert lock["behavioral_fingerprint"].startswith("sha256:")
    assert lock["snapshot_id"] == lock["exact_fingerprint"]


def test_metadata_change_does_not_change_behavioral_fingerprint(tmp_path: Path):
    write_manifest(tmp_path)
    before = resolve_lock(tmp_path / "intelligence.yaml")
    data = yaml.safe_load((tmp_path / "intelligence.yaml").read_text())
    data["metadata"]["description"] = "new description"
    (tmp_path / "intelligence.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    after = resolve_lock(tmp_path / "intelligence.yaml")

    assert before["exact_fingerprint"] != after["exact_fingerprint"]
    assert before["behavioral_fingerprint"] == after["behavioral_fingerprint"]
