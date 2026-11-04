# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 5 subjects of **Aphasia Recovery Cohort (ARC), OpenNeuro `ds004884`** (chronic left-MCA stroke, native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-stroke/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Subject and geometry

ARC ships, per subject, a T1w and a T2w plus an **expert manual lesion mask drawn in T2w space**. The
graded image is the T1w. To keep everything in one native space (option A), the T2w was rigid-registered
to the T1w (FSL FLIRT, 6 DOF) and the lesion mask carried into T1w space with nearest-neighbour
interpolation (`lesion_in_T1.nii.gz`, 82.8 cm³).

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

`consensus_mask.nii.gz`, `consensus_zones.nii.gz`, `lesion_mask.nii.gz` are on the Hugging Face Hub
(`neurodeskorg/skills-comm-ground-truth`, `structural_gt/structural-brain-extraction-stroke/<subject>/`). Fetch before grading; see
`reference/README.md`.

## Caveats

- **Registration error.** The lesion mask is drawn on T2w and rigidly mapped to T1w; sub-voxel
  misalignment is possible but small (intra-session, 1 mm iso, rigid).
- **The lesion is in the core**, so BET's drop already trips `no_focal_core_loss`; `lesion_retained`
  makes the failure explicit and would still fire if the lesion fell in the margin.
