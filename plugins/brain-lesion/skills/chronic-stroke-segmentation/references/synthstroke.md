# SynthStroke

SynthStroke segments chronic stroke lesions from T1w MRI. The installed
baseline model produces a native T1-grid binary lesion mask plus probability
outputs. This sheet describes its interface and files without ranking it.

## Availability and resources

- Module: `synthstroke/0.0.0`
- Executable: `synthstroke`
- Conservative Slurm starting request: 4 CPUs, 16 GB RAM, 2 hours.

Neurodesk's module catalog exposes the literal module name and version
`synthstroke/0.0.0`; it is the tested module identifier, not an unfilled
version placeholder. Verify it with the exact `module spider`/availability
probe below on the target cluster.

```bash
set -o pipefail
module -t avail synthstroke/0.0.0 2>&1 | grep -F 'synthstroke/0.0.0'
module load synthstroke/0.0.0
command -v synthstroke
synthstroke --help
```

## Inputs and invocation

- Required: T1w NIfTI.
- Output grid: native T1w grid.

```bash
module load synthstroke/0.0.0
mkdir -p "${ATTEMPT_DIR}/synthstroke"
synthstroke --input "${T1}" \
  --outdir "${ATTEMPT_DIR}/synthstroke" --tta
```

## Outputs

| Path under `--outdir` | Meaning | Use |
|---|---|---|
| `prediction_lesion_mask.nii.gz` | Binary chronic-stroke mask in T1 space | Publication candidate |
| `prediction_prediction.nii.gz` | Model label output | Retain, but not the requested candidate |
| `prediction_prob_class_*.nii.gz` | Class probability maps | Not publication candidates |

Use exactly `prediction_lesion_mask.nii.gz`. Class numbering varies by model,
so searching for a presumed last probability class is unsafe.

If the requested reference differs from T1w, move the binary candidate with the
skill's nearest-neighbour `resample_mask.py`, then publish against the requested
reference. Do not re-threshold probability maps.

## Known signatures

| Signature | Interpretation |
|---|---|
| `Done. Output saved`, followed by a wrapper looking for class-4/class-5 | Wrapper/output-contract failure; the documented binary output may already exist |
| Candidate differs from requested grid | Expected native-grid difference; use documented nearest-neighbour resampling |
| `0 voxels above threshold 0.5` | Empty candidate from the tool |
| MONAI warnings followed by `Done. Output saved` | Non-fatal dependency warnings |
| Internal holes listed in publisher `warnings` | Lesion QC finding, not automatic publication failure |

Retain stdout/stderr, the complete output directory, and publisher JSON.
