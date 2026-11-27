# HyperMapp3r

HyperMapp3r is a Bayesian 3D U-Net for vascular WMH segmentation. It uses
coregistered T1w, FLAIR, and a brain mask, averages repeated Monte Carlo dropout
predictions, and thresholds the mean probability map. Its published evaluation
trained on 432 subjects from four multisite studies and tested on 158 subjects,
including an unseen multisite study.

Primary sources: [official repository](https://github.com/AICONSlab/HyperMapp3r),
[official CLI documentation](https://hypermapp3r.readthedocs.io/en/latest/wmh_seg.html),
and [method paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8996363/).

## Neurodesk integration gate

No HyperMapp3r module was present when V8 was authored. `module spider
hypermapp3r`, `hypermapp3r-segmentation`, and `hypermapp` all failed on
2026-08-18. The repository declares package version 0.1.0, so the proposed
module contract is `hypermapp3r/0.1.0`; do not use this sheet until that exact
module exists or this reference is updated to the installed pinned version.

The module must bundle the trained model files, TensorFlow 1.15-compatible
runtime, ANTs/c3d dependencies used by the package, and the `hypermapper`
executable. Local installation is no longer supported upstream; package these
dependencies in the module/container instead of installing them in an analysis
workspace.

```bash
set -o pipefail
module -t avail hypermapp3r/0.1.0 2>&1 | grep -F 'hypermapp3r/0.1.0'
module load hypermapp3r/0.1.0
command -v hypermapper
command -v c3d
hypermapper --version >logs/tool-probes/hypermapp3r_version.log 2>&1
hypermapper seg_wmh --help >logs/tool-probes/hypermapp3r_help.log 2>&1
```

Do not assign final Slurm resources until the module builder records a one-case
CPU and/or GPU smoke test with peak memory and runtime.

## Inputs and staging

Require coregistered, bias-corrected T1w and FLAIR plus a validated binary brain
mask. HyperMapp3r writes preprocessing, logs, probability maps, and orientation
intermediates beside the T1w input. Never point it directly at an immutable or
shared input directory. Stage copies inside the job-specific attempt directory.

### Brain-mask dependency

If a validated brain mask is not already available, invoke the
`brain-extraction` skill before authoring the HyperMapp3r job. Do not select or
reconstruct an extraction command inside this reference. The producer skill
owns extraction-tool selection, pinned invocation, grid mapping, publication,
and `brain-extraction-qc`.

First confirm that T1w and FLAIR match in both shape and affine. Then hand off:

```text
EXTRACTION_INPUT=<documented compatible anatomical, normally T1w>
REFERENCE_GRID=<T1w, which must also be the exact FLAIR grid>
FINAL_MASK=<fresh path reserved for the HyperMapp3r brain mask>
```

Continue only after `brain-extraction` publishes a binary mask exactly on that
grid and `brain-extraction-qc` validates it. Assign that artifact to
`BRAIN_MASK`. Do not substitute a nonzero-input mask, a thresholded anatomical,
or HyperMapp3r's own preprocessing intermediates. The HyperMapp3r option is
exactly `--mask "${BRAIN_MASK}"`; it is not a lesion-mask argument.

The final output is returned on the T1w grid, so select this method directly
only when T1w, FLAIR, and brain mask match in both shape and affine. Otherwise
resolve the declared registration and publication grid before invocation; do
not treat equal array dimensions as alignment.

## Invocation

Use the documented default `224multi` model, 20 Monte Carlo samples, and fixed
threshold 0.5 for the initial comparison:

```bash
module load hypermapp3r/0.1.0
CASE_NAME="${CASE_NAME:?set a filesystem-safe case name}"
STAGE="${ATTEMPT_DIR}/hypermapp3r/${CASE_NAME}"
mkdir -p "${STAGE}"
cp --reflink=auto -- "${T1}" "${STAGE}/t1.nii.gz"
cp --reflink=auto -- "${FLAIR}" "${STAGE}/flair.nii.gz"
cp --reflink=auto -- "${BRAIN_MASK}" "${STAGE}/brain_mask.nii.gz"

hypermapper seg_wmh \
  --t1w "${STAGE}/t1.nii.gz" \
  --flair "${STAGE}/flair.nii.gz" \
  --mask "${STAGE}/brain_mask.nii.gz" \
  --out "${STAGE}/wmh_mask.nii.gz" \
  --modelId 224multi --num_mc 20 --thresh 0.5
CANDIDATE_MASK="${STAGE}/wmh_mask.nii.gz"
test -s "${CANDIDATE_MASK}"
```

Do not use `--ign_ort` merely to suppress an orientation warning; use it only
when the header orientation tag is known to be wrong and the actual spatial
relationship has been independently established. Do not add `--force` in a new
attempt directory.

## Outputs and operating point

| Path under the staged subject directory | Meaning | Use |
|---|---|---|
| `wmh_mask.nii.gz` | Binary mask at threshold 0.5 | Publication candidate |
| `<case>_wmh_prob.nii.gz` | Mean Monte Carlo lesion probability on the T1w grid | Retain for QC/calibration |
| `pred_process_wmh/` | Cropped, standardized, and resampled intermediates | Diagnostic context |
| `qc/` and `logs/` | Tool-generated QC and run log | Supplementary evidence |

Threshold and Monte Carlo sample count materially affect the result. Keep 0.5
and 20 fixed for the initial run. Select any alternative at cohort level on
a separate validation set and freeze it before evaluation; never tune per case
or against the evaluation reference.

The probability map is useful for inspecting uncertain boundaries, but it is
not itself a binary deliverable. Independently publish and run lesion QC on the
binary mask; the tool's own montage does not replace the standard exact-grid
containment, FLAIR-signature, completeness, and boundary checks.

## Known signatures

| Signature | Interpretation |
|---|---|
| Missing model JSON or HDF5 weights | Incomplete module/container |
| Writes appear beside the original input | Inputs were not staged; stop before contaminating shared data |
| T1w and FLAIR differ in affine/grid | Ineligible input preparation for this invocation |
| Large probability/binary burden change after threshold adjustment | Expected operating-point sensitivity, not post-processing |
| Orientation warning followed by an implausible mask | Header/orientation handling failure; do not hide it with `--ign_ort` |

Retain the module/help probes, model identity, staged inputs or their hashes,
command, Slurm accounting, logs, probability map, binary candidate, publisher
JSON, and lesion-QC artifacts.
