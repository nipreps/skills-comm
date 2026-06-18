# Nipoppy Post-Processing Commands: `track-processing` and `extract`

## Shared options

Both commands accept:

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--pipeline NAME` | — | Pipeline name as specified in the config file. **Required**. |
| `--pipeline-version VERSION` | latest installed | Pipeline version. Must match an installed version in the dataset. |
| `--pipeline-step STEP` | first step | Sub-step within the pipeline. |
| `--participant-id ID` | all | Operate on a single participant (with or without `sub-` prefix). |
| `--session-id ID` | all | Operate on a single session (with or without `ses-` prefix). |
| `--layout FILE` | default | Path to a custom layout specification file. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print commands but do not execute them. |

---

## `nipoppy track-processing`

Record per-participant pipeline completion status into the processing status file
(`tabular/bagel.tsv`). Run after `nipoppy process` to update tracking.

### Synopsis

```bash
nipoppy track-processing [OPTIONS]
```

### Additional options

| Option | Default | Description |
|--------|---------|-------------|
| `--n-jobs N` | 1 | Number of parallel workers to use when checking outputs. |

### Bagel file schema (`bagel.tsv`)

| Column | Values | Description |
|--------|--------|-------------|
| `participant_id` | string | Subject ID |
| `session` | string | Session label |
| `pipeline_name` | string | Pipeline identifier (e.g., `fmriprep`) |
| `pipeline_version` | string | Pipeline version string |
| `pipeline_step` | string | Step label |
| `status` | `SUCCESS`/`FAIL`/`INCOMPLETE`/`UNAVAILABLE` | Completion status |
| `bids_id` | string | BIDS subject ID used by the pipeline |

### Status values

| Value | Meaning |
|-------|---------|
| `SUCCESS` | Pipeline completed without errors; expected outputs present |
| `FAIL` | Pipeline ran but reported errors or missing outputs |
| `INCOMPLETE` | Pipeline started but did not finish (e.g., job killed) |
| `UNAVAILABLE` | Participant/session not eligible (e.g., no BIDS data) |

### Example invocations

```bash
# Track fMRIPrep status for all participants
nipoppy track-processing --pipeline fmriprep --pipeline-version 23.1.3

# Track for a single participant
nipoppy track-processing --pipeline fmriprep --participant-id sub-001 --session-id ses-01

# Track in parallel across 8 workers
nipoppy track-processing --pipeline fmriprep --n-jobs 8
```

---

## `nipoppy extract`

Extract imaging-derived phenotypes (IDPs) from pipeline outputs into analysis-ready
tabular files. Each extractor is defined by a Boutiques descriptor in the pipeline config.

**Platform requirement:** Linux + Apptainer (for containerized extractors).

### Synopsis

```bash
nipoppy extract [OPTIONS]
```

### Additional options

| Option | Default | Description |
|--------|---------|-------------|
| `--keep-workdir` | off | Keep the working directory upon success. |
| `--simulate` | off | Print the extraction command without executing. |

**Filtering:**

| Option | Default | Description |
|--------|---------|-------------|
| `--use-subcohort FILE` | — | Path to a TSV file (no header; col 1 = participant IDs, col 2 = session IDs) listing pairs to extract. Same format as `--write-subcohort` output. |

**Parallelization / HPC:**

| Option | Default | Description |
|--------|---------|-------------|
| `--hpc TYPE` | — | Submit HPC jobs instead of running locally (`slurm`, `sge`, or any PySQA-supported type). |
| `--write-subcohort FILE` | — | Write eligible participant-session pairs to a TSV file and exit. |

### Output format

Extractors write analysis-ready TSV files to `derivatives/<pipeline>/<version>/`.
Each file has one row per participant-session and one column per IDP measure.

### Common extractor pipelines

| Pipeline | What is extracted |
|----------|------------------|
| `fmriprep` | Motion parameters, confound regressors, tissue probability maps |
| `mriqc` | Image quality metrics (IQMs): SNR, TSNR, FD, DVARS, etc. |
| `freesurfer` | Cortical thickness, surface area, subcortical volumes |
| `tractoflow` | Diffusion tensor metrics: FA, MD, AD, RD per tract |

### Example invocations

```bash
# Dry-run MRIQC IDP extraction
nipoppy extract --pipeline mriqc --simulate

# Extract MRIQC IDPs for all participants
nipoppy extract --pipeline mriqc --pipeline-version 23.1.0

# Extract fMRIPrep confounds for one participant
nipoppy extract --pipeline fmriprep --participant-id sub-001 --session-id ses-01

# Submit extraction to SLURM
nipoppy extract --pipeline freesurfer --hpc slurm

# Generate subcohort file for manual HPC submission
nipoppy extract --pipeline freesurfer --write-subcohort /tmp/extract_pairs.tsv
```

### After extract

- Review IDP tables in `derivatives/`
- Merge with phenotypic data from `tabular/` for downstream analysis
- Run `nipoppy status` to confirm all participants have been processed and extracted
