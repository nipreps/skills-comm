# SynthStrip / mri_synthstrip — Deep Learning Brain Extraction

Two equivalent paths are available in Neurodesk. Both run the same underlying
SynthStrip model; choose based on what is already loaded.

---

## Path A: FreeSurfer mri_synthstrip

**Module:** `freesurfer/8.2.0`
**Command:** `mri_synthstrip`

### Usage

```bash
mri_synthstrip \
  -i <input.nii.gz> \
  -o <brain.nii.gz> \
  -m <mask.nii.gz>
```

### Key Flags

| Flag | Description |
|------|-------------|
| `-i <file>` | Input image (any modality) |
| `-o <file>` | Brain-extracted output |
| `-m <file>` | Binary brain mask output |
| `--no-csf` | Exclude CSF from the mask (tighter result) |
| `-b <mm>` | Border size in mm (default 1 mm); increase for looser mask |
| `--gpu` | Use GPU if available (requires CUDA environment) |

### FreeSurfer Licence Note

`mri_synthstrip` requires a valid FreeSurfer licence file. The licence is
typically pre-configured in Neurodesk at `/opt/freesurfer/license.txt`. Verify:
```bash
ls /opt/freesurfer/license.txt
```
If missing, set `FREESURFER_HOME` and `FS_LICENSE` environment variables to the
correct paths in the SLURM script.

### Output Files

| File | Description |
|------|-------------|
| `<brain.nii.gz>` | Brain-extracted image |
| `<mask.nii.gz>` | Binary brain mask |

**Brain mask path for QC handoff:** whatever path was passed to `-m`.

### Recommended Default Command

```bash
mri_synthstrip -i "${INPUT}" -o "${OUTPUT}" -m "${MASK}"
```

### SLURM Resource Estimates

```
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4
```

### SLURM Script Template (Path A)

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

module load freesurfer/8.2.0

export FREESURFER_HOME=/opt/freesurfer
export FS_LICENSE=${FREESURFER_HOME}/license.txt

mri_synthstrip \
  -i "${INPUT}" \
  -o "${OUTPUT}" \
  -m "${MASK}"
```

---

## Path B: SynthStrip Standalone

**Module:** `synthstrip/7.4.1`
**Command:** `synthstrip`

Lighter dependency — does not require the full FreeSurfer environment.

### Usage

```bash
synthstrip \
  -i <input.nii.gz> \
  -o <brain.nii.gz> \
  -m <mask.nii.gz>
```

Flags are identical to `mri_synthstrip`. No FreeSurfer licence required.

### SLURM Script Template (Path B)

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

module load synthstrip/7.4.1

synthstrip \
  -i "${INPUT}" \
  -o "${OUTPUT}" \
  -m "${MASK}"
```

---

## Modality Notes

SynthStrip is trained to be contrast-agnostic. It works reliably on:
- T1w (MPRAGE, MP2RAGE)
- T2w (TSE, SPACE)
- FLAIR
- DWI b0
- EPI (bold reference)

No parameter changes are needed when switching modalities.

## Common Tuning

| Problem | Adjustment |
|---------|-----------|
| Mask too loose (over-dilated) | Add `--no-csf` or decrease border: `-b 0` |
| Inferior cerebellum / brainstem clipped | Increase border: `-b 2` |
| GPU available and speed needed | Add `--gpu` (Path A only; ensure CUDA visible) |
