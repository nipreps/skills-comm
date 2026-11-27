# BIANCA

BIANCA is FSL's supervised k-nearest-neighbour classifier for white matter
hyperintensities. It learns from manually labelled subjects matched to the
cohort/protocol and produces a probability map. This sheet documents its
prerequisites and outputs without ranking it.

## Availability and resources

- Module: `fsl/6.0.7.22`
- Executable: `bianca`
- Required training resource: either a master file containing manually labelled
  training subjects or saved classifier data.
- Typical features: coregistered FLAIR and T1w, brain mask, optionally spatial
  transforms.
- Conservative Slurm starting request: 4 CPUs, 8 GB RAM, 2 hours; training-set
  size can require more.

```bash
set -o pipefail
module -t avail fsl/6.0.7.22 2>&1 | grep -F 'fsl/6.0.7.22'
module load fsl/6.0.7.22
command -v bianca
bianca --help >logs/tool-probes/bianca_help.log 2>&1
test -r "${MASTERFILE}"
```

The executable can be present while the method remains unusable: without
labelled training rows or previously saved classifier data, there is no model
to apply. An example input with only T1w and FLAIR does
not satisfy this prerequisite by itself.

## Invocation

Column numbers below are examples only; they must match the retained master
file's actual column layout:

```bash
module load fsl/6.0.7.22
mkdir -p "${ATTEMPT_DIR}/bianca"
bianca --singlefile="${MASTERFILE}" \
  --labelfeaturenum="${LABEL_COLUMN}" \
  --brainmaskfeaturenum="${BRAIN_MASK_COLUMN}" \
  --querysubjectnum="${QUERY_ROW}" \
  --trainingnums="${TRAINING_ROWS}" \
  --featuresubset="${FEATURE_COLUMNS}" \
  --trainingpts=2000 --nonlespts=10000 --selectpts=noborder \
  -o "${ATTEMPT_DIR}/bianca/wmh_probability.nii.gz" -v
```

BIANCA also accepts `--loadclassifierdata` instead of training rows when a
compatible saved classifier exists.

## Outputs

| Output | Meaning | Use |
|---|---|---|
| Path passed to `-o` | Continuous WMH probability map | Not yet a binary publication candidate |
| User-created thresholded mask | Binary mask at a declared operating point | Candidate only after threshold choice is recorded |
| Saved classifier data when requested | Reusable trained feature/classifier data | Provenance, not a mask |

A binary deliverable requires an explicit probability threshold or a documented
subject-specific calibration method such as LOCATE. The threshold materially
changes lesion burden and is an analysis decision, not an invisible file-format
conversion.

After recording the chosen operating point, a fixed-threshold conversion is:

```bash
module load fsl/6.0.7.22
fslmaths "${ATTEMPT_DIR}/bianca/wmh_probability.nii.gz" \
  -thr "${BIANCA_THRESHOLD}" -bin \
  "${ATTEMPT_DIR}/bianca/wmh_mask.nii.gz"
CANDIDATE_MASK="${ATTEMPT_DIR}/bianca/wmh_mask.nii.gz"
```

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| No labelled rows and no saved classifier | Missing prerequisite; the tool is not eligible |
| Implausible output with a successful exit | Master-file column indices or transforms may be wrong |
| Continuous-valued “mask” | Probability output was handed off without thresholding |
| Large burden change after threshold change | Expected operating-point sensitivity |
| Query geometry differs from feature/mask geometry | Input/master-file incompatibility |

Retain the master file, training-mask provenance, column mapping, threshold or
calibration decision, command, logs, probability map, and publisher JSON.
