# Grader: `structural-brain-extraction-motion`

A **consensus-calibrated grader** for the harder, motion-corrupted skull-strip task
(MR-ART `ds004173`, five subjects, `acq-headmotion2` — the worst-motion tier). It is the
companion to `structural-brain-extraction` (the healthy-adult baseline) on the **motion axis**.

Same design: score a submission against a STAPLE consensus of a tool panel split into
core (must keep) / margin (free, not scored) / background (must exclude), with all thresholds
calibrated from the tools' own disagreement. See [`PROVENANCE.md`](PROVENANCE.md).

## Shared scorer (no duplication)

This pack carries **only the calibration** (`rubrics/<subject>.json`) and the reference pointer — it does
**not** ship its own scorer. Grade with the shared scorer from the sibling pack, pointing `--pack`
here:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

> Coupling note: the scorer currently lives in `../structural-brain-extraction/`. If that task is
> ever removed, move `score_brain_mask.py` to a shared location (e.g. `benchmark/graders/`) and
> update the `invoke` path in both task entries — a one-line change.

## What's different from the baseline

On the motion scan the tools **diverge and partly fail**, so the reference panel is curated:

- **The panel is curated for this scan.** Not every method that is sound on a clean T1w stays
  sound here, and one that is not would widen the margin rather than inform it. Who was kept,
  their pairwise agreement and why the rest were set aside are in the gated provenance.
- **The surface tolerance is wider than on a clean scan**, because the boundary genuinely is
  fuzzier under motion. It is calibrated from the panel's own spread, not chosen.
- The gates include **`no_focal_bg_inclusion`**, the mirror of the focal-loss gate: it fails a
  mask that retains a large contiguous chunk of non-brain, the neck and spinal cord being the
  usual case on a scan with this field of view.

## Layout

```
structural-brain-extraction-motion/
├── rubrics/<subject>.json  # per-subject frozen calibration: τ, envelope, weights, gate caps (incl. focal_bg_max_cm3)
├── reference/           # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md        #   dataset path + fetch command
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-motion/<subject>/`.
The pack is frozen once; scoring never re-calibrates.

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
