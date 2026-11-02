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

### `metric_thresholds` for `clinical-stroke-lesion-segmentation` (Dice)

One expert tracing per subject, so there is no panel and no leave-one-out envelope; the
Dice anchors come from the literature instead. Both verified against the sources.

**Full marks, 0.70** — the inter-rater ceiling for manual tracing of chronic stroke
lesions on T1w. Two trained raters following a standardised protocol agree at Dice 0.727
(intra-rater 0.839).

> Tavenner BP, Donnelly MR, Barisano G, Liew S-L. A standardized protocol for manually
> segmenting stroke lesions on high-resolution T1-weighted MR images. *Frontiers in
> Neuroimaging* 2023;1:1098604. doi:10.3389/fnimg.2022.1098604

**Pass, 0.50** — automated state of the art on ATLAS v2.0, where the best benchmarked
models reach Dice 0.504 (3D residual U-Net) and 0.583 (2D transformer).

> Deb P, Baru LB, Dadi K, Bapi RS. BeSt-LeS: Benchmarking Stroke Lesion Segmentation
> using Deep Supervision. arXiv:2310.07060

Population: chronic-stroke T1w manual tracing from ATLAS v2.0 (Liew et al. 2022,
*Scientific Data* 9:320, doi:10.1038/s41597-022-01401-7).

So the band runs from "as good as automated methods manage" to "as good as two humans
agree with each other" — the same shape as the MS task, with raters in place of tools.

The task's `lesion_f1` thresholds (full 1.0, pass 0.5) are **not** from the literature and
carry only weight 0.1, because every subject has exactly one expert lesion and detection
F1 can then only report "found it" or "did not".

### `consensus.max_core_loss = 0.10`

`no_catastrophic_core_loss` fails a submission retaining less than 90 % of the core. The
floor is set below the worst core recall any reference tool achieves, so no panel member
can trip it:

| task | worst leave-one-out core recall | headroom above the 90 % line |
|---|---|---|
| pediatric | 0.9825 | +9.2 % |
| 3T | 0.9782 | +8.7 % |
| stroke | 0.9599 | +6.7 % |
| diffusion | 0.9591 | +6.6 % |
| motion | 0.9457 | +5.1 % |
| 7T and 7T no-dura | 0.9296 | +3.3 % |

7T is the binding case at +3.3 %. The same principle as the pass mark: a tool a competent
person would run must not fail the gate.

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

### `slack`, `verdict_thresholds.acceptable` and `.marginal` are one decision, not three

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
human running a standard tool.

Read in that direction, the free choice is not a number at all. It is the policy *the
pass mark is the weakest panel tool*, and `acceptable = 60` with `slack = 1.5` are two
expressions of it, tied by `slack = q / (1 − q)` for a pass mark of q. Pick either and
the other follows; changing one alone breaks the correspondence and the pass mark stops
meaning anything. `marginal = 30` is then half of the pass mark — a subdivision of a
derived quantity, not an independent threshold.

This section sits under *Derived* rather than *Literature* because the policy itself is a
choice. It is a defensible one, and it is the choice to state in a methods section, but no
external source sets it.

`within_reference_variability` is the stricter, per-metric form of the same bar: every
metric at least as good as the worst panel tool, rather than the weighted average.

### `weights` — reasoned ordering, robust magnitudes

NSD 0.30, core recall 0.25, background FP 0.20, HD95 0.15, volume error 0.10, on the
seven consensus tasks. Two stated principles produce the ordering:

- **Core recall outranks background FP** because losing brain is unrecoverable — the data
  is gone and downstream analysis is silently wrong — whereas retained skull is visible
  and recoverable, degrading registration and segmentation without destroying anything.
  The same asymmetry sets `focal_bg_max_cm3` looser than `focal_max_cm3`.
- **Volume error is weighted lowest** because `volume_plausible` already gates it. A high
  weight would price the same property twice.

What those principles do not fix is the exact split: nothing says 0.30/0.25/0.20/0.15/0.10
rather than 0.35/0.25/0.15/0.15/0.10. So the question is whether the magnitudes matter,
and that is measurable.

