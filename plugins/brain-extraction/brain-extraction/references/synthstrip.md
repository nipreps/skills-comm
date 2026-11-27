# SynthStrip

SynthStrip is a contrast-tolerant brain-extraction method distributed with
FreeSurfer. This sheet describes compatibility, invocation, and exact outputs
without ranking it.

## Availability and resources

- Module: `freesurfer/8.2.0`
- Executable: `mri_synthstrip`
- Inputs: 3D T1w, T2w, FLAIR, DWI/b0, and other MRI contrasts supported by the
  model.
- Conservative Slurm starting request: 4 CPUs, 8 GB RAM, 1 hour.

```bash
set -o pipefail
module -t avail freesurfer/8.2.0 2>&1 | grep -F 'freesurfer/8.2.0'
module load freesurfer/8.2.0
command -v mri_synthstrip
mri_synthstrip --help
```

## Invocation

```bash
module load freesurfer/8.2.0
mkdir -p "${ATTEMPT_DIR}"
mri_synthstrip \
  -i "${INPUT}" \
  -o "${ATTEMPT_DIR}/brain.nii.gz" \
  -m "${ATTEMPT_DIR}/brain_mask.nii.gz"
```

## Outputs

| Output | Meaning | Use |
|---|---|---|
| `brain_mask.nii.gz` (the `-m` path) | Binary brain mask on the input grid | Publication candidate |
| `brain.nii.gz` (the `-o` path) | Brain-extracted intensity image | Never publish as the mask |

The output names are caller-selected; the semantic distinction between `-m`
and `-o` is the reliable contract.

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| Lmod probe for a module named `mri_synthstrip` fails | Executable name was mistaken for module name |
| Binary absent after loading FreeSurfer | Module/environment incompatibility |
| FreeSurfer licence error | Tool-startup/environment failure |
| Intensity-valued `-o` file handed off | Output-contract violation |
| Publisher rejects grid, topology, emptiness, or volume | Candidate/output-quality failure |

Retain module/PATH probes, job logs, both outputs, and publisher JSON.
