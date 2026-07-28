from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BEHAVIOR_FIELDS = {
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


def load_lock(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, path))
        return out
    return {prefix: value}


def _classify_field(field_path: str) -> str:
    last = field_path.split(".")[-1]
    if last in {"digest", "behavioral_digest"}:
        return "implicit"
    if any(part in BEHAVIOR_FIELDS for part in field_path.split(".")):
        return "behavior_affecting"
    return "metadata"


def _markdown_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        rendered = json.dumps(value, sort_keys=True)
    else:
        rendered = str(value)
    rendered = rendered.replace("`", "\\`").replace("|", "\\|").replace("\n", " ")
    return f"`{rendered}`"


def render_markdown_diff(result: dict[str, Any]) -> str:
    summary = result.get("summary", {})
    lines = [
        "## aigit diff",
        "",
        (
            f"**Summary:** {summary.get('total_changes', 0)} total; "
            f"{summary.get('behavior_affecting', 0)} behavior-affecting; "
            f"{summary.get('structural', 0)} structural; "
            f"{summary.get('metadata', 0)} metadata; "
            f"{summary.get('implicit', 0)} implicit."
        ),
        "",
    ]
    changes = result.get("structural", [])
    if changes:
        lines.extend([
            "| Path | Class | Change | Before | After |",
            "| --- | --- | --- | --- | --- |",
        ])
        for change in changes:
            lines.append(
                "| {path} | {class_} | {change} | {before} | {after} |".format(
                    path=str(change.get("path", "")).replace("|", "\\|"),
                    class_=str(change.get("class", "")).replace("|", "\\|"),
                    change=str(change.get("change", "")).replace("|", "\\|"),
                    before=_markdown_value(change.get("before")),
                    after=_markdown_value(change.get("after")),
                )
            )
        lines.append("")
    else:
        lines.extend(["No structural changes detected.", ""])

    measured = result.get("measured", {})
    if measured.get("available"):
        lines.append("Measured diff available.")
    else:
        lines.append(f"Measured diff unavailable — {measured.get('reason', 'not provided')}.")
    return "\n".join(lines) + "\n"


def diff_locks(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    before_components = before.get("components", {})
    after_components = after.get("components", {})

    for name in sorted(set(before_components) | set(after_components)):
        if name not in before_components:
            changes.append({
                "path": f"components.{name}",
                "kind": after_components[name].get("kind"),
                "change": "added",
                "class": "structural",
                "before": None,
                "after": after_components[name].get("resolved", after_components[name]),
            })
            continue
        if name not in after_components:
            changes.append({
                "path": f"components.{name}",
                "kind": before_components[name].get("kind"),
                "change": "removed",
                "class": "structural",
                "before": before_components[name].get("resolved", before_components[name]),
                "after": None,
            })
            continue

        before_resolved = before_components[name].get("resolved", {})
        after_resolved = after_components[name].get("resolved", {})
        before_flat = _flatten(before_resolved)
        after_flat = _flatten(after_resolved)
        for field in sorted(set(before_flat) | set(after_flat)):
            old = before_flat.get(field)
            new = after_flat.get(field)
            if old == new:
                continue
            changes.append({
                "path": f"components.{name}.{field}",
                "kind": after_components[name].get("kind") or before_components[name].get("kind"),
                "change": "modified",
                "class": _classify_field(field),
                "before": old,
                "after": new,
            })

        if before_resolved == after_resolved:
            for digest_field in ["digest", "behavioral_digest"]:
                if before_components[name].get(digest_field) != after_components[name].get(digest_field):
                    changes.append({
                        "path": f"components.{name}.{digest_field}",
                        "kind": after_components[name].get("kind") or before_components[name].get("kind"),
                        "change": "modified",
                        "class": "implicit",
                        "before": before_components[name].get(digest_field),
                        "after": after_components[name].get(digest_field),
                    })

    for fingerprint_field in ["exact_fingerprint", "behavioral_fingerprint"]:
        if before.get(fingerprint_field) != after.get(fingerprint_field):
            changes.append({
                "path": fingerprint_field,
                "kind": "lockfile",
                "change": "modified",
                "class": "implicit",
                "before": before.get(fingerprint_field),
                "after": after.get(fingerprint_field),
            })

    return {
        "structural": changes,
        "measured": {
            "available": False,
            "reason": "no evaluation records available for one or both snapshots",
        },
        "summary": {
            "total_changes": len(changes),
            "behavior_affecting": sum(1 for c in changes if c["class"] == "behavior_affecting"),
            "metadata": sum(1 for c in changes if c["class"] == "metadata"),
            "structural": sum(1 for c in changes if c["class"] == "structural"),
            "implicit": sum(1 for c in changes if c["class"] == "implicit"),
        },
    }
