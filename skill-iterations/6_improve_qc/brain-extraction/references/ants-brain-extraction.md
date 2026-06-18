# ANTs - antsBrainExtraction.sh

**Executable:** `antsBrainExtraction.sh`
**Install hints:** ANTs package, container image, Conda environment, or site
module such as `ants/<version>`.

## Basic Usage

```bash
antsBrainExtraction.sh \
  -d 3 \
  -a <input.nii.gz> \
  -e <template.nii.gz> \
  -m <template_prob_mask.nii.gz> \
  -o <output_prefix>
```

## Required Arguments

| Flag | Description |
|------|-------------|
| `-d 3` | Image dimensionality for 3D structural MRI. |
| `-a <input>` | Input NIfTI image. |
| `-e <template>` | Brain extraction template. |
| `-m <prob_mask>` | Probability brain mask matching the template. |
| `-o <prefix>` | Output prefix. |

## Template Requirements

ANTs brain extraction requires a co-registered template and probability mask.
Verify paths before running:

```bash
ls "<template.nii.gz>" "<template_prob_mask.nii.gz>"
```

If templates are absent, use a locally accepted source and record the download
or copy command in a script. Common options are ANTs release templates, lab
shared storage, DataLad datasets, OpenNeuro derivatives, or direct `wget`/`curl`
downloads when licensing allows.

## Output Files

| File | Description |
|------|-------------|
| `<prefix>BrainExtractionBrain.nii.gz` | Brain-extracted image |
| `<prefix>BrainExtractionMask.nii.gz` | Binary brain mask |
| `<prefix>BrainExtractionPrior*.nii.gz` | Intermediate warped priors |

**Brain mask path for QC handoff:** `<prefix>BrainExtractionMask.nii.gz`

## Recommended Default Command

```bash
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="${THREADS:-4}"

antsBrainExtraction.sh \
  -d 3 \
  -a "${INPUT}" \
  -e "${TEMPLATE}" \
  -m "${TEMPLATE_MASK}" \
  -o "${OUTPUT_PREFIX}" \
  -u 0
```

`-u 0` disables random seeding for reproducibility.

## Portable Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="<input.nii.gz>"
TEMPLATE="<template.nii.gz>"
TEMPLATE_MASK="<template_prob_mask.nii.gz>"
OUT_DIR="<output_dir>"
OUTPUT_PREFIX="${OUT_DIR}/<subject>_"
THREADS="${THREADS:-4}"

mkdir -p "${OUT_DIR}" logs

# Optional environment setup if needed:
# source activate <env>
# module load ants/<version>
# apptainer exec <ants_image.sif> antsBrainExtraction.sh ...

command -v antsBrainExtraction.sh >/dev/null
ls "${TEMPLATE}" "${TEMPLATE_MASK}" >/dev/null
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="${THREADS}"

antsBrainExtraction.sh \
  -d 3 \
  -a "${INPUT}" \
  -e "${TEMPLATE}" \
  -m "${TEMPLATE_MASK}" \
  -o "${OUTPUT_PREFIX}" \
  -u 0

test -s "${OUTPUT_PREFIX}BrainExtractionBrain.nii.gz"
test -s "${OUTPUT_PREFIX}BrainExtractionMask.nii.gz"
```

## Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| Template not found | Template paths wrong or not downloaded | Verify and set template paths explicitly. |
| Registration diverges | Large orientation mismatch | Check orientation and consider reorientation before running. |
| Very slow | Threading not configured | Set `ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS`. |
