# Changelog

All notable changes to `aigit` will be documented in this file.

The project follows semantic versioning once the public API stabilizes. Pre-1.0 releases may change CLI output and lockfile details while the spec is being hardened.

## v0.1.0

Initial local-first MVP.

### Added

- `aigit init` command for scaffolding `intelligence.yaml` and a prompt file.
- `aigit lock` command for resolving manifests into `intelligence.lock.json`.
- `aigit snapshot` command for writing snapshot objects under `.aigit/snapshots/`.
- `aigit diff` command for structural lockfile diffs.
- `aigit doctor` command for model-alias reproducibility warnings.
- `aigit schema` command for JSON Schema output.
- Canonical JSON hashing helper.
- Component digests and behavioral digests.
- Exact and behavioral fingerprints.
- Pydantic manifest models.
- Test suite covering fingerprinting, locking, diffing, CLI behavior, and schema generation.

### Known limitations

- No eval runner yet.
- No CEL gates yet.
- No lineage SDK yet.
- No replay support yet.
- Alias detection is heuristic and intentionally conservative.
- Canonical JSON number formatting is a v0 implementation and will need conformance vectors before a frozen spec.
