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


def test_diff_reports_component_digest_changes_as_implicit_when_resolved_payload_matches():
    before = base_lock()
    after = base_lock()
    after["components"]["prompt"]["digest"] = "sha256:new"

    result = diff_locks(before, after)

    assert result["structural"] == [
        {
            "path": "components.prompt.digest",
            "kind": "prompt",
            "change": "modified",
            "class": "implicit",
            "before": "sha256:p",
            "after": "sha256:new",
        }
    ]
    assert result["summary"]["implicit"] == 1


def test_diff_reports_top_level_fingerprint_changes_as_implicit():
    before = base_lock()
    after = base_lock()
    after["exact_fingerprint"] = "sha256:exact2"
    after["behavioral_fingerprint"] = "sha256:beh2"

    result = diff_locks(before, after)

    assert [change["path"] for change in result["structural"]] == [
        "exact_fingerprint",
        "behavioral_fingerprint",
    ]
    assert {change["class"] for change in result["structural"]} == {"implicit"}
    assert result["summary"]["implicit"] == 2
