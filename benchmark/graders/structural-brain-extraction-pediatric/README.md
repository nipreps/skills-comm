# Grader: `structural-brain-extraction-pediatric`

A **consensus-calibrated grader** for the pediatric skull-strip task (ds000228, five children).
The **age axis**, companion to `structural-brain-extraction` (healthy adult) and
`structural-brain-extraction-motion` (motion).

Same design: score a submission against a STAPLE consensus of a tool panel split into core (must keep) /
margin (free, not scored) / background (must exclude), all thresholds calibrated from tool disagreement.
See [`PROVENANCE.md`](PROVENANCE.md).

## Shared scorer (no duplication)

This pack ships only the calibration (`rubrics/<subject>.json`) + the reference pointer — **not** its own scorer.
Grade with the shared scorer from the sibling pack, pointing `--pack` here:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

> Coupling note: the scorer lives in `../structural-brain-extraction/`. If that task is ever removed,
> move `score_brain_mask.py` to a shared location and update the `invoke` path in each task entry.

## What's specific to pediatric

- **The panel members agree closely on these scans**, with no outlier among them. A method that
  depends on an adult template was excluded, because such a template does not fit a young
  child's brain. Members and agreement are in the gated provenance.
- Subjects are screened for field-of-view truncation: an earlier candidate was rejected for a
  truncation cutting through the brain.
- Where the panel disagrees it is mostly about a thin outer CSF rim rather than dura, so the
  margin absorbs that convention instead of the core penalising it.
- Gates include `no_focal_bg_inclusion` (cap 40 cm³) and `no_focal_core_loss`.

## Layout

```
structural-brain-extraction-pediatric/
├── rubrics/<subject>.json  # per-subject frozen calibration: τ, envelope, weights, gate caps
├── reference/           # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md        #   dataset path + fetch command
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-pediatric/<subject>/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubrics/<subject>.json`.

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
