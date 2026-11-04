# Provenance — how this grader pack was calibrated

One rubric per subject, in `rubrics/<subject>.json`, each the frozen output of a
calibration on that subject's own panel. Scoring a submission never re-derives them.

## How the reference was built

A panel of independent skull-strippers, each run on the subject's T1w — a mix of
registration-based, intensity-based and deep-learning methods, chosen so that they fail
differently — fused by STAPLE into core, margin and background zones.

Which tools, in what configuration, the surface tolerance and the calibrated caps are in
`calibration/structural-brain-extraction/PROVENANCE.md` in the gated reference dataset,
because naming them would let a submission reproduce the reference instead of solving the
task.

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

Nothing fixes the exact **magnitudes**. A sensitivity analysis over alternative weightings
finds the verdicts robust to how the five metrics are balanced and sensitive to dropping a
metric family: rebalancing moves the pass count by at most one mask in several hundred,
while removing the surface or overlap metrics changes about two-thirds of the verdicts a
weighting can touch. Including all five is what matters; the split between them is not.

## Caveats

A tool consensus is not truth. Where every panel member keeps a structure — the superior
sagittal sinus, for instance — removing it is penalised, and only a manual expert tracing
would settle that.
