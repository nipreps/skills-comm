# Grader: `structural-brain-extraction`

A **consensus-calibrated grader** for the `structural-brain-extraction` benchmark task — a
more discriminating alternative to grading a skull-strip by *Dice against one reference mask*.

![How a brain-extraction submission is graded: a panel of skull-strippers is fused by STAPLE into core, margin and background zones; a submission passes ten validity gates, then earns a 0-100 quality score weighting NSD 30%, core recall 25%, background inclusion 20%, HD95 15% and volume error 10%; a mask can score well on metrics alone and still fail the focal-core-cut gate.](brain_extraction_grading.png)

*Full size: [`brain_extraction_grading.png`](brain_extraction_grading.png).*

Every threshold (the surface tolerance τ, the per-metric pass/fail envelope, the gate caps) was
**calibrated from the data** (leave-one-tool-out), never hand-picked. See [`PROVENANCE.md`](PROVENANCE.md).

## The reference

Several independent tools, fused so that their agreement — not any one tool's opinion —
defines what counts as correct. Which tools and how they were combined are gated with the
reference data, so that a submission cannot reproduce it instead of solving the task; see
[`PROVENANCE.md`](PROVENANCE.md). Everything governing how a submission is *graded* is
here and in [`rubrics/`](rubrics/).

## Layout

```
structural-brain-extraction/
├── rubrics/<subject>.json            # per-subject calibration: τ, envelope, weights, gate caps, grid
├── brain_extraction_grading.png      # the explainer figure above
├── score_brain_mask.py               # the grader — importable score() + CLI
├── reference/                        # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md                     #   dataset path + fetch command
│   └── .gitignore                    #   keeps *.nii.gz out of git
├── README.md
└── PROVENANCE.md
```

The reference is fetched into `reference/` before grading; see
[`reference/README.md`](reference/README.md). Each subject's rubric is frozen, so scoring
never re-calibrates — it only measures the submission against the reference.

## Run it

```bash
python3 score_brain_mask.py --mask agent_mask.nii.gz --pack . \
    [--stripped agent_brain.nii.gz] [--json result.json]
```

Output is JSON: `verdict`, `quality` (0–100), `gate_failures`, per-metric `metrics` and
`subscores`. Exit code `0` for a valid submission, `1` if any gate failed, so it drops into
a harness as a pass/fail check. Depends only on `numpy`, `scipy` and `nibabel`.

Gates first — any failure is `invalid` with the gate named — then a weighted quality.
[`PROVENANCE.md`](PROVENANCE.md) explains what each gate catches and why the metrics carry
the weights they do.

## How it is invoked

The task's entry in [`benchmark/tasks.json`](../../tasks.json) carries a `grader`
block naming this pack, the fetch command and the pass criterion. A harness reads
that rather than hard-coding anything here; [`benchmark/harness/README.md`](../../harness/README.md) describes the flow.

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
