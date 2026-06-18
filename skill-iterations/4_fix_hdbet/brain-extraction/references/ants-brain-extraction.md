# ANTs — antsBrainExtraction.sh

**Module:** `ants/2.6.5`
**Command:** `antsBrainExtraction.sh`

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
| `-d 3` | Image dimensionality (3 for 3D structural MRI) |
| `-a <input>` | Input NIfTI image |
| `-e <template>` | Brain extraction template (T1w atlas in MNI or OASIS space) |
| `-m <prob_mask>` | Probability brain mask corresponding to the template |
| `-o <prefix>` | Output prefix (directory + subject label) |

## Optional Flags

| Flag | Description |
|------|-------------|
| `-f <mask>` | Registration mask to restrict moving-image region |
| `-u 0` | Disable random seeding (set for reproducibility) |
| `-k 1` | Keep all intermediate files (useful for debugging) |

## Template Requirements

ANTs brain extraction requires a co-registered template + probability mask.
The standard choice is the **OASIS-30 template** shipped with the ANTs scripts
package or downloadable from the ANTs GitHub releases.

**Verify template paths exist before writing the script:**
```bash
ls "${ANTS_DATA}/OASIS-30_Atropos_template_stripped.nii.gz"
ls "${ANTS_DATA}/OASIS-30_Atropos_template_stripped_priors_2.nii.gz"
```

If `${ANTS_DATA}` is not set, check:
```bash
find /usr /opt /neurodesk -name "OASIS*template*" 2>/dev/null | head -5
```

If templates are not found, download via DataLad or direct wget:
```bash
# OASIS-30 templates from ANTs GitHub (record provenance with DataLad if in a dataset)
wget -q https://github.com/ANTsX/ANTs/releases/download/v2.5.0/antsBrainExtractionTemplates.zip
unzip antsBrainExtractionTemplates.zip -d templates/
```
Record the download command in a `00_download_templates.sh` script for reproducibility.

## Output Files

| File | Description |
|------|-------------|
| `<prefix>BrainExtractionBrain.nii.gz` | Brain-extracted image |
| `<prefix>BrainExtractionMask.nii.gz` | Binary brain mask |
| `<prefix>BrainExtractionPrior*.nii.gz` | Intermediate warped priors |

**Brain mask path for QC handoff:** `<prefix>BrainExtractionMask.nii.gz`

## Recommended Default Command

```bash
antsBrainExtraction.sh \
  -d 3 \
  -a "${INPUT}" \
  -e "${TEMPLATE}" \
  -m "${TEMPLATE_MASK}" \
  -o "${OUTPUT_PREFIX}" \
  -u 0
```

`-u 0` disables random seeding for reproducibility.

## SLURM Resource Estimates

```
#SBATCH --time=01:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8
```

ANTs parallelises internally — providing more CPUs significantly reduces runtime.
Set `ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS` to match `--cpus-per-task`:

```bash
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8
```

## SLURM Script Template

```bash
#!/bin/bash
#SBATCH --job-name=brain_extraction
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=01:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8

mkdir -p logs/
mkdir -p "${OUT_DIR}"

module load ants/2.6.5

export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=8

antsBrainExtraction.sh \
  -d 3 \
  -a "${INPUT}" \
  -e "${TEMPLATE}" \
  -m "${TEMPLATE_MASK}" \
  -o "${OUTPUT_PREFIX}" \
  -u 0
```

## Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| Template not found | `ANTS_DATA` not set or templates not downloaded | Verify and set template paths explicitly |
| Registration diverges | Large orientation mismatch | Ensure input is in standard orientation (`fslreorient2std`) before running |
| Very slow even with 8 CPUs | `ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS` not set | Export the variable explicitly in the script |
