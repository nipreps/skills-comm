# Provenance — how this grader pack was calibrated

The pack is the **frozen output of a one-time calibration** on the benchmark subject
(ds002790 `sub-0004`, native T1w space). It is not re-derived when a submission is scored.


> This pack calibrates one rubric per subject, in `rubrics/<subject>.json`. `fetch_reference.py --subject` selects the one being graded into `reference/rubric.json`.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Inputs

A panel of independent skull-strippers, each run on the subject's T1w: a mix of
registration-based, intensity-based and deep-learning methods, chosen so that they fail
differently. Which tools, in what configuration, and which of them defines the reference
grid are in the gated `calibration/structural-brain-extraction/PROVENANCE.md`.

## The scoring scale, and what passing means

Each metric is mapped onto the leave-one-tool-out envelope by `subscore`, which reaches
1.0 at the **median** panel tool and 0 at `worst + slack × (worst − median)`. Substituting
the worst panel tool into that gives

    subscore(worst panel tool) = slack / (1 + slack)

independent of the metric and of its values. At `slack = 1.5` that is exactly **0.60**,
verified numerically across tasks, so a submission as good as the weakest tool in the
panel scores exactly **60**.

`verdict_thresholds.acceptable = 60` therefore means *no worse overall than the weakest
tool in the reference panel* — the benchmark's intent, that an agent should not have to
beat a competent person running a standard tool. It is not a free parameter: the choice
is the policy, and `slack = 1.5` and `acceptable = 60` are two expressions of it, tied by
`slack = q / (1 − q)`. Changing one alone breaks the correspondence and the pass mark
stops meaning anything. `marginal = 30` is half the pass mark.

`within_reference_variability` is the stricter, per-metric form of the same bar: *every*
metric at least as good as the worst panel tool, rather than the weighted average. A run
can compensate a weak metric with a strong one and reach `acceptable` without reaching it.

## Why the metrics are weighted as they are

NSD 0.30, core recall 0.25, background FP 0.20, HD95 0.15, volume error 0.10. Two
principles set the **ordering**:

- **Core recall outranks background FP** because losing brain is unrecoverable — the data
  is gone and downstream analysis is silently wrong — whereas retained skull is visible
  and recoverable, degrading registration and segmentation without destroying anything.
  The same asymmetry makes `focal_bg_max_cm3` looser than `focal_max_cm3`.
- **Volume error is weighted lowest** because `volume_plausible` already gates it, and a
  high weight would price the same property twice.

Nothing fixes the exact **magnitudes**, so they were tested rather than argued. Quality is
a linear recombination of the per-metric subscores, so every alternative weighting can be
evaluated from one scoring pass. On the 425 graded masks of benchmark wave 7 — of which
78 are gate-failed and 290 are `within_reference_variability`, a per-metric test
independent of the weighting, leaving **57 that a weighting governs**:

| weighting | acceptable | Δ | verdicts changed |
|---|---|---|---|
| shipped .30/.25/.20/.15/.10 | 18 | — | — |
| core recall first | 18 | 0 | 0 % |
| volume ignored | 17 | −1 | 4 % |
| equal weights | 18 | 0 | 16 % |
| background doubled | 19 | +1 | 18 % |
| surface only (NSD + HD95) | 9 | −9 | 67 % |
| overlap only (core + bg) | 47 | +29 | 67 % |

**Results are robust to how the five metrics are balanced, and not to dropping metric
families.** Any plausible rebalancing moves the pass count by at most ±1 of 425; removing
the surface or the overlap metrics moves it by 9 to 29 and changes two-thirds of the
verdicts it can touch. The split is not load-bearing; including all five metrics is.

Quoted against the full 425 rather than the 57, that effect would look seven times
smaller than it is.

## Reference data

The `reference/` NIfTIs are on the Hugging Face Hub with the other task ground truth:

- Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction/<subject>/`
- `consensus_mask.nii.gz`, `consensus_zones.nii.gz` (native T1w space)

Fetch them before grading — see `reference/README.md` for the fetch command. Everything else
the grader needs (tau, the envelope, the gate caps) is in `rubric.json`.

## Caveats

- **Consensus of tools is not truth.** If every panel tool keeps a structure (e.g. the superior
  sagittal sinus), removing it is penalised. One manual expert tracing would settle it.
