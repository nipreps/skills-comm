# AFNI 3dSkullStrip

**Executables:** `3dSkullStrip`, `3dcalc`; optionally `3dAFNItoNIFTI`
**Install hints:** AFNI package, container image, Conda environment, or site
module such as `afni/<version>`.

3dSkullStrip uses surface expansion to separate brain from non-brain tissue. It
works on T1w structural data and EPI/functional volumes, especially within AFNI
workflows.

## Basic Usage

```bash
3dSkullStrip \
  -input <input+orig.HEAD or input.nii.gz> \
  -prefix <output>
```

Both AFNI-format and NIfTI inputs are accepted.

## Key Options

| Option | Description |
|--------|-------------|
| `-input <file>` | Input dataset. |
| `-prefix <name>` | Output prefix. |
| `-orig_vol` | Output in the same grid/space as the input. |
| `-rat` | Rat brain mode. |
| `-monkey` | Non-human primate mode. |
| `-push_to_edge` | Aggressive expansion; use if too much brain is removed. |
| `-no_avoid_eyes` | Include eye orbits. |
| `-shrink_fac <val>` | Shrinkage factor; lower = larger mask. |
| `-ld <val>` | Level of detail; higher can be more precise and slower. |

## Output Files

By default, AFNI may write HEAD/BRIK. To write NIfTI, use
`-prefix <name>.nii.gz` or convert afterwards with `3dAFNItoNIFTI`.

Create a binary mask from the stripped brain:
```bash
3dcalc -a <output>.nii.gz -expr 'step(a)' -prefix <output>_mask.nii.gz
```

**Brain mask path for QC handoff:** `<output>_mask.nii.gz`

## Recommended Default Command

```bash
3dSkullStrip \
  -input "${INPUT}" \
  -prefix "${OUTPUT}.nii.gz" \
  -orig_vol

3dcalc \
  -a "${OUTPUT}.nii.gz" \
  -expr 'step(a)' \
  -prefix "${MASK}"
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

# Optional environment setup if needed:
# source activate <env>
# module load afni/<version>

command -v 3dSkullStrip >/dev/null
command -v 3dcalc >/dev/null

3dSkullStrip -input "${INPUT}" -prefix "${OUTPUT}.nii.gz" -orig_vol
3dcalc -a "${OUTPUT}.nii.gz" -expr 'step(a)' -prefix "${MASK}"

test -s "${OUTPUT}.nii.gz"
test -s "${MASK}"
```

## Tuning Guide

| Problem | Adjustment |
|---------|-----------|
| Over-stripping | Lower `-shrink_fac`, e.g. `0.4`, or add `-push_to_edge`. |
| Under-stripping | Raise `-shrink_fac`, e.g. `0.7`. |
| Complex data | Increase `-ld`, e.g. `40`. |
| Functional EPI data | Consider `3dAutomask` for 4D data. |
