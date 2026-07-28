from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .fingerprint import sha256_digest
from .models import IntelligenceManifest


class LockError(ValueError):
    pass


def load_manifest(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise LockError("manifest must be a mapping")
    try:
        IntelligenceManifest.model_validate(data)
    except ValidationError as exc:
        unknown = [err for err in exc.errors() if err.get("type") == "extra_forbidden"]
        if unknown:
            keys = ", ".join(str(err["loc"][0]) for err in unknown)
            raise LockError(f"unknown top-level key(s): {keys}") from exc
        raise LockError(str(exc)) from exc
    return data


def _file_digest(root: Path, relative: str) -> str:
    file_path = (root / relative).resolve()
    try:
        content = file_path.read_bytes()
    except FileNotFoundError as exc:
        raise LockError(f"referenced file not found: {relative}") from exc
    return "sha256:" + __import__("hashlib").sha256(content).hexdigest()


def _resolve_component(root: Path, component: dict[str, Any]) -> dict[str, Any]:
    resolved = deepcopy(component)
    if "file" in resolved:
        resolved["file_digest"] = _file_digest(root, resolved["file"])
    if "definitions" in resolved:
        # M1 keeps glob expansion deterministic and lightweight.
        files = sorted(root.glob(str(resolved["definitions"])))
        resolved["definition_digests"] = {
            str(path.relative_to(root)): _file_digest(root, str(path.relative_to(root)))
            for path in files
            if path.is_file()
        }
    return resolved


def _behavior_value(component: dict[str, Any]) -> dict[str, Any]:
    keys = {
        "kind",
        "provider",
        "model",
        "params",
        "file_digest",
        "top_k",
        "embedding",
        "corpus",
        "chunking",
        "strategy",
        "rerank",
        "filters",
        "definitions",
        "definition_digests",
        "side_effects",
        "timeout_ms",
    }
    return {key: deepcopy(value) for key, value in component.items() if key in keys}


def _git_output(root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_metadata(root: Path) -> dict[str, Any] | None:
    repo_root = _git_output(root, ["rev-parse", "--show-toplevel"])
    if not repo_root:
        return None
    commit = _git_output(root, ["rev-parse", "HEAD"])
    branch = _git_output(root, ["branch", "--show-current"])
    porcelain = _git_output(root, ["status", "--porcelain"])
    return {
        "root": str(Path(repo_root).resolve()),
        "commit": commit,
        "branch": branch or None,
        "is_dirty": bool(porcelain),
    }


def resolve_lock(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    root = manifest_path.parent
    manifest = load_manifest(manifest_path)

    components: dict[str, Any] = {}
    behavioral_components: dict[str, Any] = {}
    for name, component in sorted(manifest["components"].items()):
        if not isinstance(component, dict):
            raise LockError(f"component {name} must be a mapping")
        resolved = _resolve_component(root, component)
        digest = sha256_digest(resolved)
        behavioral = _behavior_value(resolved)
        behavioral_digest = sha256_digest(behavioral)
        components[name] = {
            "kind": resolved.get("kind"),
            "resolved": resolved,
            **({"file_digest": resolved["file_digest"]} if "file_digest" in resolved else {}),
            **({"definition_digests": resolved["definition_digests"]} if "definition_digests" in resolved else {}),
            "digest": digest,
            "behavioral_digest": behavioral_digest,
        }
        behavioral_components[name] = {
            "kind": resolved.get("kind"),
            "behavioral": behavioral,
            "behavioral_digest": behavioral_digest,
        }

    exact_payload = {
        "apiVersion": manifest["apiVersion"],
        "metadata": manifest.get("metadata", {}),
        "components": components,
        "evaluation": manifest.get("evaluation", {}),
        "environment": manifest.get("environment", {}),
    }
    behavioral_payload = {
        "components": behavioral_components,
        "evaluation_graders": (manifest.get("evaluation") or {}).get("graders", {}),
        "environment": manifest.get("environment", {}),
    }
    exact_fingerprint = sha256_digest(exact_payload)
    behavioral_fingerprint = sha256_digest(behavioral_payload)
    lock = {
        "lockfileVersion": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator": "aigit 0.1.0",
        "snapshot_id": exact_fingerprint,
        "exact_fingerprint": exact_fingerprint,
        "behavioral_fingerprint": behavioral_fingerprint,
        "components": components,
        "environment": manifest.get("environment", {}),
    }
    git = git_metadata(root)
    if git is not None:
        lock["git"] = git
    return lock


def write_lock(manifest_path: Path | str, output_path: Path | str | None = None) -> dict[str, Any]:
    lock = resolve_lock(manifest_path)
    out = Path(output_path) if output_path else Path(manifest_path).with_name("intelligence.lock.json")
    out.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock
