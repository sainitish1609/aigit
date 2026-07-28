from aigit_core.diffing import diff_locks


def base_lock():
    return {
        "components": {
            "main_model": {
                "kind": "model",
                "resolved": {"kind": "model", "model": "m1", "params": {"temperature": 0}},
                "digest": "sha256:a",
                "behavioral_digest": "sha256:ba",
            },
            "prompt": {
                "kind": "prompt",
                "resolved": {"kind": "prompt", "file": "p.md", "file_digest": "sha256:p1"},
                "file_digest": "sha256:p1",
                "digest": "sha256:p",
                "behavioral_digest": "sha256:bp",
            },
        },
        "exact_fingerprint": "sha256:exact1",
        "behavioral_fingerprint": "sha256:beh1",
    }


def test_diff_classifies_behavior_affecting_field_changes():
    before = base_lock()
    after = base_lock()
    after["components"]["main_model"]["resolved"]["model"] = "m2"

    result = diff_locks(before, after)

    assert result["structural"][0]["path"] == "components.main_model.model"
    assert result["structural"][0]["class"] == "behavior_affecting"


def test_diff_classifies_component_added_as_structural():
    before = base_lock()
    after = base_lock()
    after["components"]["tool"] = {
        "kind": "tool",
        "resolved": {"kind": "tool", "definitions": "tools/*.json"},
        "digest": "sha256:t",
        "behavioral_digest": "sha256:bt",
    }

    result = diff_locks(before, after)

    assert result["structural"][0]["path"] == "components.tool"
    assert result["structural"][0]["class"] == "structural"
    assert result["structural"][0]["change"] == "added"


def test_diff_reports_measured_unavailable_when_no_evaluations():
    result = diff_locks(base_lock(), base_lock())

    assert result["measured"]["available"] is False
    assert "no evaluation" in result["measured"]["reason"]
