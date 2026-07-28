# Release Notes — v0.1.0

`aigit` v0.1.0 is the first local-first MVP for AI system behavior versioning.

## Highlights

- Scaffold an AI system manifest with `aigit init`.
- Resolve manifest state into `intelligence.lock.json` with `aigit lock`.
- Create content-addressed snapshot objects with `aigit snapshot`.
- Compare lockfiles with `aigit diff`.
- Detect likely moving model aliases with `aigit doctor`.
- Export the manifest JSON Schema with `aigit schema`.

## What this release is good for

- Early experimentation with the AI-behavior-versioning workflow.
- Reviewing how prompt/model/config changes appear in lockfiles.
- Building the structural-diff PR-comment wedge.
- Creating the foundation for evals, gates, lineage, and replay.

## Not ready yet

- Production CI gates.
- Hosted/team server usage.
- Eval datasets and grader calibration.
- Trace lineage and replay.
- Frozen fingerprint conformance guarantees.

## Verify locally

```bash
python -m pytest -q
```

Expected result for this release:

```text
17 passed
```
