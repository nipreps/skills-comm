# Grader: `structural-brain-extraction-stroke`

A **consensus-calibrated brain-extraction grader** for a **lesioned (chronic-stroke) brain**
(Aphasia Recovery Cohort, OpenNeuro `ds004884`, five subjects). Companion to the other
`structural-brain-extraction-*` tasks on the **pathology axis**: does the skull-strip keep the
lesion, or carve it out?

Same design as the baseline: score a submission against a STAPLE consensus of a tool panel split
into core / margin / background, thresholds calibrated by leave-one-tool-out. See
[`PROVENANCE.md`](PROVENANCE.md).

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/structural-brain-extraction-stroke/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

Gated so that a submission cannot reproduce the reference instead of solving the
task. Everything governing how a submission is *graded* stays here.

## Shared scorer

No scorer ships here — grade with the shared scorer, pointing `--pack` at this pack:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

## Geometry note

The expert lesion mask was drawn in **T2w** space; it was rigid-registered (FSL FLIRT, 6 DOF) into the
native **T1w** space during ground-truth construction, so the whole task lives in one native T1w
space. See PROVENANCE.

## Layout

```
structural-brain-extraction-stroke/
├── rubrics/policy.json  # shared policy: weights, gates, verdict thresholds. The calibrated half and this subject's own fields are merged in from the gated dataset at fetch time
├── reference/           # consensus + lesion NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-stroke/<subject>/`.
Companion lesion-segmentation task: `clinical-stroke-lesion-segmentation` (same subject).

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in the merged `reference/rubric.json`.

| verdict | meaning |
|---|---|
| `within_reference_variability` | inside the panel's own leave-one-tool-out spread — every metric is at least as good as the weakest the reference tools themselves achieve, so the submission cannot be told apart from a panel member |
| `acceptable` | `quality >= 60` |
| `marginal` | `quality >= 30` |
| `unacceptable` | below that |
| `invalid` | a validity gate failed; `quality` is forced to 0 |

A submission passes when the verdict is `within_reference_variability` or `acceptable`.
`within_reference_variability` is the top grade, not a hedge: it says the answer sits
inside the disagreement the reference itself carries, which is as close as this task can
measure.
