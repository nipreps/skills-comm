# Nipoppy Pipeline Authoring Commands: `create`, `validate`, `upload`

These commands support building and publishing new pipeline configurations.
Use them when developing a pipeline to share with the community via Zenodo.

Typical workflow: `create` → edit config files → `validate` → `upload`

---

## `nipoppy pipeline create`

Scaffold a new pipeline config directory from a template, optionally seeded from
an existing Boutiques descriptor.

### Synopsis

```bash
nipoppy pipeline create [OPTIONS] PIPELINE_DIR
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PIPELINE_DIR` | Path to the new pipeline config directory to create. Must not exist. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--type TYPE` / `-t TYPE` | — | Pipeline type. **Required**. One of: `bidsification`, `processing`, `extraction`. |
| `--source-descriptor FILE` | — | Seed from an existing Boutiques descriptor JSON file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Pipeline types

| Type | Use for |
|------|---------|
| `bidsification` | BIDS converters (dcm2bids, HeuDiConv, BIDScoin) |
| `processing` | Processing pipelines (fMRIPrep, MRIQC, FreeSurfer) |
| `extraction` | IDP extractors |

### Example invocations

```bash
# Create a new processing pipeline template
nipoppy pipeline create ./my-fmriprep-config --type processing

# Create a bidsification template seeded from an existing descriptor
nipoppy pipeline create ./my-dcm2bids --type bidsification \
  --source-descriptor /path/to/dcm2bids_descriptor.json
```

---

## `nipoppy pipeline validate`

Validate a pipeline config directory against the nipoppy schema. Run before
installing or uploading to catch errors early.

### Synopsis

```bash
nipoppy pipeline validate [OPTIONS] PATH
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATH` | Path to the pipeline config directory to validate. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Example invocations

```bash
# Validate a pipeline before installing
nipoppy pipeline validate ./my-fmriprep-config

# Validate with verbose output to see all checks
nipoppy pipeline validate ./my-fmriprep-config --verbose
```

---

## `nipoppy pipeline upload`

Upload a pipeline config directory to Zenodo to share with the community. Requires
a Zenodo access token.

### Synopsis

```bash
nipoppy pipeline upload [OPTIONS] PIPELINE_DIR
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PIPELINE_DIR` | Path to the pipeline config directory to upload. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--password-file FILE` | — | Path to file containing Zenodo access token. **Required**. |
| `--zenodo-id ID` | — | Zenodo record ID to update an existing record rather than create a new one. |
| `--sandbox` | off | Use the Zenodo sandbox API (safe for testing). |
| `--force` / `-f` | off | Ignore safeguard warnings and upload anyway. Use with caution. |
| `--assume-yes` / `--yes` / `-y` | off | Answer yes to all confirmation prompts. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print actions without executing. |

### Typical upload workflow

```bash
# 1. Validate first
nipoppy pipeline validate ./my-fmriprep-config

# 2. Test upload to sandbox
nipoppy pipeline upload ./my-fmriprep-config \
  --password-file ~/.zenodo_token --sandbox

# 3. Upload to production Zenodo (creates a new record)
nipoppy pipeline upload ./my-fmriprep-config \
  --password-file ~/.zenodo_token

# 4. Update an existing Zenodo record
nipoppy pipeline upload ./my-fmriprep-config \
  --password-file ~/.zenodo_token --zenodo-id 1234567
```

### Notes

- The Zenodo access token file must contain only the token string (no newlines or extra content).
- Always validate before uploading to catch schema errors early.
- Use `--sandbox` for test uploads to avoid publishing incomplete pipelines.
- Once published to production Zenodo, a record cannot be fully deleted — use `--sandbox` for iteration.
