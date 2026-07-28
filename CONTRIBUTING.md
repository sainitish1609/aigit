# Contributing

Thanks for considering a contribution to `aigit`.

## Development setup

```bash
git clone <repo-url> aigit
cd aigit
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
```

## Development principles

- Keep the M1 wedge simple: manifest → lockfile → snapshot → structural diff.
- Prefer deterministic behavior over clever inference.
- Keep measured results separate from hypotheses.
- Do not introduce paid API calls into the default test suite.
- Add tests before implementation for behavior changes.
- Keep the CLI useful offline.

## Testing

Run all tests:

```bash
python -m pytest -q
```

Run a focused test:

```bash
python -m pytest tests/test_locking.py -q
```

## Commit style

Use conventional commits where practical:

- `feat: add schema command`
- `fix: handle missing prompt file`
- `docs: expand quickstart`
- `test: cover metadata-only diff`

## Pull request checklist

Before submitting:

- [ ] Tests pass locally.
- [ ] README/docs updated for user-facing changes.
- [ ] CLI output remains clear and scriptable.
- [ ] New behavior has tests.
- [ ] No secrets or local-only paths committed.

## Release checklist

- [ ] Update `CHANGELOG.md`.
- [ ] Update `RELEASE_NOTES.md`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m build`.
- [ ] Run `python -m twine check dist/*`.
- [ ] Commit changes.
- [ ] Tag release, e.g. `git tag -a v0.1.0 -m "v0.1.0"`.
- [ ] Push `main` and tags.
- [ ] Create GitHub release from `RELEASE_NOTES.md` and attach `dist/*` artifacts.
- [ ] Confirm `.github/workflows/publish-pypi.yml` publishes to PyPI using Trusted Publishing.
