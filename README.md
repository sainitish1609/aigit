# AI Git (`aigit`)

`aigit` versions AI system behavior using a human-edited `intelligence.yaml`, a generated lockfile, content-addressed snapshots, and structural diffs.

Current implementation focus: M0/M1 wedge.

## Commands

```bash
aigit init
aigit lock
aigit snapshot -m "baseline"
aigit diff intelligence.lock.json .aigit/snapshots/<id>.json
aigit doctor
```
