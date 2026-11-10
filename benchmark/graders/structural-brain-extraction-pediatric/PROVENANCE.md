# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 5 subjects of **ds000228** (children aged 3.5–4.8, native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-pediatric/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Subject selection

ds000228 (Richardson, "Development of the social brain") — children and adults; the graded
subjects are children.

Candidates are screened for field-of-view truncation, measured as the percentage of the brain
surface adjacent to zero-valued data. The screen exists because a candidate was found whose T1w
carries a planar zero-cut through one side of the brain — not defacing, and not obvious unless
looked for, with several percent of the brain surface sitting on the cut. A mask of a truncated
brain is a fair mask of the wrong anatomy, and no panel agreement would reveal that. The graded
subjects all have full coverage.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-pediatric/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **Consensus leans on the tighter members.** Where one is more inclusive about the outer CSF
  rim, that rim lands in the margin rather than the core, so it is never scored.
