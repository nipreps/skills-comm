# SynthStrip / mri_synthstrip - Deep Learning Brain Extraction

**Executable:** `mri_synthstrip`
**Install hints:** FreeSurfer, SynthStrip standalone package, container image,
Conda environment, or site module such as `freesurfer/<version>` or
`synthstrip/<version>`.

SynthStrip is contrast-agnostic and works across T1w, T2w, FLAIR, DWI b0, and
EPI reference images. In current usage, the command to run is
`mri_synthstrip`.

## Usage

```bash
mri_synthstrip \
  -i <input.nii.gz> \
  -o <brain.nii.gz> \
  -m <mask.nii.gz>
```

## Key Flags

| Flag | Description |
|------|-------------|
| `-i <file>` | Input image. |
| `-o <file>` | Brain-extracted output. |
| `-m <file>` | Binary brain mask output. |
| `--no-csf` | Exclude CSF from the mask for a tighter result. |
| `-b <mm>` | Border size in mm; increase for looser mask. |
| `--gpu` | Use GPU if the install supports it and CUDA is available. |

## Licence Note

Some FreeSurfer-based installs require a FreeSurfer licence. Do not assume a
fixed licence path. If `mri_synthstrip` reports a licence error, locate the
site/user licence and set `FS_LICENSE` in the script.

## Output Files

| File | Description |
|------|-------------|
| `<brain.nii.gz>` | Brain-extracted image |
| `<mask.nii.gz>` | Binary brain mask |

**Brain mask path for QC handoff:** whatever path was passed to `-m`.

## Recommended Default Command

```bash
mri_synthstrip -i "${INPUT}" -o "${OUTPUT}" -m "${MASK}"
```

## Portable Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="<input.nii.gz>"
OUT_DIR="<output_dir>"
OUTPUT="${OUT_DIR}/<subject>_brain.nii.gz"
MASK="${OUT_DIR}/<subject>_brain_mask.nii.gz"

mkdir -p "${OUT_DIR}" logs

# Optional environment setup if needed:
# source activate <env>
# module load freesurfer/<version>
# module load synthstrip/<version>
# export FS_LICENSE="<path_to_license>"

command -v mri_synthstrip >/dev/null
mri_synthstrip -i "${INPUT}" -o "${OUTPUT}" -m "${MASK}"

test -s "${OUTPUT}"
test -s "${MASK}"
```

## Common Tuning

| Problem | Adjustment |
|---------|-----------|
| Mask too loose | Add `--no-csf` or decrease border with `-b 0`. |
| Inferior cerebellum/brainstem clipped | Increase border with `-b 2`. |
| GPU available and speed needed | Add `--gpu` if supported by the install. |
