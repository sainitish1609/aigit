from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def create_snapshot(lock_path: Path | str, message: str = "") -> dict[str, Any]:
    path = Path(lock_path)
    lock = json.loads(path.read_text(encoding="utf-8"))
    snapshot = {
        "schema": "aigit.dev/v1/Snapshot",
        "snapshot_id": lock["snapshot_id"],
        "message": message,
        "components": {
            name: {
                "kind": component.get("kind"),
                "digest": component.get("digest"),
                "behavioral_digest": component.get("behavioral_digest"),
            }
            for name, component in lock.get("components", {}).items()
        },
        "environment": lock.get("environment", {}),
        "exact_fingerprint": lock["exact_fingerprint"],
        "behavioral_fingerprint": lock["behavioral_fingerprint"],
    }
    out_dir = path.parent / ".aigit" / "snapshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = lock["snapshot_id"].replace(":", "-")
    out_path = out_dir / f"{safe_id}.json"
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    snapshot["path"] = str(out_path)
    return snapshot
