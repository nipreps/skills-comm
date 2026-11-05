# Grader: `clinical-wmh-segmentation`

Grades **white-matter-hyperintensity (WMH) segmentation** on a FLAIR image against an **expert mask**,
with thresholds **data-derived from inter-rater agreement**. Dementia / small-vessel-disease axis;
companion to `clinical-stroke-lesion-segmentation`.

Data: **WMH Segmentation Challenge 2017**, five cases across its three acquisition sites. These
are clinical FLAIRs carrying many small, multi-focal foci, which is the case where **Dice alone is
misleading** — a small boundary slip on tiny lesions tanks it — and **lesion-wise detection
matters**.

![How a WMH submission is graded: several experts trace the same FLAIR and the primary mask becomes the reference; a submission passes four validity gates, then earns a 0-100 quality score weighting Dice 40%, lesion-wise F1 40% and volume error 20%; altered copies of the expert mask show that dilating by 2 voxels finds every lesion yet scores marginal.](wmh_grading.png)

*Full size: [`wmh_grading.png`](wmh_grading.png).*

## The reference

Independent expert observers traced each case, and the primary observers' mask is the
reference — not a consensus of tools, and no tool was run to make it. The remaining
observers are what the thresholds are derived from: they say how well one expert agrees
with another, which is the most a submission can be asked for. Who traced what, and the
agreement between them, are in `calibration/clinical-wmh-segmentation/PROVENANCE.md`
inside the gated reference dataset [`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

It is gated because the mask is the answer: the grader must be able to see it and a
submission must not. Everything governing how a submission is *graded* stays here and in
[`rubrics/`](rubrics/).

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_lesion_seg.py --pred agent_wmh.nii.gz --pack . [--json result.json]
```

The submission is a **binary WMH mask in native FLAIR space**. Same scorer as the stroke lesion task
(Dice + lesion-wise detection F1 + volume error); only the reference and the calibrated thresholds
differ. WMH weighting puts **lesion-wise F1 on par with Dice** (0.4 / 0.4 / 0.2) because the lesions
are many and small.

## Data access — fully open, agent-runnable

The images come from **DataverseNL** (DOI `10.34894/AECRSD`) via the open Dataverse access API — a
plain `curl`, no login or Data-Use-Agreement — so an agent can fetch the FLAIR itself. The expert
masks are **grader-side only**; they are never in the agent's input.

## Subjects

Five subjects from the challenge's training set, spanning its three scanner sites. Each
is graded against its own rubric in `rubrics/<subject>.json`; there is no shared default,
and the grader refuses to run if the selected rubric does not describe the fetched
reference.

| subject | scanner | grid |
|---|---|---|
| `Amsterdam_GE3T_100` | Amsterdam GE3T | 132x256x83 |
| `Amsterdam_GE3T_114` | Amsterdam GE3T | 132x256x83 |
| `Singapore_52` | Singapore | 232x256x48 |
| `Utrecht_33` | Utrecht | 240x240x48 |
| `Utrecht_39` | Utrecht | 240x240x48 |

Lesion load, focus counts and each subject's thresholds are in the gated
`calibration/clinical-wmh-segmentation/PROVENANCE.md`; the thresholds themselves ship with
the per-subject calibration the grader merges at scoring time.

Thresholds differ per subject because they are measured per subject: the challenge ships
two additional raters, and full marks is their mean agreement with the primary reference.
Full marks therefore spans a wide range in Dice across these five — a fixed threshold
would be wrong for most of them.

Selection is recorded in `subjects.tsv` in the build directory, including why each of the
other 55 training subjects was not used. Two constraints applied: rater agreement rises
with lesion load, so subjects below a mean of 0.70 were dropped as their envelope asks
almost nothing of a submission; and subjects carrying the dataset's label 2 (other
pathology) were avoided, since the graded reference is label 1 only and a submission that
segments the other pathology would be charged false positives for finding something real.

## Layout

```
clinical-wmh-segmentation/
├── rubrics/<subject>.json          # inter-rater-derived thresholds, weights, grid; records the O3/O4 metrics
├── score_lesion_seg.py  # Dice + lesion-wise F1 + volume error
├── reference/           # primary expert WMH mask — fetched from the Hub
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `clinical_gt/clinical-wmh-segmentation/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubrics/<subject>.json`.

| verdict | meaning |
|---|---|
| `within_reference_variability` | inside the published inter-rater ceiling recorded in `threshold_basis` — the reference is one expert tracing, so there is no panel spread to measure against and the bar comes from the literature |
| `acceptable` | `quality >= 60` |
| `marginal` | `quality >= 30` |
| `unacceptable` | below that |
| `invalid` | a validity gate failed; `quality` is forced to 0 |

A submission passes when the verdict is `within_reference_variability` or `acceptable`.
`within_reference_variability` is the top grade, not a hedge: it says the answer sits
inside the disagreement the reference itself carries, which is as close as this task can
measure.


## Reference copies

`not_reference_copy` is the fifth gate. These references are published alongside the images
the task hands out, so a submission can be a download rather than a segmentation; a Dice at or
above 0.995 is refused as a copy and the run is **invalid**. The threshold sits far above what
segmenting the image reaches — the best published method on this reference, and the agreement
between two experts tracing the same scan, are both well below it — so it cannot catch an honest
answer.
