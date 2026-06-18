# FSL BET — Brain Extraction Tool

**Module:** `fsl/6.0.7.22`
**Command:** `bet`

## Basic Usage

```bash
bet <input> <output> [options]
```

`<input>` — input NIfTI image (T1w recommended)
`<output>` — output brain image path (without extension; BET adds `.nii.gz`)

## Key Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-f <val>` | 0.5 | Fractional intensity threshold (0–1). Lower = larger brain estimate. Try 0.3–0.4 for images with large scalp/neck. |
| `-g <val>` | 0 | Vertical gradient (-1 to 1). Negative = larger at bottom (useful for neck-heavy FOV). |
| `-R` | off | Robust brain centre estimation — iterates BET; slower but better for challenging images |
| `-m` | off | Output binary brain mask as `<output>_mask.nii.gz` |
| `-B` | off | Bias field correction + brain extraction (adds time; useful for field-inhomogeneous data) |
| `-S` | off | Eye & optic nerve cleanup (use with `-B` for cleaner masks) |
| `-F` | off | Functional data mode — applies to 4D EPI |

## Output Files

| File | Description |
|------|-------------|
| `<output>.nii.gz` | Brain-extracted image |
| `<output>_mask.nii.gz` | Binary brain mask (requires `-m`) |

**Brain mask path for QC handoff:** `<output>_mask.nii.gz`

## Recommended Default Command

```bash
bet "${INPUT}" "${OUTPUT}" -f 0.5 -m -R
```

`-R` improves robustness with minimal time cost for most structural T1w scans.
Use `-B` additionally if field inhomogeneity is expected.

## Tuning Guide

| Problem observed | Adjustment |
|-----------------|-----------|
| Too much brain removed (over-stripping) | Lower `-f` (try 0.3) |
| Skull/scalp remaining (under-stripping) | Raise `-f` (try 0.6–0.7) |
| Poor result in inferior brain | Add `-g -0.1` |
| Still failing | Switch to `-R` + reduce `-f`, or consider mri_synthstrip |

## SLURM Resource Estimates

```
#SBATCH --time=00:15:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1
```

## SLURM Script Template

```bash
#!/bin/bash
#SBATCH --job-name=brain_extraction
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:15:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

mkdir -p logs/
mkdir -p "${OUT_DIR}"

module load fsl/6.0.7.22

bet "${INPUT}" "${OUTPUT}" -f 0.5 -m -R
```
