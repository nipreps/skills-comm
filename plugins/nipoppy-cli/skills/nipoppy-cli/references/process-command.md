# Nipoppy `process` Command

Run a processing pipeline (fMRIPrep, MRIQC, etc.) on BIDS data. Invokes the
pipeline container via Apptainer and Boutiques.

**Platform requirement:** Linux + Apptainer. Will not work on macOS or Windows.

## Synopsis

```bash
nipoppy process [OPTIONS]
```

## Options

**Command-specific:**

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--pipeline NAME` | — | Pipeline name as specified in the config file. **Required**. |
| `--pipeline-version VERSION` | latest installed | Pipeline version. Must match an installed version in the dataset. |
| `--pipeline-step STEP` | first step | Sub-step within the pipeline (if the pipeline defines multiple steps). |
| `--tar` | off | Archive participant-session-level results into a tarball upon successful completion. The path to be archived must be specified in the tracker configuration file. |

**Filtering:**

| Option | Default | Description |
|--------|---------|-------------|
| `--participant-id ID` | all | Operate on a single participant (with or without `sub-` prefix). |
| `--session-id ID` | all | Operate on a single session (with or without `ses-` prefix). |
| `--use-subcohort FILE` | — | Path to a TSV file (no header; col 1 = participant IDs, col 2 = session IDs) listing the participant-session pairs to process. Same format as `--write-subcohort` output. |

**Parallelization / HPC:**

| Option | Default | Description |
|--------|---------|-------------|
| `--hpc TYPE` | — | Submit HPC jobs instead of running locally. Supported: `slurm`, `sge`, or any PySQA-supported type. |
| `--write-subcohort FILE` | — | Write eligible participant-session pairs to a TSV file and exit without running. Use to prepare input for `--use-subcohort` or manual HPC job arrays. |

**Troubleshooting:**

| Option | Default | Description |
|--------|---------|-------------|
| `--keep-workdir` | off | Keep the pipeline working directory upon success (default: deleted unless a run failed). Useful for debugging. |
| `--simulate` | off | Print the Boutiques/Apptainer invocation without executing. |
| `--verbose` / `-v` | off | Show DEBUG messages. |
| `--dry-run` | off | Print commands but do not execute them. |
| `--layout FILE` | default | Path to a custom layout specification file. |

## HPC / parallel execution

**Pattern 1 — Native HPC submission (recommended):**

```bash
# Direct SLURM submission (nipoppy handles job creation)
nipoppy process --pipeline fmriprep --hpc slurm

# Direct SGE submission
nipoppy process --pipeline fmriprep --hpc sge
```

**Pattern 2 — Manual subcohort splitting:**

```bash
# Write participant-session list
nipoppy process --pipeline fmriprep --write-subcohort /tmp/fmriprep_pairs.tsv

# Submit as SLURM array (read subcohort line by line)
sbatch --array=1-$(wc -l < /tmp/fmriprep_pairs.tsv) run_array.sh
```

## Example invocations

```bash
# Dry-run fMRIPrep on all participants
nipoppy process --pipeline fmriprep --simulate

# Run fMRIPrep on all participants
nipoppy process --pipeline fmriprep --pipeline-version 23.1.3

# Run MRIQC on one participant, preserving workdir for debugging
nipoppy process --pipeline mriqc --participant-id sub-001 --session-id ses-01 --keep-workdir

# Submit all participants to SLURM
nipoppy process --pipeline fmriprep --hpc slurm

# Generate subcohort file for manual HPC submission
nipoppy process --pipeline fmriprep --write-subcohort /tmp/pairs.tsv
```

## Next step

After `process` completes, run `nipoppy track-processing` to record completion
status in `tabular/bagel.tsv`.
