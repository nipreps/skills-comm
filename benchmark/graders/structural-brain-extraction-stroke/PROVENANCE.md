# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **Aphasia Recovery Cohort (ARC), OpenNeuro `ds004884`,
`sub-M2191` `ses-681`** (chronic left-MCA stroke, native T1w space). Not re-derived at grade time.

## Subject and geometry

ARC ships, per subject, a T1w and a T2w plus an **expert manual lesion mask drawn in T2w space**. The
graded image is the T1w. To keep everything in one native space (option A), the T2w was rigid-registered
to the T1w (FSL FLIRT, 6 DOF) and the lesion mask carried into T1w space with nearest-neighbour
interpolation (`lesion_in_T1.nii.gz`, 82.8 cm³).

## Panel curation

Four tools were run on the T1w (FSL BET, HD-BET, AFNI `3dSkullStrip`, SynthStrip). The chronic infarct
is a fluid-filled cavity, dark and CSF-like on T1 — a natural failure point:

| tool       | brain vol | lesion retained |
|------------|-----------|-----------------|
| HD-BET     | 1164 cm³  | 99.6 %          |
| SynthStrip | 1305 cm³  | 100 %           |
| AFNI       | 1157 cm³  | 93.7 %          |
| **FSL BET**| 1039 cm³  | **52 %**        |

- **Kept (reference): HD-BET, AFNI, SynthStrip** — they retain the lesion.
- **Dropped: FSL BET** — carves out ~half the lesion; kept as a scored candidate (comes out `invalid`).

## Calibration steps

1. **Geometry harmonisation** onto the reference grid (GRID_TOOL = HD-BET); AFNI's header-only
   deoblique read on the native grid (`grid.raw_affine` carried for the same case in a submission).
2. **STAPLE consensus** of the three reference tools → `consensus_mask.nii.gz` (1195 cm³; core 1121 /
   margin 188). The lesion sits inside the core (all three retain it).
3. **Zones** → `consensus_zones.nii.gz` (0 = background, 1 = margin, 2 = core).
4. **τ** = 95th percentile pairwise surface disagreement ≈ 5.4 mm.
5. **Envelope** by leave-one-tool-out → per-metric median (full marks) / worst (pass line).
6. **Gate caps:** `focal_max_cm3` (5.0–12.5 cm³ here, LOTO-calibrated on the largest held-out miss that
   survives a max(1.5 mm, one voxel) shave), `focal_bg_max_cm3` = 40 cm³ (fixed, measured the same
   way), and **`lesion_retained_min`
   = 0.85** (fixed) — a competent stripper keeps ≥ 94 % of the lesion; BET's 52 % fails with margin.

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
