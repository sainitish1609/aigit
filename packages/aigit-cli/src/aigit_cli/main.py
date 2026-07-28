from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from aigit_core.diffing import diff_locks, load_lock
from aigit_core.locking import LockError, load_manifest, write_lock
from aigit_core.models import json_schema
from aigit_core.snapshot import create_snapshot

app = typer.Typer(help="Version AI system behavior with manifests, locks, snapshots, and diffs.")
console = Console()

DEFAULT_MANIFEST = """apiVersion: aigit.dev/v1
kind: IntelligenceSystem
metadata:
  name: demo-agent
  owner: unknown
components:
  main_model:
    kind: model
    provider: openai
    model: gpt-4.1
    params:
      temperature: 0.2
      max_tokens: 1024
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
environment:
  runtime: python==3.11.*
"""


def _manifest_path(path: str) -> Path:
    return Path(path).resolve()


@app.command()
def init(force: bool = typer.Option(False, "--force", help="Overwrite existing intelligence.yaml.")) -> None:
    """Scaffold an intelligence.yaml and minimal prompt file."""

    manifest = Path("intelligence.yaml")
    if manifest.exists() and not force:
        console.print("intelligence.yaml already exists; use --force to overwrite")
        raise typer.Exit(1)
    Path("prompts").mkdir(exist_ok=True)
    prompt = Path("prompts/system.md")
    if not prompt.exists() or force:
        prompt.write_text("You are a helpful AI assistant.\n", encoding="utf-8")
    manifest.write_text(DEFAULT_MANIFEST, encoding="utf-8")
    console.print("Wrote intelligence.yaml")
    console.print("Next: aigit lock && aigit snapshot -m 'baseline'")


@app.command()
def lock(
    manifest: str = typer.Option("intelligence.yaml", "--manifest", "-f"),
    check: bool = typer.Option(False, "--check", help="Fail if intelligence.lock.json would change."),
) -> None:
    """Resolve intelligence.yaml into intelligence.lock.json."""

    try:
        lock_data = write_lock(_manifest_path(manifest))
    except LockError as exc:
        console.print(f"ERROR  {exc}")
        raise typer.Exit(1) from exc
    if check:
        existing = Path("intelligence.lock.json")
        if not existing.exists() or json.loads(existing.read_text()) != lock_data:
            console.print("ERROR  intelligence.lock.json is stale")
            raise typer.Exit(1)
    console.print(f"✓ intelligence.lock.json written ({len(lock_data['components'])} components)")
    console.print(f"snapshot {lock_data['snapshot_id']}")


@app.command()
def snapshot(message: str = typer.Option("", "--message", "-m"), lockfile: str = "intelligence.lock.json") -> None:
    """Create a small immutable snapshot object from the lockfile."""

    snap = create_snapshot(lockfile, message=message)
    console.print(f"✓ snapshot {snap['snapshot_id']}")
    console.print(str(snap["path"]))


@app.command()
def diff(before: str, after: str, format: str = typer.Option("human", "--format")) -> None:
    """Render a structural diff between two lockfiles."""

    result = diff_locks(load_lock(before), load_lock(after))
    if format == "json":
        console.print(json.dumps(result, indent=2, sort_keys=True))
        return
    table = Table(title="STRUCTURAL")
    table.add_column("Path")
    table.add_column("Class")
    table.add_column("Before")
    table.add_column("After")
    for change in result["structural"]:
        table.add_row(change["path"], change["class"], str(change["before"]), str(change["after"]))
    console.print(table)
    console.print(f"MEASURED unavailable — {result['measured']['reason']}")


@app.command()
def schema() -> None:
    """Print the v1 intelligence.yaml JSON Schema."""

    console.print(json.dumps(json_schema(), indent=2, sort_keys=True))


@app.command()
def doctor(manifest: str = typer.Option("intelligence.yaml", "--manifest", "-f")) -> None:
    """Check for obvious reproducibility hazards."""

    try:
        data = load_manifest(_manifest_path(manifest))
    except LockError as exc:
        console.print(f"ERROR  {exc}")
        raise typer.Exit(1) from exc
    failures = 0
    for name, component in data.get("components", {}).items():
        if component.get("kind") == "model":
            model = str(component.get("model", ""))
            if not re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", model):
                console.print(f"ERROR  components.{name}.model appears to be a moving alias: {model}")
                failures += 1
    if failures:
        raise typer.Exit(1)
    console.print("✓ doctor passed")


if __name__ == "__main__":
    app()
