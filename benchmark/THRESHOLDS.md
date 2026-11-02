# Where every threshold comes from

One place to check what each number in a rubric rests on. Three kinds of entry:

- **Literature** — an external, citable source. Reproduced here with the figure it gives.
- **Derived** — computed from this benchmark's own data by a stated rule, with the rule
  written out. Defensible, but not externally anchored.
- **Unjustified** — chosen, and nothing supports the particular value. Listed because a
  threshold nobody can reconstruct is the kind that turns out to be wrong.

A number's status is not a judgement of whether it is *right*. `SLACK` is unjustified and
also load-bearing; `focal_max_cm3` is derived and has already been wrong twice.

---

## Literature

### STAPLE consensus

Every consensus reference is the STAPLE estimate over a tool panel.

> Warfield SK, Zou KH, Wells WM. Simultaneous truth and performance level estimation
> (STAPLE): an algorithm for the validation of image segmentation. *IEEE Transactions on
> Medical Imaging* 2004;23(7):903–921. doi:10.1109/TMI.2004.828354

### `tau_mm` — the surface tolerance for NSD

NSD is the fraction of each surface lying within τ of the other. The metric, and the
practice of setting τ from the spread among independent raters rather than picking a
round number, are from:

> Nikolov S, Blackwell S, Zverovitch A, et al. Deep learning to achieve clinically
> applicable segmentation of head and neck anatomy for radiotherapy. *Journal of Medical
> Internet Research* 2021;23(7):e26151. arXiv:1809.04430

**Deviation to state plainly**: that paper sets τ from inter-*observer* variation among
human experts. Here τ is the 95th percentile of pairwise surface disagreement among the
*tools* in the panel. The construction is the same; the population is not. The tolerance
therefore describes what automated methods disagree about, which is not the same quantity
as what two radiologists disagree about, and it is not interchangeable with a τ quoted
from a human-rater study.

### `SOLID_SHAVE_MM = 1.5` — thickness required to count as missing anatomy

`no_focal_core_loss` and `no_focal_bg_inclusion` measure the largest component surviving
a shave of `max(1.5 mm, one voxel)`. A region survives only if it exceeds about twice the
shave, so the gate tolerates a boundary offset of roughly one cortical thickness and
catches anything thicker.

> Fischl B, Dale AM. Measuring the thickness of the human cerebral cortex from magnetic
> resonance images. *PNAS* 2000;97(20):11050–11055.

That paper gives cortical thickness as 1–4.5 mm, mean ≈ 2.5 mm. **The honest reading**:
a lost strip thinner than ~3 mm is treated as a boundary convention, which means a
genuinely missing ribbon of thin cortex would not trip the gate. The gate is for missing
*structures* — a lobe, a cerebellum, a temporal pole — which are thick in every direction.
Total core loss is still priced by `core_recall` and `no_catastrophic_core_loss`, and
boundary disagreement by τ, NSD and HD95.

The one-voxel floor is not from literature: a 1.5 mm shave removes nothing on a 2.5 mm
grid, where no voxel is within 1.5 mm of the outside, so the measure would silently fall
back to a raw component volume. No grid resolves a layer thinner than its own voxel.

### `metric_thresholds` for `clinical-ms-lesion-segmentation` (full marks only)

> Wiltgen T, McGinnis J, Schlaeger S, et al. LST-AI: A deep learning ensemble for accurate
> MS lesion segmentation. *NeuroImage: Clinical* 2024;42:103611.
> doi:10.1016/j.nicl.2024.103611. PMID 38703470, PMCID PMC11088188

Anchored on the `msljub` rows of supplementary table `anima_mean_scores` (mmc1.xlsx) —
the same Ljubljana 30-patient cohort and the same three-rater consensus reference used
here:

| tool | Dice | lesion-wise F1 |
|---|---|---|
| LST-AI | **0.7425** | **0.6972** |
| DeepLesionBrain | 0.5541 | 0.3748 |
| samseg-7.3.2 | 0.4804 | 0.2564 |
| nnUNet | 0.4435 | 0.3116 |
| LST-LPA | 0.3957 | 0.1822 |
| LST-LGA | **0.3727** | **0.1545** |

`full` = LST-AI, the best published method on this cohort. `pass`, the zero-credit line,
= LST-LGA, the weakest. The four other published tools fall inside the band, so a
submission matching any of them scores above zero on both metrics, which is the intent.

The F1 anchors transfer because the detection convention matches: Anima counts a
reference lesion as detected at ≥ 10 % overlap, and `overlap_frac_for_match` is 0.1 here.
One difference remains — `min_lesion_voxels` drops components below 3 voxels on both
sides, which Anima does not do — so the F1 anchors are close rather than exact.

`abs_volume_err_pct` (full 15 %, pass 50 %) is **not** from the paper. It is a tolerance
of this benchmark's own choosing and belongs in the unjustified list below.

**Corrected 2026-11-02.** The rubric previously set `pass` at Dice 0.53 / F1 0.33,
attributed to LST-LGA, with SAMSEG at 0.62/0.47 and nnU-Net at 0.58/0.54 described as
mid-band. None of those six figures appear in the paper; the real values are in the table
above. The error ran the wrong way: the old pass line was stricter than the weakest
published tool, so a submission reproducing DeepLesionBrain's published performance on
this cohort (0.55/0.37) scored 28.1 and graded `unacceptable`. It now scores 55.1. The
`full` anchors were correct throughout.

