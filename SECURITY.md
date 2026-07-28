# Security Policy

## Supported versions

`aigit` is pre-1.0. Security fixes are applied to the latest release only.

## Reporting a vulnerability

Please do not open a public issue for sensitive vulnerabilities.

If a GitHub repository is available, use GitHub's private vulnerability reporting. Otherwise, contact the maintainers directly with:

- affected version or commit
- reproduction steps
- impact
- suggested fix, if known

## Security design goals

- Manifests must not contain secret values.
- Lockfiles and snapshots must not write resolved secret values.
- Local-first behavior must work without accounts or hosted services.
- Future explainer/gate systems must keep untrusted model/corpus text out of authoritative policy decisions.

## Current scope

The current MVP does not call model providers or upload data. Main risks are local file handling, accidental secret inclusion in manifests, and package supply-chain hygiene.