**Sensitivity, measured on 425 graded wave-7 agent masks.** Quality is
`100 × Σ(wₖ · subscoreₖ)`, so every alternative weighting is a recombination of stored
subscores. Of the 425, 78 are forced invalid by a gate and 290 are
`within_reference_variability` — a per-metric test independent of the weighting — leaving
**57 masks the weighting actually governs**. Among those 57:

| weighting | acceptable | Δ | verdicts changed |
|---|---|---|---|
| shipped .30/.25/.20/.15/.10 | 18 | — | — |
| core recall first .25/.35/.20/.10/.10 | 18 | 0 | 0 % |
| volume ignored .33/.28/.22/.17/.00 | 17 | −1 | 4 % |
| equal weights .20 × 5 | 18 | 0 | 16 % |
| background doubled .25/.20/.35/.10/.10 | 19 | +1 | 18 % |
| surface only (NSD + HD95) | 9 | −9 | 67 % |
| overlap only (core + bg) | 47 | +29 | 67 % |

**Results are robust to how the five metrics are balanced and not to dropping metric
families.** Any plausible rebalancing moves the pass count by at most ±1 of 425; removing
the surface or the overlap metrics entirely moves it by 9 to 29 and changes two-thirds of
the verdicts it can touch. So the ordering above is load-bearing, the magnitudes are not,
and the decision that matters is including all five metrics rather than the split between
them.

Worth stating with the caveat attached: 368 of 425 masks cannot move under any weighting,
so a figure quoted against the full 425 would understate the effect by a factor of seven.

### `collapse_margin = 0.2` — tissue parcellation

`no_class_collapse` fails a submission recovering less of a class's unanimous core than
`max(0.25, worst panel core recall − 0.20)`. Same "slack below the weakest reference"
construction as the pass mark and `max_core_loss`, and like them it needs a check from
outside the panel: CEREBRUM7T and FreeSurfer v6/v7 define the core between them.

SynthSeg, on the cleaned UNI masked by the brain-extraction task's own consensus mask,
clears every floor on all three subjects:

| | tightest class | SynthSeg | floor | headroom |
|---|---|---|---|---|
| sub-025 | basal ganglia | 0.9374 | 0.7121 | +0.2253 |
| sub-045 | ventricles | 0.9265 | 0.7217 | +0.2048 |
| sub-075 | ventricles | 0.9051 | 0.7043 | **+0.2009** |

It exceeds the panel's worst member on all 18 class-subject combinations, so the margin
is not too tight. Nor is it inert: a swapped or missing class — the failures the gate is
named for — gives core recall near zero.

An intensity tissue classifier cannot be the comparator here. This task grades six
classes (GM, basal ganglia, WM, ventricles, cerebellum, brainstem); FAST and Atropos
produce three tissues and have no label for the last three.

### `plausible_volume_cm3`

`[900, 1900]` structural, `[1020, 2290]` diffusion. A validity bound that rejects a mask
which is not a brain at all, not a normative range.

**Deliberately derived rather than cited.** The quantity is a skull-strip *mask* volume,
which includes CSF to a tool-dependent degree: it sits between brain parenchyma and
intracranial volume at a position that depends on which tool produced it, so no published
norm measures it. The paediatric task (ds000228) is children, so adult norms would not
cover it in any case. And the gate's job is to reject gross error, not to enforce
normality — the right calibration is "outside every legitimate reference, inside every
gross failure", which is a property of this benchmark's data.

Literature is quoted only to show the bounds sit in a sensible region, not to justify
them: for adults aged 40+, total brain volume is about 1245 ± 125 cm³ and total
intracranial volume about 1397 ± 133 cm³, so `[900, 1900]` is roughly ICV mean ± 3.7 SD.

Where the bounds actually stand against this benchmark's data:

| | bound | nearest reference | nearest failure it catches |
|---|---|---|---|
| structural lower | 900 | 1067.5 (`sub-pixar017`), 15.7 % headroom | 838 (AFNI automask), 546 (BET −R at 7T) |
| structural upper | 1900 | 1717.8 (`sub-0023`), 10.6 % headroom | nothing measured |
| diffusion | [1020, 2290] | references span 1357.7–1812.5 | 838 (AFNI automask) |

