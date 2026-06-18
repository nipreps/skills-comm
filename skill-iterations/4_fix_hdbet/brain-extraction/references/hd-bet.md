# HD-BET — High-Definition Brain Extraction Tool

**Module:** `hdbet/2.0.1`
**Module lookup:** `module spider hdbet`
**Command:** `hd-bet`

HD-BET is a deep learning tool trained on multi-site, multi-contrast MRI data.
It is especially reliable on standard T1w images and supports GPU acceleration.

## Basic Usage

```bash
hd-bet -i <input.nii.gz> -o <output_image.nii.gz>
```

`<output_image.nii.gz>` is the brain-extracted image path. In Neurodesk,
HD-BET is provided by the `hdbet` module, while the executable remains
`hd-bet`. For discovery, run `module spider hdbet`; do not search for a
module named `hd-bet`.

For predictable downstream naming, set:
- `OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"`
- `MASK_IMAGE="${OUTPUT_PREFIX}_bet_mask.nii.gz"`

HD-BET writes the mask by adding `_mask` before the image extension, so the
mask corresponding to `${OUTPUT_PREFIX}_bet.nii.gz` is
`${OUTPUT_PREFIX}_bet_mask.nii.gz`.

## Key Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-i <file>` | — | Input NIfTI image (required) |
| `-o <file>` | — | Output brain-extracted image path (required) |
| `-device cpu` | gpu | Force CPU mode when no GPU is available |
| `-mode fast` | accurate | Fast mode: slightly less accurate, much faster |
| `--disable_tta` | off | Disable test-time augmentation (faster; slightly less robust) |
| `-pp 0` | 1 | Disable postprocessing (faster; may leave small disconnected regions) |

## Output Files

| File | Description |
|------|-------------|
| `${OUTPUT_PREFIX}_bet.nii.gz` | Brain-extracted image |
| `${OUTPUT_PREFIX}_bet_mask.nii.gz` | Binary brain mask |

**Brain mask path for QC handoff:** `${OUTPUT_PREFIX}_bet_mask.nii.gz`

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
OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}"
```

**CPU mode:**
```bash
OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}" -device cpu --disable_tta
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

module load hdbet/2.0.1

OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
MASK_IMAGE="${OUTPUT_PREFIX}_bet_mask.nii.gz"

hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}"

test -s "${OUTPUT_IMAGE}"
test -s "${MASK_IMAGE}"
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

module load hdbet/2.0.1

OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
MASK_IMAGE="${OUTPUT_PREFIX}_bet_mask.nii.gz"

hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}" -device cpu --disable_tta

test -s "${OUTPUT_IMAGE}"
test -s "${MASK_IMAGE}"
```

## Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| CUDA out of memory | GPU memory insufficient | Switch to CPU mode or use a smaller batch |
| Output mask all zeros | Input path incorrect or unsupported format | Check file exists and is NIfTI |
| Slow even in GPU mode | TTA enabled with many augmentations | Add `--disable_tta` for speed |
