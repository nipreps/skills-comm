# Grader: `clinical-stroke-lesion-segmentation`

Grades a **stroke-lesion segmentation** against an **expert manual mask** (Aphasia Recovery Cohort,
OpenNeuro `ds004884`, five subjects). Step 2 of the stroke pair; step 1 is
`structural-brain-extraction-stroke` (same subject).

## The reference

An expert traced each lesion by hand and the tracing ships with the dataset. That tracing
is the reference — not a consensus of tools, and no tool was run to make it. How it is
brought onto the grid the agent is given, and the published results the thresholds are
read from, are in `calibration/clinical-stroke-lesion-segmentation/PROVENANCE.md` inside
the gated reference dataset [`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

It is gated because the mask is the answer: the grader must be able to see it and a
submission must not. Everything governing how a submission is *graded* stays here and in
[`rubrics/`](rubrics/).

## Why an expert mask, not a consensus

The brain-extraction and tissue graders score against a *tool consensus* — valid because
skull-strippers largely agree. **Lesion segmentation is different:** automated lesion tools disagree
wildly, so a tool-consensus would be untrustworthy. Here the dataset's **expert manual tracing IS the
ground truth**. Because one subject gives no leave-one-out envelope, the pass/fail thresholds are
**fixed from the literature** (chronic-stroke inter-rater Dice ≈ 0.70), recorded in `rubric.json`.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_lesion_seg.py --pred agent_lesion.nii.gz --pack . [--json result.json]
```

The submission is a **binary lesion mask in native T1w space**.

## Metrics

Dice alone is misleading for lesions (a small lesion tanks Dice even when correctly found), so quality
combines three:

- **Dice** (weight 0.7) — overlap; full marks at 0.70, pass at 0.50.
- **lesion-wise detection F1** (0.1) — precision/recall over *lesion instances* (connected
  components); a predicted blob overlapping no true lesion is a false positive, a missed lesion a
  false negative. Full 1.0, pass 0.5. It carries little weight here because every subject has
  exactly one expert lesion, so detection can only report "found it" or "did not", which Dice
  already covers — see `weight_basis` in the rubric.
- **absolute volume error %** (0.2) — full ≤ 15 %, pass ≤ 50 %.

Verdict: `within_reference_variability` when all three hit full marks; else `acceptable`/`marginal`/
`unacceptable` by weighted quality; `invalid` on a gate failure (`binary`, `native_grid`, `nonempty`,
`volume_plausible`, `not_reference_copy`).

`not_reference_copy` is the fifth gate. These references are published alongside the images
the task hands out, so a submission can be a download rather than a segmentation; a Dice at or
above 0.995 is refused as a copy and the run is **invalid**. The threshold sits far above what
segmenting the image reaches — the best published method on this reference, and the agreement
between two experts tracing the same scan, are both well below it — so it cannot catch an honest
answer.

## Layout

```
clinical-stroke-lesion-segmentation/
├── rubrics/policy.json  # shared policy: weights, gates, verdict thresholds. The calibrated half and this subject's own fields are merged in from the gated dataset at fetch time
├── score_lesion_seg.py  # the lesion scorer
├── reference/           # expert lesion mask — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `clinical_gt/clinical-stroke-lesion-segmentation/<subject>/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in the merged `reference/rubric.json`.

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
