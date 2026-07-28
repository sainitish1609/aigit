# AI Git (`aigit`)

**Git-style behavior versioning for AI systems.**

`aigit` tracks the artifacts that determine AI behavior — models, prompts, retrieval/index config, tools, policies, graders, datasets, and runtime settings — as one declarative system snapshot.

The first release focuses on the M1 wedge:

- one `intelligence.yaml`
- generated `intelligence.lock.json`
- content-addressed component digests
- exact and behavioral fingerprints
- snapshot files
- structural diffs that separate behavior-affecting changes from metadata

## Why this exists

Git answers: **what text changed?**

AI teams usually need: **why did behavior change?**

`aigit` is designed to make silent AI-system drift visible:

- prompt edits
- model alias changes
- decoding parameter changes
- prompt file digest changes
- tool definition changes
- index/corpus digest changes
- behavior-affecting config changes hidden in generated locks

## Current status

`v0.1.0` is an early, local-first MVP.

Implemented:

- `aigit init`
- `aigit lock`
- `aigit snapshot`
- `aigit diff`
- `aigit doctor`
- `aigit schema`
- Pydantic manifest model
- deterministic canonical JSON hashing
- lockfile generation
- snapshot object generation
- structural diff classification
- test suite

Not implemented yet:

- eval runner
- statistical gates
- trace/lineage SDK
- replay modes
- optional server
- GitHub release automation beyond local tagging/workflow scaffolding

## Install from source

```bash
git clone <repo-url> aigit
cd aigit
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Then run:

```bash
aigit --help
```

## Quickstart

```bash
mkdir my-ai-app
cd my-ai-app

aigit init
```

This creates:

```text
intelligence.yaml
prompts/system.md
```

The generated model is intentionally an alias so `doctor` can show the reproducibility warning:

```bash
aigit doctor
```

Example warning:

```text
ERROR  components.main_model.model appears to be a moving alias: gpt-4.1
```

Pin the model in `intelligence.yaml`, for example:

```yaml
model: gpt-4.1-2025-04-14
```

Then create a lockfile and snapshot:

```bash
aigit doctor
aigit lock
aigit snapshot -m "baseline"
```

## Example diff flow

Create a baseline lock:

```bash
aigit lock
cp intelligence.lock.json before.lock.json
```

Change a behavior-affecting field in `intelligence.yaml`:

```yaml
params:
  temperature: 0.3
```

Regenerate and diff:

```bash
aigit lock
aigit diff before.lock.json intelligence.lock.json
```

JSON output:

```bash
aigit diff before.lock.json intelligence.lock.json --format json
```

Example result:

```json
{
  "path": "components.main_model.params.temperature",
  "class": "behavior_affecting",
  "before": 0.2,
  "after": 0.3
}
```

## Commands

### `aigit init`

Scaffolds a minimal AI system manifest.

```bash
aigit init
```

Use `--force` to overwrite an existing scaffold.

### `aigit doctor`

Checks for reproducibility hazards.

Current checks:

- model identifiers that look like moving aliases

```bash
aigit doctor
```

### `aigit lock`

Resolves `intelligence.yaml` into `intelligence.lock.json`.

```bash
aigit lock
```

The lockfile includes:

- component resolved data
- file digests
- component digest
- behavioral digest
- exact fingerprint
- behavioral fingerprint
- snapshot id

### `aigit snapshot`

Creates a snapshot object under `.aigit/snapshots/`.

```bash
aigit snapshot -m "baseline"
```

### `aigit diff`

Compares two lockfiles.

```bash
aigit diff before.lock.json after.lock.json
```

Machine-readable output:

```bash
aigit diff before.lock.json after.lock.json --format json
```

Change classes:

- `behavior_affecting` — model, params, file digest, retrieval/index/tool behavior config
- `metadata` — non-behavioral edits
- `structural` — component added/removed
- `implicit` — digest moved without resolved manifest field changes

### `aigit schema`

Prints the JSON Schema for `intelligence.yaml`.

```bash
aigit schema > intelligence.schema.json
```

## Example `intelligence.yaml`

```yaml
apiVersion: aigit.dev/v1
kind: IntelligenceSystem
metadata:
  name: demo-agent
  owner: platform-team
components:
  main_model:
    kind: model
    provider: openai
    model: gpt-4.1-2025-04-14
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
```

## Development

Run tests:

```bash
python -m pytest -q
```

Run a single test file:

```bash
python -m pytest tests/test_diffing.py -q
```

Check package metadata:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Release process

Local release preparation:

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
git status --short
git tag -a v0.1.0 -m "v0.1.0"
```

If a GitHub remote is configured:

```bash
git push origin main
git push origin v0.1.0
```

Create GitHub release:

```bash
gh release create v0.1.0 --title "v0.1.0" --notes-file RELEASE_NOTES.md dist/aigit-0.1.0-py3-none-any.whl dist/aigit-0.1.0.tar.gz
```

PyPI publishing is handled by `.github/workflows/publish-pypi.yml` when a GitHub release is published. Configure PyPI Trusted Publishing for this repository before the next release:

- PyPI project: `aigit`
- Owner: `sainitish1609`
- Repository: `aigit`
- Workflow: `publish-pypi.yml`
- Environment: `pypi`

## Roadmap

Next feature milestones:

- richer manifest validation and conformance vectors
- markdown diff renderer for PR comments
- GitHub Action for structural diffs
- eval runner with deterministic fake provider
- CEL-based policy gates
- trace lineage SDK

## License

Apache-2.0. See [`LICENSE`](LICENSE).
