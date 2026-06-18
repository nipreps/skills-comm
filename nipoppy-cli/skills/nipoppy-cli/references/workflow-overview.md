# Nipoppy Workflow Overview

## What is nipoppy?

Nipoppy is a Python CLI tool for managing neuroimaging datasets in a standardized,
reproducible way. It wraps around Boutiques descriptors and Apptainer containers to
provide a consistent interface for DICOM organization, BIDS conversion, pipeline
execution, and phenotype extraction.

**Key dependencies:**
- Python 3.8+, installed via `pip install nipoppy`
- **Linux + Apptainer** (formerly Singularity) for all pipeline commands
- Boutiques (`boutiques`) for pipeline descriptor resolution

---

## Linear Workflow

```
Raw DICOMs arrive
        │
        ▼
[1] nipoppy init          — Create dataset directory structure + config stubs
        │
        ▼
[2] Edit manifest.tsv     — Register all expected participant-session pairs
        │
        ▼
[3] nipoppy track-curation — Build/update curation status file
        │
        ▼
[4] nipoppy reorg          — Move/copy DICOMs → post_reorg layout
        │
        ▼
[5] nipoppy track-curation — Update status after reorg
        │
        ▼
[6] nipoppy bidsify        — Convert DICOMs to BIDS (dcm2bids / HeuDiConv / BIDScoin)
        │
        ▼
[7] nipoppy track-curation — Update status after BIDS conversion
        │
        ▼
[8] nipoppy process        — Execute processing pipeline (fMRIPrep, MRIQC, etc.)
        │
        ▼
[9] nipoppy track-processing — Record per-participant pipeline completion
        │
        ▼
[10] nipoppy extract       — Extract IDPs into analysis-ready tables
        │
        ▼
[11] nipoppy status        — Report overall workflow status at any time
```

`nipoppy status` can be run at any point to see current state.

---

## Key Files and Directories

### Dataset root (created by `nipoppy init`)

```
<dataset>/
├── config.json                    # Global config: pipelines, BIDS converters, paths
├── manifest.tsv                   # Participant-session registry (user-maintained)
├── sourcedata/
│   └── imaging/
│       ├── pre_reorg/             # Raw DICOMs drop zone (input to reorg)
│       └── post_reorg/            # Reorg output: <participant>/<session>/ layout
├── bids/                          # BIDS-valid output from bidsify
├── derivatives/                   # Pipeline outputs (fMRIPrep, MRIQC, etc.)
├── proc/
│   └── logs/                      # Per-run log files
├── scratch/                       # Temporary working directories
└── tabular/
    ├── curation_status.tsv        # Per-participant-session curation tracking
    └── bagel.tsv                  # Processing pipeline status (the "bagel" file)
```

### config.json structure (abbreviated)

```json
{
  "DATASET_NAME": "my-study",
  "VISITS": ["baseline", "followup"],
  "SESSIONS": ["ses-01", "ses-02"],
  "BIDS_CONVERTER": {
    "NAME": "dcm2bids",
    "VERSION": "3.1.0",
    "STEP": "prepare"
  },
  "PROC_PIPELINES": {
    "fmriprep": {
      "VERSION": "23.1.3",
      "STEP": "default"
    }
  }
}
```

### manifest.tsv columns

| Column | Description |
|--------|-------------|
| `participant_id` | Subject identifier (e.g., `sub-001`) |
| `visit` | Visit label (e.g., `baseline`) |
| `session` | Session label (e.g., `ses-01`) |
| `datatype` | Imaging datatype (e.g., `anat`, `func`) |

---

## Key Concepts & Glossary

| Term | Definition |
|------|------------|
| **Boutiques** | JSON descriptor standard for containerized tools; nipoppy uses it to resolve pipeline invocations |
| **Apptainer** | Linux container runtime (replaces Singularity); required for pipeline commands |
| **BIDS** | Brain Imaging Data Structure — the target format for `bidsify` output |
| **curation_status.tsv** | Tracks raw data availability, reorg completion, and BIDS conversion per participant-session |
| **bagel.tsv** | Processing status file tracking pipeline completion per participant-session |
| **IDP** | Imaging-Derived Phenotype — quantitative measure extracted from a pipeline output (e.g., cortical thickness, FA values) |
| **pre_reorg** | Raw DICOM drop zone; unstructured |
| **post_reorg** | Structured DICOM layout: one folder per participant per session |
| **pipeline step** | A sub-stage within a pipeline (e.g., `prepare`, `convert` in dcm2bids) |
| **simulate** | Dry-run mode: prints commands without executing them |

---

## Platform Requirements

| Feature | Requirement |
|---------|-------------|
| CLI installation | Python 3.8+, any OS |
| `init`, `status`, `track-curation` | Any OS |
| `reorg` | Any OS (file operations only) |
| `bidsify`, `process`, `extract` | **Linux + Apptainer** (containers required) |
| HPC execution | SLURM or SGE recommended for large cohorts |

---

## Common Pitfalls

1. **Uninitialized dataset** — Running any command other than `init` without a `config.json` will fail.
2. **Missing manifest entries** — Participants not in `manifest.tsv` are invisible to all nipoppy commands.
3. **Pre-reorg files not in expected layout** — `reorg` expects files in `pre_reorg/`; ad-hoc layouts may need custom heuristics.
4. **Apptainer not on PATH** — Pipeline commands fail silently if Apptainer is not available; check with `apptainer --version`.
5. **Container image not pulled** — Pipeline containers must be pulled before `process`; nipoppy does not auto-pull by default.
6. **config.json pipeline version mismatch** — The version specified in `config.json` must match the pulled container image tag.
