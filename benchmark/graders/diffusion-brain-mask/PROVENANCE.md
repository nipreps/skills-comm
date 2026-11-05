# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 5 subjects of **ds001226 (BTC_preop), `acq-AP` diffusion series**, tag `5.0.1`. Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/diffusion-brain-mask/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Subject and input

The AP series is 96 × 96 × 60 at 2.5 mm isotropic, 102 volumes, shells b = 0 / 700 / 1200 / 2800
with 6 b = 0 volumes. The graded space is the **diffusion grid itself**: a submission masks
whatever b0 it extracts, and every b0 shares that grid, so no resampling is implied.

A submission may mask any b0 it extracts, averaged or not: every b0 shares the diffusion grid,
so the comparison is well defined either way and nothing about the reference requires a
particular choice. What the reference itself was built on is in the gated provenance.

The agent is given the **raw** series. Only `acq-AP` is fetched — the dataset also ships a
reverse-phase-encode PA series, but this task is masking, not distortion correction.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

`reference/consensus_mask.nii.gz` and `consensus_zones.nii.gz` are **not** in git — they belong
on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`diffusion_gt/diffusion-brain-mask/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.
