# HD-BET — High-Definition Brain Extraction Tool

**Module:** `hd-bet/2.0.1`
**Command:** `hd-bet`

HD-BET is a deep learning tool trained on multi-site, multi-contrast MRI data.
It is especially reliable on standard T1w images and supports GPU acceleration.

## Basic Usage

```bash
hd-bet -i <input.nii.gz> -o <output_prefix>
```

`<output_prefix>` — HD-BET appends `_bet.nii.gz` and `_bet_mask.nii.gz`
automatically. Provide a full path prefix (directory + subject label).

## Key Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-i <file>` | — | Input NIfTI image (required) |
| `-o <prefix>` | — | Output path prefix (required) |
| `-device cpu` | gpu | Force CPU mode when no GPU is available |
| `-mode fast` | accurate | Fast mode: slightly less accurate, much faster |
| `-tta 0` | 1 | Disable test-time augmentation (faster; slightly less robust) |
| `-pp 0` | 1 | Disable postprocessing (faster; may leave small disconnected regions) |

## Output Files

| File | Description |
|------|-------------|
| `<prefix>_bet.nii.gz` | Brain-extracted image |
| `<prefix>_bet_mask.nii.gz` | Binary brain mask |

**Brain mask path for QC handoff:** `<prefix>_bet_mask.nii.gz`

## GPU vs CPU Mode

HD-BET uses GPU by default. Check GPU availability before writing the script:
```bash
nvidia-smi 2>/dev/null | head -5
```

- **GPU available:** use default (omit `-device`); request a GPU partition in SLURM
- **No GPU:** add `-device cpu`; increase wall time and CPU allocation

## Recommended Default Commands

**GPU mode:**
```bash
hd-bet -i "${INPUT}" -o "${OUTPUT_PREFIX}"
```

**CPU mode:**
```bash
hd-bet -i "${INPUT}" -o "${OUTPUT_PREFIX}" -device cpu
```

## SLURM Resource Estimates

**GPU mode:**
```
#SBATCH --time=00:15:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
```

**CPU mode:**
```
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4
```

## SLURM Script Templates

### GPU mode

```bash
#!/bin/bash
#SBATCH --job-name=brain_extraction
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:15:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu

mkdir -p logs/
mkdir -p "${OUT_DIR}"

module load hd-bet/2.0.1

hd-bet -i "${INPUT}" -o "${OUTPUT_PREFIX}"
```

### CPU mode

```bash
#!/bin/bash
#SBATCH --job-name=brain_extraction
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4

mkdir -p logs/
mkdir -p "${OUT_DIR}"

module load hd-bet/2.0.1

hd-bet -i "${INPUT}" -o "${OUTPUT_PREFIX}" -device cpu
```

## Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| CUDA out of memory | GPU memory insufficient | Switch to CPU mode or use a smaller batch |
| Output mask all zeros | Input path incorrect or unsupported format | Check file exists and is NIfTI |
| Slow even in GPU mode | TTA enabled with many augmentations | Add `-tta 0` for speed |
