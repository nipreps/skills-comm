# Grader: `clinical-ms-lesion-segmentation`

Grades an **MS white-matter lesion segmentation** against the **expert multi-rater consensus mask**
of `patient01` of the open_ms_data cross-sectional dataset (Ljubljana MS database, CC-BY).

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/clinical-ms-lesion-segmentation/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

Gated so that a submission cannot reproduce the reference instead of solving the
task. Everything governing how a submission is *graded* stays here.

## Why an expert mask, not a consensus of tools

The brain-extraction and tissue graders score against a *tool consensus* — valid because
skull-strippers largely agree. **Lesion segmentation is different:** automated lesion tools disagree
wildly (published Dice on this very cohort spans 0.50–0.74 across methods), so a tool consensus
would be untrustworthy. Here three expert raters segmented the patient independently and the
dataset ships their **consensus**, which IS the ground truth.

Because the individual rater masks are not public and one subject gives no leave-one-out envelope,
the thresholds are **fixed from published results on this same cohort and reference standard** —
see `PROVENANCE.md`.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_lesion_seg.py --pred agent_lesion.nii.gz --pack . [--json result.json]
```

The submission is a **binary lesion mask in the FLAIR space of the co-registered resampled images**
(154 × 240 × 240, 1 mm isotropic).

## Metrics

Dice alone is misleading for MS: the burden is multifocal (408 foci here, median 0.011 cm³), and a
tool can capture the large periventricular confluences while missing most lesion *instances*. So
quality combines three:

- **Dice** (weight 0.4) — overlap; full marks at 0.74, zero credit at 0.53.
- **lesion-wise detection F1** (0.4) — precision/recall over lesion instances (connected
  components, ≥ 10 % overlap counts as detected, components < 3 voxels not counted on either side).
  Full 0.70, zero credit at 0.33.
- **absolute volume error %** (0.2) — full ≤ 15 %, zero credit at 50 %.

Verdict: `within_reference_variability` when all three hit full marks; else `acceptable`/`marginal`/
`unacceptable` by weighted quality; `invalid` on a gate failure (`binary`, `native_grid`,
`nonempty`, `volume_plausible` at 0.5–150 cm³).

`copy_suspect_dice` additionally reports (never scores) a submission that reproduces the reference
too exactly: the upstream dataset ships `consensus_gt.nii.gz` in the same folder as the images, so a
Dice ≥ 0.995 means the reference was copied rather than segmented.

## Layout

```
clinical-ms-lesion-segmentation/
├── rubrics/<subject>.json  # per-subject fixed metric thresholds, weights, verdict thresholds, grid
├── score_lesion_seg.py  # the lesion scorer (shared with the stroke and WMH packs)
├── reference/           # expert consensus mask — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `clinical_gt/clinical-ms-lesion-segmentation/<subject>/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubric.json`.

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
