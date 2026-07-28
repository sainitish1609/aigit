# GitHub Actions usage

`aigit` can run in CI to keep `intelligence.lock.json` in sync and to render lockfile diffs for pull requests.

## Check that the lockfile is current

Add this workflow to a repository that contains an `intelligence.yaml` and committed `intelligence.lock.json`:

```yaml
name: aigit lock check

on:
  pull_request:
  push:
    branches: [main]

jobs:
  lock-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install aigit from source
        run: python -m pip install git+https://github.com/sainitish1609/aigit.git
      - name: Verify intelligence.lock.json
        run: aigit lock --check
```

`aigit lock --check` exits non-zero when the committed lockfile is stale. The check compares the desired lockfile while ignoring volatile `generated_at` drift.

## Render a markdown diff in pull requests

The `markdown` diff format is suitable for PR summaries or bot comments:

```yaml
name: aigit PR diff

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  diff:
    runs-on: ubuntu-latest
    steps:
      - name: Check out PR head
        uses: actions/checkout@v4
        with:
          path: head
      - name: Check out base branch
        uses: actions/checkout@v4
        with:
          ref: ${{ github.base_ref }}
          path: base
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install aigit from source
        run: python -m pip install git+https://github.com/sainitish1609/aigit.git
      - name: Build base lockfile
        working-directory: base
        run: aigit lock
      - name: Build PR lockfile
        working-directory: head
        run: aigit lock
      - name: Render aigit diff
        run: |
          aigit diff base/intelligence.lock.json head/intelligence.lock.json --format markdown > aigit-diff.md
          cat aigit-diff.md >> "$GITHUB_STEP_SUMMARY"
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('aigit-diff.md', 'utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body,
            });
```

For other install methods, replace the source install command with the command your project uses.

## Recommended repository policy

- Commit both `intelligence.yaml` and `intelligence.lock.json`.
- Run `aigit doctor` before `aigit lock --check` if you want CI to reject moving model aliases.
- Use `aigit diff --format markdown` in PR workflows so reviewers can see behavior-affecting, structural, metadata, and implicit fingerprint changes.
