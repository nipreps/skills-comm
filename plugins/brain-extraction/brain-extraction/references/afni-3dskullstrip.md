# AFNI 3dSkullStrip

`3dSkullStrip` uses iterative surface expansion to extract brain from
surrounding tissue. It accepts AFNI datasets and NIfTI inputs and is primarily
documented for human T1-weighted MRI. This sheet describes the installed
interface and outputs without ranking it.

## Availability and resources

- Module: `afni/26.0.07`
- Executables: `3dSkullStrip`, `3dcalc`
- Conservative Slurm starting request: 2 CPUs, 4 GB RAM, 1 hour.

```bash
set -o pipefail
module -t avail afni/26.0.07 2>&1 | grep -F 'afni/26.0.07'
module load afni/26.0.07
command -v 3dSkullStrip
command -v 3dcalc
3dSkullStrip -help >logs/tool-probes/afni_3dskullstrip_help.log 2>&1
```

## Invocation

```bash
module load afni/26.0.07
mkdir -p "${ATTEMPT_DIR}"
3dSkullStrip -input "${INPUT}" \
  -prefix "${ATTEMPT_DIR}/brain.nii.gz" -orig_vol
3dcalc -a "${ATTEMPT_DIR}/brain.nii.gz" \
  -expr 'step(a)' -prefix "${ATTEMPT_DIR}/brain_mask.nii.gz"
```

`3dcalc` binarizes the documented skull-stripped output, not the original input.

## Outputs

| Output | Meaning | Use |
|---|---|---|
| `brain.nii.gz` | Skull-stripped intensity image | Intermediate, not the requested mask |
| `brain_mask.nii.gz` | Binary mask derived from the stripped output | Publication candidate |

Providing a `.nii.gz` prefix prevents an unexpected AFNI HEAD/BRIK output.
`-orig_vol` retains input-grid geometry.

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| HEAD/BRIK files but no NIfTI | Prefix omitted a NIfTI suffix |
| Eye/orbit or inferior leakage | Candidate-quality limitation |
| Frontal or inferior brain clipping | Candidate-quality limitation |
| Empty/whole-volume mask after `3dcalc` | Wrong intermediate or failed extraction |
| Publisher rejects grid, topology, emptiness, or volume | Candidate/output-quality failure |

Options such as `-push_to_edge`, `-shrink_fac`, and `-ld` change the operating
point and must be recorded rather than tried silently in a loop. Retain both
images, the exact command, logs, and publisher JSON.