The lower bound is load-bearing and well placed, separating cleanly between the smallest
reference and the largest gross failure. **The upper bound catches nothing in any test
and carries the tightest margin to a real reference**, so it is pure false-fail risk;
widening it to about 2200 would cost no discrimination. Not changed here — it is a
behaviour change and should be made deliberately, not folded into a documentation pass.

---

## Policy choices

Deliberate design decisions with stated reasoning. Not derived from data, and they do not
pretend to be.

| threshold | value | scope | reasoning |
|---|---|---|---|
| `focal_bg_max_cm3` | 10.0 | 7 tasks | below, measured |
| `lesion_retained_min` | 0.85 | stroke | the lesion must survive extraction; 15 % slack for boundary disagreement |
| `min_lesion_voxels` | 3 (MS), 10 (stroke) | 2 tasks | stroke's is derived from resampling debris (see `weight_basis`); MS's is not |
| `overlap_frac_for_match` | 0.1 | MS, stroke | matches Anima's detection convention, which is what lets the MS anchors transfer; unexamined for stroke |

### `focal_bg_max_cm3 = 10`

Two independent measurements, agreeing.

**Tool masks.** Every non-panel mask on disk, scored through the grader (39 across 7T,
motion, pediatric and diffusion):

| group | n | `focal_bg_incl_cm3` |
|---|---|---|
| well-chosen invocations (HD-BET and SynthStrip at defaults, BET −R, BET default on paediatric) | 16 | 0.00 – 3.87 |
| masks that *under*-include (AFNI and BET −R at 7T, dwi2mask, AFNI automask, BET f0.5) | 21 | 0.00 – 0.78 |
| BET at its defaults on motion-corrupted T1w | 5 | **16.67 – 113.27** |

The under-inclusive group registers nothing — those fail the *core* gate instead. So the
discriminating evidence is five masks, with an empty band between 3.87 and 16.67.

**Agent masks.** The 425 graded wave-7 masks put p90 at 2.50, p95 at 5.15 and p99 at
7.03 cm³, with the next value above 40. **No mask falls between 10 and 40**, so moving
the cap from 40 to 10 changes no verdict in wave 7 while closing a demonstrated false
pass: `sub-281888` at 16.67 cm³ was rendered and characterised as a genuine swallowed
chunk (18.9 mm thick, only 43 % within 5 mm of the boundary), not a rim.

10 is `SLACK × worst legitimate` rounded up — the same rule the core cap uses, applied to
the 3.87 cm³ worst legitimate value. It sits mid-band in both measurements, so it would
take a legitimate tool at 2.6× the worst yet seen, or a failure below 10, to break it.

The cap is deliberately looser than the core cap, because lost brain is unrecoverable
while retained skull is visible and downstream-recoverable. The gate catches gross
inclusion; `bg_fp_frac_of_ref` at weight 0.20 prices the gradient.

**It is not calibrated from leave-one-out**, unlike the core cap. That construction was
tried and rejected on inspection: holding a tool out and measuring what it admits of the
reduced panel's background gives 0.1–69.2 cm³ across 28 subjects, which would set
per-subject caps from 5 to 104. The 69.2 cm³ case (`motion sub-723372`) was rendered and
is a continuous rim of dura and inner skull table around the whole cortical surface, 87 %
of it within 5 mm of the boundary. Calibrating from it would write a boundary convention
into a permissive threshold.

---

## Undocumented

Nobody recorded why these particular values. Three single-task constants; none is in the
core machinery.

| threshold | value | scope | consequence if wrong |
|---|---|---|---|
| `metric_thresholds.abs_volume_err_pct` | full 15 %, pass 50 % | MS, stroke | scores, at weight 0.2 |
| `copy_suspect_dice` | 0.995 | MS | none — diagnostic only, see `copy_suspect_basis` |

---

## Known gaps

- The MS thresholds are now verified against the paper's supplementary table. The stroke
  task's `metric_thresholds` have had no such check and are round numbers.
- `plausible_volume_cm3` is derived by decision, not cited. Bounds left as they are: they
  work for the current subjects.
- `focal_bg_max_cm3` passes a genuine over-inclusion (`sub-281888`, 16.67 cm³). Lowering
  it to about 10 would catch every case measured, but rests on 16 legitimate masks from
  three tasks.
- τ is calibrated on tool disagreement, not rater disagreement, and must not be reported
  as if it were the latter.
