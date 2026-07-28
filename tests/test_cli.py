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


def test_snapshot_writes_snapshot_object(tmp_path: Path):
    invoke_in(tmp_path, ["init"])
    invoke_in(tmp_path, ["lock"])

    result = invoke_in(tmp_path, ["snapshot", "-m", "baseline"])

    assert result.exit_code == 0
    assert "snapshot" in result.output
    snapshots = list((tmp_path / ".aigit" / "snapshots").glob("*.json"))
    assert len(snapshots) == 1


def test_doctor_detects_model_alias(tmp_path: Path):
    invoke_in(tmp_path, ["init"])

    result = invoke_in(tmp_path, ["doctor"])

    assert result.exit_code == 1
    assert "moving alias" in result.output
