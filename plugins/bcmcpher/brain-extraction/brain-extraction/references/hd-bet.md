# HD-BET - High-Definition Brain Extraction Tool

**Executable:** `hd-bet`
**Package/module name often used:** `hdbet`
**Install hints:** HD-BET package, container image, Conda environment, or site
module such as `hdbet/<version>`.

HD-BET is a deep learning tool trained on multi-site, multi-contrast MRI data.
It is especially useful for standard T1w images and supports GPU acceleration.

## Basic Usage

```bash
hd-bet -i <input.nii.gz> -o <output_image.nii.gz>
```

For discovery, search for the executable with `command -v hd-bet`. On module
systems, the module may be named `hdbet`, not `hd-bet`.

For predictable downstream naming:
- `OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"`
- `MASK_IMAGE="${OUTPUT_PREFIX}_bet_mask.nii.gz"`

HD-BET writes the mask by adding `_mask` before the image extension.

## Key Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-i <file>` | - | Input NIfTI image. |
| `-o <file>` | - | Output brain-extracted image path. |
| `-device cpu` | gpu | Force CPU mode when no GPU is available. |
| `-mode fast` | accurate | Faster, slightly less accurate mode. |
| `--disable_tta` | off | Disable test-time augmentation for speed. |
| `-pp 0` | 1 | Disable postprocessing. |

## Output Files

| File | Description |
|------|-------------|
| `${OUTPUT_PREFIX}_bet.nii.gz` | Brain-extracted image |
| `${OUTPUT_PREFIX}_bet_mask.nii.gz` | Binary brain mask |

**Brain mask path for QC handoff:** `${OUTPUT_PREFIX}_bet_mask.nii.gz`

## GPU vs CPU Mode

Check GPU availability using whatever is present on the system:
```bash
command -v nvidia-smi >/dev/null && nvidia-smi 2>/dev/null | head -5
```

- GPU available: omit `-device` unless the site requires a specific GPU setup.
- No GPU: add `-device cpu`; consider `--disable_tta` for faster runtime.

## Recommended Default Commands

**GPU/default mode:**
```bash
OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}"
```

**CPU mode:**
```bash
OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}" -device cpu --disable_tta
```

## Portable Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="<input.nii.gz>"
OUT_DIR="<output_dir>"
OUTPUT_PREFIX="${OUT_DIR}/<subject>"
OUTPUT_IMAGE="${OUTPUT_PREFIX}_bet.nii.gz"
MASK_IMAGE="${OUTPUT_PREFIX}_bet_mask.nii.gz"

mkdir -p "${OUT_DIR}" logs

# Optional environment setup if needed:
# source activate <env>
# module load hdbet/<version>
# apptainer exec --nv <hdbet_image.sif> hd-bet ...

command -v hd-bet >/dev/null

if command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null 2>&1; then
  hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}"
else
  hd-bet -i "${INPUT}" -o "${OUTPUT_IMAGE}" -device cpu --disable_tta
fi

test -s "${OUTPUT_IMAGE}"
test -s "${MASK_IMAGE}"
```

## Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| CUDA out of memory | GPU memory insufficient | Switch to CPU mode or use a smaller image/batch. |
| Output mask all zeros | Input path or image unsupported | Check file exists and is valid NIfTI. |
| Slow runtime | CPU mode or TTA enabled | Add `--disable_tta` or use GPU if available. |
