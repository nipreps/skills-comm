# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **ds000228 `sub-pixar017`** (~3.6 yo, native T1w space).
Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-pediatric/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Subject selection

ds000228 (Richardson, "Development of the social brain") — children + adults. An earlier pick,
**sub-pixar009, was rejected**: its T1w has a field-of-view truncation (a planar zero-cut through the right
side of the brain — not defacing; ~6-8 % of the brain surface sat on the cut). Candidates were screened with
an FOV-completeness metric (% of brain surface adjacent to zero-data); **sub-pixar017** was
the cleanest (0.2 %) with full coverage.

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

- **Consensus leans on the tighter tools.** The loosest member's CSF rim lands in the margin, not the core.
