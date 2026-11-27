# LINDA

LINDA segments chronic stroke lesions from T1w MRI using registration,
left-right asymmetry, and iterative refinement. It provides entry points with
internal skull stripping or with a supplied brain mask. This sheet describes
both interfaces without preferring one tool over another.

## Availability and resources

- Module: `linda/0.5.1`
- Executables: `linda_predict.sh`, `linda_predict_with_mask.sh`
- Observed runtime varies materially by image and container build: about
  25–50 minutes on tested 1 mm T1w volumes.
- Conservative Slurm starting request: 4 CPUs, 16 GB RAM, 2 hours.

```bash
set -o pipefail
module -t avail linda/0.5.1 2>&1 | grep -F 'linda/0.5.1'
module load linda/0.5.1
command -v linda_predict.sh
command -v linda_predict_with_mask.sh
linda_predict_with_mask.sh --help
```

## Inputs and invocations

- Required: T1w NIfTI.
- Optional for the masked entry point: an already validated brain mask on the
  T1w grid.
- Output grid: native T1w grid for `*_native` files.

Standard entry point, which performs its own skull stripping. The installed
wrapper passes the input filename to R without forwarding the requested output
directory for NIfTI products. Therefore copy the T1w into the attempt directory
first; LINDA will write its fixed-name images beside that copy. This also
prevents a symlinked input from contaminating the canonical source
directory.

```bash
module load linda/0.5.1
mkdir -p "${ATTEMPT_DIR}/linda"
cp --preserve=timestamps "${T1}" "${ATTEMPT_DIR}/linda/input_T1w.nii.gz"
linda_predict.sh \
  "${ATTEMPT_DIR}/linda/input_T1w.nii.gz" \
  "${ATTEMPT_DIR}/linda"
CANDIDATE_MASK="${ATTEMPT_DIR}/linda/Prediction3_native.nii.gz"
```

Entry point using an existing validated brain mask:

```bash
module load linda/0.5.1
mkdir -p "${ATTEMPT_DIR}/linda"
linda_predict_with_mask.sh \
  --t1 "${T1}" --mask "${BRAIN_MASK}" \
  --outdir "${ATTEMPT_DIR}/linda" --quiet
```

Do not invent a brain mask to use the second interface. When no validated mask
exists, the standard interface remains a documented invocation.

## Outputs

LINDA uses fixed names rather than names derived from the input. For the
standard installed wrapper below, “path under `--outdir`” is true only because
the staged input itself is placed in that directory. The second positional
argument receives RData/provenance, but does not relocate the NIfTI products.

| Path under `--outdir` | Meaning | Use |
|---|---|---|
| `Prediction3_native.nii.gz` | Final binary lesion mask in native T1 space | Publication candidate |
| `Prediction3_probability_native.nii.gz` | Native-space probability map | Retain, not a binary deliverable |
| `Prediction3_graded_map.nii.gz` | Graded prediction | Not the requested mask |
| `Prediction3_template.nii.gz` | Template-space prediction | Not a native-grid substitute |
| `Lesion_in_MNI.nii.gz` | MNI-space lesion | Not a native-grid substitute |
| `Prediction1.nii.gz`, `Prediction2.nii.gz` | Earlier iterations | Superseded by Prediction3 |
| `Mask.lesion*.nii.gz` | Intermediate masks, sometimes brain-sized | Never use as the lesion deliverable |
| `BrainMask.nii.gz` | Brain mask LINDA used | Not the lesion mask |
| `Console_Output.txt`, `Session_Info.txt` | Progress and provenance | Retain for diagnosis |

Use exactly `Prediction3_native.nii.gz` beside the staged T1w. If another
reference grid is required, use the skill's bundled nearest-neighbour resampling
helper before publication.

## Known signatures

| Signature | Interpretation |
|---|---|
| Successful run followed by “no image files match” | Wrapper guessed an input-derived filename instead of the fixed output name |
| Successful run followed by missing `Prediction3_native.nii.gz` under the second positional directory | Input was not staged there; this wrapper writes NIfTI files beside its input |
| Candidate volume near whole-brain size | A `Mask.lesion*` intermediate was selected |
| Template/MNI geometry | A non-native output was selected |
| Little log movement but changing `Console_Output.txt` stages over ~25 minutes | Normal computation, not a stall |
| Failure beside a large cavity with internal skull stripping | Candidate/tool limitation; preserve output and logs for classification |

Retain the module probe, Slurm accounting, console/session logs, output listing,
and publisher JSON.
