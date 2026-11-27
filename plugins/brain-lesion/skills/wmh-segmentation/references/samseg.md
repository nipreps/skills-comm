# SAMSEG lesion model

SAMSEG jointly segments brain structures and a lesion class from coregistered
structural images. With lesion modelling enabled, cerebral lesion voxels are
stored as label 99 in its segmentation. This sheet describes the installed
interface and outputs without making a general tool-ranking claim.

## Availability and resources

- Module: `freesurfer/8.2.0`
- Executables: `run_samseg`, `mri_binarize`
- Inputs: coregistered T1w and FLAIR.
- Measured runtime on a clinical pair: about 17 minutes.
- Conservative Slurm starting request: 8 CPUs, 16 GB RAM, 2 hours.

```bash
set -o pipefail
module -t avail freesurfer/8.2.0 2>&1 | grep -F 'freesurfer/8.2.0'
module load freesurfer/8.2.0
command -v run_samseg
command -v mri_binarize
FS_IMAGE_KEY=NEURODESK_IMAGE_667265657375726665722F382E322E30
FS_CONTAINER="${!FS_IMAGE_KEY:?freesurfer/8.2.0 did not export its image path}"
test -r "${FS_CONTAINER}"
singularity --silent exec --cleanenv $neurodesk_singularity_opts \
  "${FS_CONTAINER}" /opt/freesurfer-8.2.0/bin/fspython \
  -c "import tensorflow as tf; print(tf.__version__)"
```

The TensorFlow test must use the container-side `fspython`; a host-Python
import is not an equivalent availability probe. The module exports its image
path under `NEURODESK_IMAGE_667265657375726665722F382E322E30`; resolve that value
after loading the pinned module rather than hard-coding a dated CVMFS build path.

## Invocation

```bash
module load freesurfer/8.2.0
mkdir -p "${ATTEMPT_DIR}/samseg"
run_samseg --input "${T1}" "${FLAIR}" \
  --output "${ATTEMPT_DIR}/samseg" \
  --pallidum-separate --lesion --lesion-mask-pattern 0 1 \
  --threshold 0.3 \
  --threads "${SLURM_CPUS_PER_TASK:-8}"
mri_binarize --i "${ATTEMPT_DIR}/samseg/seg.mgz" --match 99 \
  --o "${ATTEMPT_DIR}/samseg/wmh_mask.nii.gz" \
  --count "${ATTEMPT_DIR}/samseg/wmh_mask.count.txt"
```

Use `freesurfer/8.2.0` exactly after its probe succeeds. Do not silently select
an older version from the broader `module spider freesurfer` list. The mask
pattern is ordered exactly like `--input`: `0` identifies T1w and `1` identifies
FLAIR. FreeSurfer strongly recommends declaring this pattern for lesion
segmentation. The fixed `0.3` threshold makes SAMSEG's documented default
operating point explicit; do not tune it per subject or against a hidden
reference mask.

## Outputs

| Path under `--output` | Meaning | Use |
|---|---|---|
| `seg.mgz` | Whole-brain label map; lesions are label 99 | Source for candidate extraction |
| `wmh_mask.nii.gz` | Binary label-99 mask created above | Publication candidate |
| `wmh_mask.count.txt` | Candidate voxel count | Cross-check |
| `samseg.stats`, `samseg.fs.stats`, `samseg.csv` | Regional and lesion volumes | Quantitative QC |
| `mode*_bias_corrected.mgz` | Bias-corrected inputs | Supplementary QC |
| registration/transform files | Model alignment products | Diagnostic context |

Never binarize every nonzero value in `seg.mgz`; that produces a whole-brain
mask rather than WMH. The label-99 candidate follows SAMSEG's input geometry
but MGZ/NIfTI conversion can introduce micrometre-scale affine rounding. Check
it against the requested FLAIR grid. On `reference_grid_exact`, use the bundled
nearest-neighbour helper from the main skill; do not hand-copy the array under
the FLAIR header.

## Known signatures

| Signature | Interpretation |
|---|---|
| TensorFlow import failure in container `fspython` | Environment incompatibility before execution |
| CUDA-driver, TF-TRT, or deprecation warnings while iterations advance | Non-fatal CPU-path diagnostics |
| Changing iteration/deformation lines | Active computation, not a loop |
| Slurm cancellation without a preceding traceback | External tool-execution failure |
| Candidate covers the whole brain | Output extraction error: nonzero labels were used instead of label 99 |
| Publisher reports only `reference_grid_exact` with matching shape/orientation | Expected conversion rounding; run the bundled reference-grid helper before publication |

Retain the import probe, Slurm accounting, stdout/stderr, stats, label count, and
publisher JSON.
