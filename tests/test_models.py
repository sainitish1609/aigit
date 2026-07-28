import json

import pytest
from pydantic import ValidationError

from aigit_core.models import IntelligenceManifest, json_schema


def test_manifest_model_accepts_plugin_component_fields():
    manifest = IntelligenceManifest.model_validate(
        {
            "apiVersion": "aigit.dev/v1",
            "kind": "IntelligenceSystem",
            "metadata": {"name": "demo"},
            "components": {
                "custom": {
                    "kind": "plugin_kind",
                    "plugin_specific": {"x": 1},
                }
            },
        }
    )

    assert manifest.components["custom"].kind == "plugin_kind"
    assert manifest.components["custom"].extra_fields["plugin_specific"] == {"x": 1}


def test_manifest_model_rejects_unknown_top_level_keys():
    with pytest.raises(ValidationError):
        IntelligenceManifest.model_validate(
            {
                "apiVersion": "aigit.dev/v1",
                "kind": "IntelligenceSystem",
                "metadata": {"name": "demo"},
                "components": {"m": {"kind": "model"}},
                "unexpected": True,
            }
        )


def test_json_schema_contains_intelligence_system_title():
    schema = json_schema()

    assert schema["title"] == "IntelligenceManifest"
    assert "components" in json.dumps(schema)
