# PyPI Publishing

`aigit` publishes to PyPI through GitHub Actions Trusted Publishing.

## One-time PyPI setup

Create or claim the PyPI project named `aigit`, then configure Trusted Publishing:

- PyPI project: `aigit`
- GitHub owner: `sainitish1609`
- GitHub repository: `aigit`
- Workflow filename: `publish-pypi.yml`
- Environment name: `pypi`

The workflow uses OpenID Connect (`id-token: write`) and does not require a long-lived PyPI API token.

## Release flow

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file RELEASE_NOTES.md dist/*
```

Publishing the GitHub release triggers `.github/workflows/publish-pypi.yml`.

## Manual retry

If a release publish fails after PyPI Trusted Publishing is fixed:

```bash
gh workflow run publish-pypi.yml --ref main
```

## Validation

The workflow runs:

```bash
python -m pytest -q
python -m build
python -m twine check dist/*
```

before publishing.
