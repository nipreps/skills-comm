# AFNI 3dSkullStrip

**Module:** `afni/26.0.07`
**Command:** `3dSkullStrip`

3dSkullStrip is an AFNI tool that uses surface expansion to separate brain from
non-brain tissue. It works on T1w structural data and EPI/functional volumes, and
is the natural choice when working within an AFNI-based pipeline.

## Basic Usage

```bash
3dSkullStrip \
  -input <input+orig.HEAD or input.nii.gz> \
  -prefix <output>
```

Both AFNI-format (HEAD/BRIK) and NIfTI inputs are accepted.

## Key Options

| Option | Description |
|--------|-------------|
| `-input <file>` | Input dataset (required) |
| `-prefix <name>` | Output prefix (required) |
| `-orig_vol` | Output in the same grid/space as the input (recommended for NIfTI workflows) |
| `-rat` | Rat brain mode — adjusts parameters for rodent data |
| `-monkey` | Non-human primate mode |
| `-push_to_edge` | Aggressive expansion — use if too much brain is removed |
| `-no_avoid_eyes` | Include eye orbits in mask (off by default) |
| `-shrink_fac <val>` | Shrinkage factor (default 0.6); lower = larger mask |
| `-ld <val>` | Level of detail (default 20); increase for more precise boundary |

## Output Files

By default, 3dSkullStrip writes AFNI format (HEAD/BRIK). To write NIfTI:
- Use `-prefix <name>.nii.gz` directly, or
- Convert afterwards: `3dAFNItoNIFTI -prefix <name>.nii.gz <name>+orig`

To also output the binary mask:
```bash
3dcalc -a <output>.nii.gz -expr 'step(a)' -prefix <output>_mask.nii.gz
```

**Brain mask path for QC handoff:** `<output>_mask.nii.gz` (after the 3dcalc step)

## Recommended Default Command

```bash
3dSkullStrip \
  -input "${INPUT}" \
  -prefix "${OUTPUT}.nii.gz" \
  -orig_vol

# Generate binary mask from stripped brain
3dcalc \
  -a "${OUTPUT}.nii.gz" \
  -expr 'step(a)' \
  -prefix "${MASK}"
```

## SLURM Resource Estimates

```
#SBATCH --time=00:20:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1
```

## SLURM Script Template

```bash
#!/bin/bash
#SBATCH --job-name=brain_extraction
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:20:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

mkdir -p logs/
mkdir -p "${OUT_DIR}"

module load afni/26.0.07

3dSkullStrip \
  -input "${INPUT}" \
  -prefix "${OUTPUT}.nii.gz" \
  -orig_vol

# Create binary mask
3dcalc \
  -a "${OUTPUT}.nii.gz" \
  -expr 'step(a)' \
  -prefix "${MASK}"
```

## Tuning Guide

| Problem | Adjustment |
|---------|-----------|
| Over-stripping (brain tissue removed) | Lower `-shrink_fac` (e.g., 0.4) or add `-push_to_edge` |
| Under-stripping (skull remaining) | Raise `-shrink_fac` (e.g., 0.7) |
| Slow on complex data | Increase `-ld` (e.g., 40) — more accurate but slower |
| Functional EPI data | Use with EPI reference volume; consider also `3dAutomask` for 4D data |

## Note on Functional Data

For 4D EPI time series, `3dAutomask` is often preferred over `3dSkullStrip`:
```bash
3dAutomask -prefix "${EPI_MASK}" "${EPI_INPUT}"
```
This is faster and avoids the surface-fitting approach which can fail on EPI
contrast. Use `3dSkullStrip` when working with a high-res anatomical reference.
