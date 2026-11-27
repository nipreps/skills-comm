# ANTs BrainExtraction

`antsBrainExtraction.sh` performs template-based brain extraction by registering
an anatomical template and its brain-probability mask to the subject. It is not
turnkey without compatible template resources. This sheet documents the
installed interface and exact outputs without ranking it.

## Availability and resources

- Module: `ants/2.6.5`
- Executable: `antsBrainExtraction.sh`
- Required external resources: anatomical extraction template and matching
  probability mask.
- Conservative Slurm starting request: 4 CPUs, 16 GB RAM, 4 hours.

```bash
set -o pipefail
module -t avail ants/2.6.5 2>&1 | grep -F 'ants/2.6.5'
module load ants/2.6.5
command -v antsBrainExtraction.sh
antsBrainExtraction.sh -h >logs/tool-probes/ants_brain_extraction_help.log 2>&1
test -r "${TEMPLATE}"
test -r "${TEMPLATE_PROBABILITY_MASK}"
```

The tool is compatible only when the two template files are already available
and their provenance is recorded. Module availability alone is insufficient.

## Invocation

```bash
module load ants/2.6.5
mkdir -p "${ATTEMPT_DIR}"
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS="${SLURM_CPUS_PER_TASK:-4}"
OUTPUT_PREFIX="${ATTEMPT_DIR}/ants_"
antsBrainExtraction.sh \
  -d 3 -a "${INPUT}" \
  -e "${TEMPLATE}" -m "${TEMPLATE_PROBABILITY_MASK}" \
  -o "${OUTPUT_PREFIX}" -u 0
```

`-u 0` fixes the random seed. Exact bitwise reproducibility additionally
requires controlling thread count.

## Outputs

| Output | Meaning | Use |
|---|---|---|
| `${OUTPUT_PREFIX}BrainExtractionMask.nii.gz` | Binary brain mask on the subject grid | Publication candidate |
| `${OUTPUT_PREFIX}BrainExtractionBrain.nii.gz` | Brain-extracted intensity image | Not the requested mask |
| `${OUTPUT_PREFIX}BrainExtractionPrior*.nii.gz` | Warped prior/intermediate files | Diagnostic only |
| registration transforms/warps | Template-to-subject alignment | Retain for diagnosis |

## Known signatures and limitations

| Signature | Interpretation |
|---|---|
| Template or probability mask absent | Prerequisite incompatibility; do not submit |
| Registration divergence or implausible warp | Template/input incompatibility or orientation problem |
| Very long runtime with no configured threads | Resource configuration issue |
| Template-space or prior file handed off | Output-contract violation |
| Publisher rejects grid, topology, emptiness, or volume | Candidate/output-quality failure |

Do not download an unpinned template opportunistically during task execution.
Retain template provenance, exact command, transforms, logs, and publisher JSON.
