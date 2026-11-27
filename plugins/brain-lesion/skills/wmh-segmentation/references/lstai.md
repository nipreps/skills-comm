# LST-AI experimental transfer mode

LST-AI is a three-model 3D U-Net ensemble trained for multiple-sclerosis lesion
segmentation. Vascular WMH and MS lesions overlap in FLAIR appearance, so this
sheet permits an explicitly selected research comparison on confirmed vascular
WMH. It is a second-line off-domain candidate, not an aetiology classifier or a
validated vascular-WMH default.

## Availability, evidence, and resources

- Module: `lstai/1.2.0` (the module name is `lstai`, not `lst-ai`).
- Executable: `lst`.
- Inputs: gzipped 3D T1w and 3D FLAIR NIfTI images.
- Training evidence: 491 paired T1w/FLAIR scans from patients with MS; published
  external evaluation used 103 MS cases. No vascular-WMH validation was reported.
- Intended use: research only; the authors do not claim clinical validation.
- Conservative Slurm starting request: 8 CPUs, 24 GB RAM, 3 hours. Probe GPU
  capacity first; otherwise declare `--device cpu`.

```bash
set -o pipefail
module -t avail lstai/1.2.0 2>&1 | grep -F 'lstai/1.2.0'
module load lstai/1.2.0
command -v lst
lst --help >logs/tool-probes/lstai_help.log 2>&1
```

The installed Neurodesk module and its help must both be retained. The model
downloads missing weights when first invoked; a network/download failure is an
availability failure and must not trigger an unpinned installation.

## Invocation for confirmed vascular WMH

Use this method only after a compatible vascular-WMH method has failed or
remained Borderline on lesion QC, or after all such methods are unavailable.
Retain that evidence, tell the user LST-AI was trained and validated for MS, and
obtain their explicit tool choice. Disable McDonald-criteria annotation, retain
the ensemble probabilities, and use the published fixed threshold:

```bash
module load lstai/1.2.0
mkdir -p "${ATTEMPT_DIR}/lstai/output" "${ATTEMPT_DIR}/lstai/temp"
lst --t1 "${T1}" --flair "${FLAIR}" \
  --output "${ATTEMPT_DIR}/lstai/output" \
  --temp "${ATTEMPT_DIR}/lstai/temp" \
  --segment_only --probability_map --threshold 0.5 \
  --device cpu --threads "${SLURM_CPUS_PER_TASK:-8}"
CANDIDATE_MASK="${ATTEMPT_DIR}/lstai/output/space-flair_seg-lst.nii.gz"
test -s "${CANDIDATE_MASK}"
```

Do not add `--stripped` unless both inputs are genuinely skull-stripped. LST-AI
cannot accept a mixture of stripped and non-stripped inputs. Do not use its
default segmentation-plus-annotation mode for vascular WMH: periventricular,
juxtacortical, and infratentorial McDonald labels are MS-specific and would
misstate the result.

## Outputs and operating point

| Path | Meaning | Use |
|---|---|---|
| `output/space-flair_seg-lst.nii.gz` | Binary ensemble lesion mask in original FLAIR space | Publication candidate |
| `output/lesion_stats.csv` | Component/volume summary | Quantitative cross-check |
| `temp/sub-X_ses-Y_space-FLAIR_seg-lst_prob.nii.gz` | Ensemble probability map in FLAIR space | Retain for calibration/QC |
| `temp/*_seg-lst_prob_[123].nii.gz` | Individual network probabilities | Diagnostic disagreement |

The documented default threshold is `0.5`; keep it fixed for the first
comparison. Any alternative threshold is a cohort-level analysis decision that
must be chosen on a separate validation set and frozen before evaluation. Never
tune it per case or against the evaluation reference.

Although the candidate is described as FLAIR-space output, still verify exact
shape and affine and use the main skill's nearest-neighbour grid helper if only
tool reorientation or header rounding differs.

## Interpretation and known signatures

| Signature | Interpretation |
|---|---|
| Output resembles vascular WMH | Transfer may be useful; it does not establish MS |
| High juxtacortical/infratentorial false-positive burden | Expected risk from MS-domain training |
| Confluent vascular WMH is fragmented or under/over-called | Domain-shift failure; do not repair with handwritten morphology |
| Weights cannot be found or downloaded | Tool unavailable in this environment/run |
| Only annotated output is present | Wrong mode; rerun once with `--segment_only` |

Report the method as `LST-AI 1.2.0, experimental MS-to-vascular-WMH transfer`.
Retain the availability probe, command, Slurm accounting, logs, binary mask,
probability maps, stats, publisher JSON, and lesion-QC artifacts.
