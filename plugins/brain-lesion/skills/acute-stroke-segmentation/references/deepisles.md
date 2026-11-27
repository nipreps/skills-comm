# DeepISLES

DeepISLES segments acute ischaemic stroke from DWI and ADC, with optional
FLAIR. It is a GPU-dependent Python ensemble in this deployment; this sheet
describes compatibility and files without ranking it against another tool.

## Availability and resources

- Module: `deepisles/1.1`
- Interface: Python API through the bundled `scripts/run_deepisles.py`; there
  is no supported command-line executable.
- Hardware: NVIDIA GPU required.
- Conservative Slurm starting request: 4 CPUs, 16 GB RAM, 4 hours, one GPU when
  the live partition advertises a GPU GRES.

```bash
set -o pipefail
nvidia-smi
module -t avail deepisles/1.1 2>&1 | grep -F 'deepisles/1.1'
module load deepisles/1.1
python -c "import sys; sys.path.append('/opt/DeepIsles'); from src.isles22_ensemble import IslesEnsemble; print(IslesEnsemble.__name__)"
```

## Inputs and invocation

- Required: DWI and ADC.
- Optional: FLAIR.
- DWI defines the native output grid; ADC is aligned internally.

```bash
module load deepisles/1.1
FLAIR_ARGS=()
if [ -n "${FLAIR:-}" ]; then FLAIR_ARGS=(--flair "${FLAIR}"); fi
python "${SKILL_DIR}/scripts/run_deepisles.py" \
  --dwi "${DWI}" --adc "${ADC}" "${FLAIR_ARGS[@]}" \
  --work-dir "${ATTEMPT_DIR}/deepisles_work" \
  --output-dir "${ATTEMPT_DIR}/deepisles_output"
```

## Outputs

| Path under `--output-dir` | Meaning | Use |
|---|---|---|
| `lesion_msk.nii.gz` | Binary acute-stroke mask in DWI space | Publication candidate |
| `output_screenshot.png` | Tool-rendered overview when produced | Supplementary QC only |
| `output_teams/` | Individual ensemble results when enabled | Not the requested mask |
| `output_mni/` | Optional normalized outputs | Not a native-grid substitute |

Use exactly `${ATTEMPT_DIR}/deepisles_output/lesion_msk.nii.gz`. Do not select a
team output or derive a mask by thresholding DWI/ADC.

## Known signatures

| Signature | Interpretation |
|---|---|
| `nvidia-smi` absent/fails | Hardware incompatibility; the tool was not attempted |
| Import failure for `src.isles22_ensemble` | Module/environment probe failure |
| Atlas download or `data/atlas` path error | Tool-startup/environment failure |
| Python nonzero exit or missing `lesion_msk.nii.gz` | Tool-execution failure |
| Candidate rejected by the publisher | Output-contract or candidate-quality failure |

Retain the complete probe, stdout/stderr, attempt tree, and publisher JSON.
