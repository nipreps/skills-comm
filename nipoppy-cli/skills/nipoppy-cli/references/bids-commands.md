# Nipoppy BIDS Commands: `bidsify`

## `nipoppy bidsify`

Run a BIDS conversion pipeline on the reorganized DICOMs in `post_reorg/`, producing
BIDS-valid output in `bids/`. The converter (dcm2bids, HeuDiConv, or BIDScoin) is
specified in `config.json` and invoked via Boutiques and Apptainer.

**Platform requirement:** Linux + Apptainer. Will not work on macOS or Windows.

### Synopsis

```bash
nipoppy bidsify [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--pipeline NAME` | — | BIDS converter name (e.g., `dcm2bids`, `heudiconv`, `bidscoin`). Must match config. **Required**. |
| `--pipeline-version VERSION` | latest installed | Converter version. Must match an installed version. |
| `--pipeline-step STEP` | first step | Converter sub-step (e.g., `prepare`, `convert` for dcm2bids). |
| `--participant-id ID` | all | Run conversion for a single participant (with or without `sub-` prefix). |
| `--session-id ID` | all | Run conversion for a single session (with or without `ses-` prefix). |
| `--use-subcohort FILE` | — | Path to a TSV file (no header; col 1 = participant IDs, col 2 = session IDs) to restrict which participants are processed. |
| `--simulate` | off | Print Boutiques invocation without executing. |
| `--dry-run` | off | Print commands without executing. |
| `--keep-workdir` | off | Keep the pipeline working directory upon success (default: deleted unless a run failed). |
| `--hpc TYPE` | — | Submit HPC jobs instead of running locally. Supported: `slurm`, `sge`, or any PySQA-supported type. |
| `--write-subcohort FILE` | — | Write eligible participant-session pairs to a TSV file and exit without running. Replaces the old `--write-list`. |
| `--layout FILE` | default | Path to a custom layout specification file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |

### Supported converters

| Converter | pipeline name in config | Notes |
|-----------|------------------------|-------|
| **dcm2bids** | `dcm2bids` | Two-step: `prepare` then `convert`. Config JSON required. |
| **HeuDiConv** | `heudiconv` | Heuristic Python file required. |
| **BIDScoin** | `bidscoin` | Plugin-based; requires a BIDScoin dataset map. |

### Pipeline config in `config.json`

```json
{
  "BIDS_CONVERTER": {
    "NAME": "dcm2bids",
    "VERSION": "3.1.0",
    "STEP": "convert",
    "CONTAINER": "/path/to/dcm2bids_3.1.0.sif",
    "CONFIG": "./code/dcm2bids_config.json"
  }
}
```

### dcm2bids two-step workflow

dcm2bids requires two passes:

1. **prepare step** — Generates a `tmp_dcm2bids/` with a DICOM structure overview and
   a helper JSON. Used to build the `dcm2bids_config.json`.

   ```bash
   nipoppy bidsify --pipeline dcm2bids --pipeline-step prepare --participant-id sub-001 --session-id ses-01
   ```

2. **convert step** — Uses `dcm2bids_config.json` to convert all DICOMs to BIDS.

   ```bash
   nipoppy bidsify --pipeline dcm2bids --pipeline-step convert
   ```

### HeuDiConv workflow

HeuDiConv uses a Python heuristic file specified in `config.json`. Conversion is
typically single-step but may require a scouting pass first.

```bash
nipoppy bidsify --pipeline heudiconv --simulate
nipoppy bidsify --pipeline heudiconv
```

### Boutiques context

Nipoppy resolves converter invocations from Boutiques descriptors. The descriptor
defines input/output mappings, container mounts, and command-line templates.
Custom descriptors can be placed in `code/boutiques/` and referenced in `config.json`.

### HPC / batch execution

**Pattern 1 — Native HPC submission (recommended):**

```bash
# Direct SLURM submission
nipoppy bidsify --pipeline dcm2bids --pipeline-step convert --hpc slurm
```

**Pattern 2 — Manual subcohort splitting:**

```bash
# Write participant-session pairs to a file
nipoppy bidsify --pipeline dcm2bids --pipeline-step convert \
  --write-subcohort /tmp/bidsify_pairs.tsv
# Then iterate over lines in an HPC array job
```

### Example invocations

```bash
# Dry-run to check what would be converted
nipoppy bidsify --simulate

# Run dcm2bids prepare step for one participant
nipoppy bidsify --pipeline dcm2bids --pipeline-step prepare \
  --participant-id sub-001 --session-id ses-01

# Run full dcm2bids conversion
nipoppy bidsify --pipeline dcm2bids --pipeline-step convert

# Run HeuDiConv on all participants
nipoppy bidsify --pipeline heudiconv

# Write subcohort file for manual HPC submission
nipoppy bidsify --pipeline dcm2bids --pipeline-step convert --write-subcohort /tmp/pairs.tsv

# Submit directly to SLURM
nipoppy bidsify --pipeline dcm2bids --pipeline-step convert --hpc slurm
```

### After bidsify

1. Validate BIDS output with the BIDS Validator (`bids-validator bids/` or the online tool).
2. Run `nipoppy track-curation` to update `has_bids_data` flags.
