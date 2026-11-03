# Grader: `structural-brain-extraction-7t`

A **consensus-calibrated grader** for skull-stripping a **7 Tesla MP2RAGE** scan
(CEREBRUM-7T `ds003642`; sub-025, sub-045 and sub-075, 0.63 mm isotropic). It is the companion to
`structural-brain-extraction` (healthy 3T baseline) on the **field-strength / sequence axis**.

Same design as the baseline: score a submission against a STAPLE consensus of a tool panel split
into core (must keep) / margin (free, not scored) / background (must exclude), with all thresholds
calibrated from the tools' own disagreement. See [`PROVENANCE.md`](PROVENANCE.md).

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/structural-brain-extraction-7t/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

That detail is gated because it describes the answer: in one benchmark wave, agent runs
retrieved these files from GitHub and one rebuilt the panel consensus from them. Access
is granted on request, and everything needed to audit *how* grading works — the gates,
weights, verdict thresholds and the scoring scale — stays here.

## Shared scorer (no duplication)

This pack carries **only the calibration** (`rubrics/<subject>.json`) and the reference pointer — it does
**not** ship its own scorer. Grade with the shared scorer from the baseline pack, pointing `--pack`
here:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

## Layout

```
structural-brain-extraction-7t/
├── rubrics/<subject>.json  # per-subject frozen calibration: τ, envelope, weights, gate caps, grid.raw_affine
├── reference/           # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md        #   dataset path + fetch command
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-7t/<subject>/`.
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
