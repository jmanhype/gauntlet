# GAUNTLET canonical repository migration

This checkout is the canonical GAUNTLET workspace.

Legacy source checkout preserved read-only for recovery:

```text
/Users/speed/Downloads/AI_Videos/google-usercontent/gauntlet
```

The legacy checkout used a nested bare remote under its own `.git` directory.
This repository replaces that with a normal GitHub remote while preserving the
legacy remote as `legacy-local` for recovery.

## Migration rules

- Do not delete the legacy checkout until this repository is fully pushed and
  its backlog is restored.
- All future GAUNTLET work happens here.
- The live nd vault is branch-independent under:

```text
.git/paivot/nd-vault
```

- The durable backlog snapshot remains on `nd/backlog`.
