# FSL BET - Brain Extraction Tool

**Executable:** `bet`
**Install hints:** FSL package, container image, Conda environment, or site
module such as `fsl/<version>`.

## Basic Usage

```bash
bet <input> <output> [options]
```

`<output>` is the output brain image path without extension; BET usually adds
`.nii.gz`.

## Key Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-f <val>` | 0.5 | Fractional intensity threshold. Lower = larger brain estimate. |
| `-g <val>` | 0 | Vertical gradient. Negative = larger at bottom. |
| `-R` | off | Robust brain centre estimation. |
| `-m` | off | Output binary mask as `<output>_mask.nii.gz`. |
| `-B` | off | Bias field correction plus brain extraction. |
| `-F` | off | Functional data mode for 4D EPI. |

## Output Files

| File | Description |
|------|-------------|
| `<output>.nii.gz` | Brain-extracted image |
| `<output>_mask.nii.gz` | Binary brain mask with `-m` |

**Brain mask path for QC handoff:** `<output>_mask.nii.gz`

## Recommended Default Command

```bash
bet "${INPUT}" "${OUTPUT}" -f 0.5 -m -R
```

## Portable Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="<input.nii.gz>"
OUT_DIR="<output_dir>"
OUTPUT="${OUT_DIR}/<subject>_brain"
MASK="${OUTPUT}_mask.nii.gz"

mkdir -p "${OUT_DIR}" logs

# Optional environment setup if needed on this system:
# source activate <env>
# module load fsl/<version>
# apptainer exec <fsl_image.sif> bet ...

command -v bet >/dev/null
bet "${INPUT}" "${OUTPUT}" -f 0.5 -m -R

test -s "${OUTPUT}.nii.gz"
test -s "${MASK}"
```

## Tuning Guide

| Problem observed | Adjustment |
|-----------------|-----------|
| Too much brain removed | Lower `-f`, e.g. `0.3`. |
| Skull/scalp remaining | Raise `-f`, e.g. `0.6` to `0.7`. |
| Poor inferior result | Add `-g -0.1`. |
| Still failing | Try `-R`, lower `-f`, or consider mri_synthstrip. |
