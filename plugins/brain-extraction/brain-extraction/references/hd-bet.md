# HD-BET

HD-BET is a deep-learning brain-extraction method trained across MRI scanners
and contrasts. The installed interface supports GPU and CPU execution. This
sheet documents both without ranking them.

## Availability and resources

- Module: `hdbet/2.0.1`
- Executable: `hd-bet`
- Conservative GPU request: 4 CPUs, 8 GB RAM, 1 hour, one GPU only when Slurm
  advertises it.
- Conservative CPU request: 4 CPUs, 8 GB RAM, 2 hours.

```bash
set -o pipefail
module -t avail hdbet/2.0.1 2>&1 | grep -F 'hdbet/2.0.1'
module load hdbet/2.0.1
command -v hd-bet
module help hdbet/2.0.1 >logs/tool-probes/hdbet_help.log 2>&1
```

The module help is the lightweight interface probe; `hd-bet -h` can spend more
than 20 seconds initializing before printing anything.

## Invocations

GPU/default interface on an eligible GPU node:

```bash
module load hdbet/2.0.1
mkdir -p "${ATTEMPT_DIR}"
hd-bet -i "${INPUT}" -o "${ATTEMPT_DIR}/brain.nii.gz" \
  --save_bet_mask
```

CPU interface:

```bash
module load hdbet/2.0.1
mkdir -p "${ATTEMPT_DIR}"
hd-bet -i "${INPUT}" -o "${ATTEMPT_DIR}/brain.nii.gz" \
  -device cpu --disable_tta --save_bet_mask
```

## Outputs

For an output image named `brain.nii.gz`, HD-BET writes:

| Output | Meaning | Use |
|---|---|---|
| `brain.nii.gz` | Brain-extracted intensity image | Not the requested mask |
| `brain_bet.nii.gz` | Binary brain mask, with `_bet` inserted before the extension | Publication candidate |

The caller controls the output image name. In installed HD-BET 2.0.1, derive
the mask name by inserting `_bet` before `.nii.gz`. The mask is deleted after
the brain image is created unless `--save_bet_mask` is present, so that flag is
required for a mask deliverable. Do not threshold the intensity output.

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| CUDA out-of-memory/device error | GPU execution incompatibility |
| CPU execution with TTA enabled appears very slow | Expected resource/runtime difference |
| Help probe appears to hang during imports | Initialization overhead; use module help and PATH probe |
| Brain image exists but `_bet.nii.gz` does not | `--save_bet_mask` was omitted, so HD-BET removed its intermediate mask |
| `brain.nii.gz` handed off as mask | Output-contract violation |
| Publisher rejects grid, topology, emptiness, or volume | Candidate/output-quality failure |

Device choice and `--disable_tta` change runtime or the operating point and must
be recorded. Retain both outputs, logs, resource probe, and publisher JSON.
