# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 5 subjects of **MR-ART `ds004173`, `acq-headmotion2`** (native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-motion/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Subject

MR-ART pairs a motion-free scan with two motion-corrupted scans of the same subject. The graded
input is the **high-motion** scan (`acq-headmotion2`, quality score 3/3 — the worst tier);
`acq-standard` is the clean control.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are **not** stored in git — they live on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-motion/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **Curating the panel uses judgement.** ANTs is dropped objectively (coherence); BET is dropped for
  neck over-inclusion.
- **Consensus leans on its tightest member.** The core is close to that one tool's mask. A more
  rigorous alternative is a clean-scan-derived truth (extract from `acq-standard`, register onto the
  motion scan), which does not depend on how tools behave under motion.