---

## Derived

### `focal_max_cm3` — per subject

`max(SLACK × worst held-out focal miss, 5.0 cm³ floor)`, the held-out miss measured by the
same shaved-component function the scorer applies to a submission. Hold each panel tool
out, rebuild the consensus from the rest, and measure the largest solid region of core
that only that tool's dissent was keeping out.

Measuring the cap and the quantity it caps the same way is the point: a connected-component
volume cannot separate a uniform boundary offset from a missing structure, so calibrating
on the raw volume sets a cap wide enough to admit a missing lobe.

Checked against tools outside each panel, which is the only non-circular test available —
panel members contain the core by construction. See the per-pack PROVENANCE files.

### `dura_max_cm3 = 50` — `structural-brain-extraction-7t-nodura`

Bounded on both sides by measurement. The consensus reference itself sits 15.2–33.7 cm³
outside the pial envelope across the three subjects, so a perfect answer fails below ~34.
The smallest rim-retaining failure (SynthStrip at its defaults) is 117.7 cm³. 50 sits
between them.

**Limitation worth stating**: the envelope and the consensus are independently built and
cross each other — 15–34 cm³ of consensus lies outside the envelope and 36–59 cm³ of
envelope lies outside the consensus. A perfect answer therefore consumes most of the
gate's budget before a submission is examined, so the gate is coarse by construction.

### `plausible_volume_cm3`

`[900, 1900]` structural, `[1020, 2290]` diffusion. Intended as a sanity bound that
rejects a mask which is not a brain at all, not a normative range. **These should be
anchored to published brain-volume norms and currently are not** — a cheap fix and worth
doing before publication.

---

## Unjustified

These have no external source and no derivation. Ordered by how much they move results.

| threshold | value | scope | note |
|---|---|---|---|
| `slack` | 1.5 | 8 consensus tasks | sets the whole score scale — see below |
| `weights` | NSD .30, core recall .25, bg FP .20, HD95 .15, volume .10 | 7 tasks | relative importance of the five metrics; nothing supports this split |
| `verdict_thresholds.marginal` | 30 | all 10 tasks | halfway between 60 and 0 |
| `consensus.max_core_loss` | 0.10 | all | `no_catastrophic_core_loss` fires below 90 % core retained |
| `focal_bg_max_cm3` | 40.0 | 7 tasks | fixed policy; a leave-one-out anchor was attempted and rejected, below |
| `lesion_retained_min` | 0.85 | stroke | |
| `min_lesion_voxels` | 3 (MS), 10 (stroke) | 2 tasks | |
| `collapse_margin` | 0.2 | tissue | |
| `copy_suspect_dice` | 0.995 | MS | |
| `metric_thresholds` | stroke: Dice full 0.7 / pass 0.5, F1 full 1.0 / pass 0.5 | stroke | round numbers |
| `metric_thresholds.abs_volume_err_pct` | full 15 %, pass 50 % | MS, stroke | the one part of the MS thresholds not taken from the literature |
| `overlap_frac_for_match` | 0.1 | MS, stroke | matches Anima's detection convention, so defensible for MS; unexamined for stroke |

### `slack` and `verdict_thresholds.acceptable` are one decision, not two

`subscore` maps the median panel tool to 1.0 and reaches 0 at
`worst + slack × (worst − median)`. Substituting the worst panel tool gives

```
subscore(worst) = slack / (1 + slack)
```

independent of the metric and of its values. At `slack = 1.5` that is exactly **0.60**, so
a submission as good as the weakest tool in the panel scores exactly **60** — verified
numerically on four tasks.

So `acceptable ≥ 60` means **"no worse overall than the weakest tool in the reference
panel"**, which is the benchmark's intent: an agent should not have to beat a competent
human running a standard tool. The threshold is principled, but it is *determined* by
`slack`. Changing either alone breaks the correspondence, and `slack = 1.5` is the single
free parameter behind both.

`within_reference_variability` is the stricter, per-metric form of the same bar: every
metric at least as good as the worst panel tool, rather than the weighted average.

### Why `focal_bg_max_cm3` was not calibrated from leave-one-out

The core cap's leave-one-out construction was tried on the background side and rejected on
inspection. Holding a tool out and measuring what it admits of the reduced panel's
background gives 0.1–69.2 cm³ across 28 subjects, which would set per-subject caps from
5 to 104 cm³. The 69.2 cm³ case (`structural-brain-extraction-motion` `sub-723372`) was
rendered and is a continuous rim of dura and inner skull table around the whole cortical
surface — 87 % of it within 5 mm of the consensus boundary. Calibrating from it would
write a boundary convention into a permissive threshold. The fixed 40 cm³ stands until
there is a better anchor.

---

## Known gaps

- The MS thresholds are now verified against the paper's supplementary table. The stroke
  task's `metric_thresholds` have had no such check and are round numbers.
- `plausible_volume_cm3` has no normative citation.
- `slack`, `weights` and `marginal` are unjustified and apply everywhere.
- τ is calibrated on tool disagreement, not rater disagreement, and must not be reported
  as if it were the latter.
