import json
import os
from pathlib import Path

from typer.testing import CliRunner

from aigit_cli.main import app

runner = CliRunner()


def invoke_in(cwd: Path, args: list[str]):
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, args)
    finally:
        os.chdir(previous)


def test_init_writes_manifest(tmp_path: Path):
    result = invoke_in(tmp_path, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / "intelligence.yaml").exists()
    assert "Wrote intelligence.yaml" in result.output


def test_lock_writes_lockfile(tmp_path: Path):
    invoke_in(tmp_path, ["init"])

    result = invoke_in(tmp_path, ["lock"])

    assert result.exit_code == 0
    lock = json.loads((tmp_path / "intelligence.lock.json").read_text())
    assert lock["snapshot_id"].startswith("sha256:")


def test_lock_check_ignores_generated_at_drift_and_does_not_rewrite(tmp_path: Path):
    invoke_in(tmp_path, ["init"])
    invoke_in(tmp_path, ["lock"])
    lock_path = tmp_path / "intelligence.lock.json"
    lock = json.loads(lock_path.read_text())
    lock["generated_at"] = "2000-01-01T00:00:00Z"
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = invoke_in(tmp_path, ["lock", "--check"])

    assert result.exit_code == 0
    assert "up to date" in result.output
    assert json.loads(lock_path.read_text())["generated_at"] == "2000-01-01T00:00:00Z"


def test_lock_check_fails_for_stale_lock_without_rewriting(tmp_path: Path):
    invoke_in(tmp_path, ["init"])
    invoke_in(tmp_path, ["lock"])
    lock_path = tmp_path / "intelligence.lock.json"
    before = lock_path.read_text()
    manifest_path = tmp_path / "intelligence.yaml"
    manifest_path.write_text(
        manifest_path.read_text().replace("temperature: 0.2", "temperature: 0.7"),
        encoding="utf-8",
    )

    result = invoke_in(tmp_path, ["lock", "--check"])

    assert result.exit_code == 1
    assert "stale" in result.output
    assert lock_path.read_text() == before


def test_snapshot_writes_snapshot_object(tmp_path: Path):
    invoke_in(tmp_path, ["init"])
    invoke_in(tmp_path, ["lock"])

    result = invoke_in(tmp_path, ["snapshot", "-m", "baseline"])

    assert result.exit_code == 0
    assert "snapshot" in result.output
    snapshots = list((tmp_path / ".aigit" / "snapshots").glob("*.json"))
    assert len(snapshots) == 1


def test_diff_renders_json(tmp_path: Path):
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps({"components": {}}), encoding="utf-8")
    after.write_text(json.dumps({"components": {"x": {"kind": "tool", "resolved": {}}}}), encoding="utf-8")

    result = invoke_in(tmp_path, ["diff", str(before), str(after), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["total_changes"] == 1


def test_diff_renders_markdown(tmp_path: Path):
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(
        json.dumps({"components": {"x": {"kind": "model", "resolved": {"kind": "model", "model": "m1"}}}}),
        encoding="utf-8",
    )
    after.write_text(
        json.dumps({"components": {"x": {"kind": "model", "resolved": {"kind": "model", "model": "m2"}}}}),
        encoding="utf-8",
    )

    result = invoke_in(tmp_path, ["diff", str(before), str(after), "--format", "markdown"])

    assert result.exit_code == 0
    assert result.output.startswith("## aigit diff")
    assert "| components.x.model | behavior_affecting | modified | `m1` | `m2` |" in result.output


def test_doctor_detects_model_alias(tmp_path: Path):
    invoke_in(tmp_path, ["init"])

    result = invoke_in(tmp_path, ["doctor"])

    assert result.exit_code == 1
    assert "moving alias" in result.output
