# FSL BET

BET extracts a brain surface from an intensity image using a deformable model.
Its behavior depends on image contrast and the fractional intensity parameter.
This sheet documents the conventional invocation and exact mask filename
without ranking it.

## Availability and resources

- Module: `fsl/6.0.7.22`
- Executable: `bet`
- Input compatibility: conventional T1w is the documented V4 use. Computed or
  noisy contrasts such as raw MP2RAGE UNI require particular caution.
- Conservative Slurm starting request: 2 CPUs, 4 GB RAM, 30 minutes.

```bash
set -o pipefail
module -t avail fsl/6.0.7.22 2>&1 | grep -F 'fsl/6.0.7.22'
module load fsl/6.0.7.22
command -v bet
bet >logs/tool-probes/bet_help.log 2>&1 || test -s logs/tool-probes/bet_help.log
```

## Invocation

The conventional fixed invocation documented for this tool is:

```bash
module load fsl/6.0.7.22
mkdir -p "${ATTEMPT_DIR}"
BET_PREFIX="${ATTEMPT_DIR}/brain"
bet "${INPUT}" "${BET_PREFIX}" -f 0.5 -m -R
```

Use that command unchanged. `-m` and `-R` are boolean flags. `-S` is also a
boolean optional cleanup mode, is not part of this validated invocation, and
must never be written as `-S 1` (BET interprets `1` as an unexpected argument
and exits after printing usage). Do not add `-S`, `-B`, or another variation
without an explicit method decision.

Do not select this conventional BET sheet for a high-resolution 7T or raw
MP2RAGE/UNI input merely because the module is available. Choose only a tool
whose own reference documents compatibility with that contrast.

## Outputs

| Output | Meaning | Use |
|---|---|---|
| `${BET_PREFIX}_mask.nii.gz` | Binary mask created by `-m` | Publication candidate |
| `${BET_PREFIX}.nii.gz` | Brain-extracted intensity image | Never publish as the mask |

Do not give the prefix a `_mask` suffix and then select the prefix image; BET
always appends `_mask` to create the binary candidate.

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| BET wrote a binary mask, followed by an ad hoc Nibabel exception | Wrapper failure, not tool failure |
| Logged values `[0. 1.]` followed by a custom non-binary error | Wrapper/output-validation failure |
| Prefix intensity image handed off | Output-contract violation |
| Publisher rejects topology, grid, emptiness, or volume | Candidate/output-quality failure |

Parameter tuning changes the operating point and should be recorded as a
scientific choice rather than silently tried in a loop. Publisher volume
rejection is not permission to lower `-f` repeatedly until the gate passes.
Retain command, job logs, both outputs, and publisher JSON.
