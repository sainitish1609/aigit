from typer.testing import CliRunner

from aigit_cli.main import app

runner = CliRunner()


def test_schema_command_outputs_manifest_schema():
    result = runner.invoke(app, ["schema"])

    assert result.exit_code == 0
    assert '"title": "IntelligenceManifest"' in result.output
