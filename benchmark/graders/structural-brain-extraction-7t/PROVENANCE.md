# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on the benchmark subject **CEREBRUM-7T `ds003642`,
`sub-025` `ses-003`** (7T MP2RAGE, 0.63 mm isotropic, native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-7t/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Subject and inputs

CEREBRUM-7T provides MP2RAGE INV1 / INV2 / UNI (BIDS `T1w`) at 0.63 mm on a 7T scanner. The graded
input is the **UNI** image. Its background is salt-and-pepper noise (≈ 80 % of background voxels are
"bright"); the **INV2** magnitude is clean outside the head and is used only to build the reference's
cleaned image.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are **not** in git — they live on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-7t/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **τ is wide.** The quality score is permissive by design here; the gates do the discrimination.
