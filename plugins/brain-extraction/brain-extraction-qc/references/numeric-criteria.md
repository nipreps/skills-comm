# Numeric QC Criteria

What `scripts/qc_metrics.py` measures, why each metric works, and where each one
is unreliable. Read this before interpreting a result — the metrics are useful
precisely because their failure modes are known, and a rating quoted without
that context is not much better than a guess.

## Contents

- [The reference frame](#the-reference-frame)
- [Criterion 1 — residual skull or scalp](#criterion-1--residual-skull-or-scalp)
- [Criterion 2 — tissue loss](#criterion-2--tissue-loss)
- [Criterion 3 — symmetry](#criterion-3--symmetry)
- [Criterion 4 — topology](#criterion-4--topology)
- [Criterion 5 — boundary tightness](#criterion-5--boundary-tightness)
- [Context-only metrics](#context-only-metrics)
- [Validation evidence](#validation-evidence)
- [Retuning the thresholds](#retuning-the-thresholds)

---

## The reference frame

Two preprocessing choices carry most of the weight, and both replace something
that looks reasonable but is quietly wrong.

**Canonical RAS reorientation.** Every volume is passed through
`nib.as_closest_canonical` before anything is measured, so axis 0 is
left→right, axis 1 posterior→anterior, axis 2 inferior→superior. Symmetry only
means something along the true anatomical left-right axis; computing it on raw
voxel axes compares the wrong directions on any non-RAS acquisition and can
report a perfectly good mask as asymmetric.

**Head mask by flood fill, not by threshold.** The head is found by flood-filling
background inward from the volume faces and keeping everything unreachable.
Thresholding fails here in a way that poisons every depth-based metric: cortical
bone is a signal void in T1, so a threshold carves the skull out of the head and
leaves the head surface sitting directly on the brain. Depth then reads near
zero for cortex, and real scalp inclusion becomes undetectable. Flood filling
keeps the dark skull because it is enclosed by the scalp.

Depth below the head surface, in millimetres, comes from a Euclidean distance
transform of that head mask, and is what makes "is this voxel shallow enough to
be scalp" answerable without eyes.

---

## Criterion 1 — residual skull or scalp

| Metric | Meaning | Pass | Fail |
|---|---|---|---|
| `shallow_mask_frac_pct` | % of mask voxels less than 4 mm below the head surface | ≤ 2.0 | ≥ 8.0 |
| `bright_rim_frac_pct` | % of the mask's inner rim brighter than 1.15× the mask core's 98th percentile | ≤ 0.10 | ≥ 0.30 |
| `brain_to_head_ratio_high` | mask volume / head volume, high side | ≤ 0.62 | ≥ 0.72 |

Brain never reaches the outside of the head; scalp and skull do. A mask with a
meaningful share of its voxels within a few millimetres of the head surface has
eaten non-brain tissue. Scalp fat is also the brightest thing in a T1, so bright
voxels in the mask's outer shell are the signature of an under-strip that kept
the fat ring.

**Weak against:** inclusion that is deep rather than shallow — dura, sinuses,
and the tentorium all sit well inside the head and will not move these numbers.

---

## Criterion 2 — tissue loss

| Metric | Meaning | Pass | Fail |
|---|---|---|---|
| `brain_to_head_ratio_low` | mask volume / head volume, low side | ≥ 0.44 | ≤ 0.35 |
| `rim_brightness_high` | median rim intensity / median mask core intensity, high side | ≤ 0.42 | ≥ 0.55 |

An over-stripped mask is small relative to the head, and its boundary has been
pulled inward off the cortex/CSF edge into bright white matter — which drives
the rim/core intensity ratio up. A correct boundary sits on darker tissue.

**Weak against:** focal clipping. Both metrics are whole-mask averages, so a
single clipped temporal pole on an otherwise good mask may not move either.
Visual review is materially better here, and `missed_tissue_by_region` (below)
can help localise once something else has flagged a problem.

---

## Criterion 3 — symmetry

| Metric | Meaning | Pass | Fail |
|---|---|---|---|
| `lr_mirror_dice` | Dice between the mask and its reflection about the mid-sagittal plane | ≥ 0.95 | ≤ 0.90 |
| `lr_volume_asym_pct` | \|right − left\| as % of total | ≤ 12.0 | ≥ 25.0 |
| `centroid_offset_lr_mm` | mask centroid distance from the mid-sagittal plane | ≤ 6.0 | ≥ 12.0 |

The mid-sagittal plane is found by searching for the sagittal plane that
maximises the **head** mask's own mirror overlap, reported as
`head_symmetry_dice` (expect > 0.97; a low value means the search failed and
every symmetry number below it is suspect).

Two details matter here, and both were wrong in earlier versions:

*Mirror about the head, never about the mask itself.* A mask mirrored about its
own centroid scores a one-hemisphere mask as perfectly symmetric — the exact
failure most worth catching.

*Use the symmetry plane, not the head centroid.* Whatever the field of view
happens to include of neck, jaw and shoulders drags the centroid sideways by
several millimetres — the same order as the displacement being detected.

`lr_mirror_dice` is the workhorse: it is the only one of the three insensitive
to *which direction* a mask was displaced. A mask shifted toward the midline can
leave `centroid_offset_lr_mm` looking better than the original.

**Weak against:** genuine anatomical asymmetry. Stroke, resection, mass effect,
focal atrophy and a partial field of view all produce real asymmetry, and a mask
correctly following an asymmetric brain will be flagged. These metrics cannot
distinguish that from a lateralised extraction failure. Clinical context or
visual review can, so a symmetry flag is a prompt to check, not a conviction.

---

## Criterion 4 — topology

| Metric | Meaning | Pass | Fail |
|---|---|---|---|
| `extra_component_cm3` | volume outside the largest connected component | ≤ 0.5 | ≥ 3.0 |
| `hole_volume_cm3` | volume filled by 3-D hole filling | ≤ 0.5 | ≥ 3.0 |

The most reliable metrics in the battery — both measure exactly what they claim,
with no intensity assumptions and no anatomical confounds.

**Weak against:** nothing much. A hole is a hole. Note that holes coinciding
with real structures a tool intentionally excludes (some tools drop the
ventricles) will register; check what the tool is meant to produce.

---

## Criterion 5 — boundary tightness

| Metric | Meaning | Pass | Fail |
|---|---|---|---|
| `dark_voxel_frac_pct` | % of mask voxels below 0.25× the core median (CSF, skull, air) | 2.0 – 12.0 | ≤ 0.5 or ≥ 20.0 |
| `rim_darkness_low` | median rim / core intensity, low side | ≥ 0.18 | ≤ 0.12 |

A tight brain mask carries a little sulcal and ventricular CSF. A mask dilated
into the subarachnoid space carries a lot, and its rim sits in dark CSF.

**Weak against:** dura specifically — dura is not dark, so a mask dilated just
far enough to include it may look tight by both numbers. This is the blind spot
that keeps dura UNVERIFIED.

---

## Context-only metrics

Reported but deliberately **not** rated. They are useful for localisation and
sanity-checking, and misleading as pass/fail gates.

| Metric | Why it is not rated |
|---|---|
| `missed_tissue_cm3`, `missed_tissue_by_region` | Temporalis muscle and dura sit just outside every correct mask at brain-like intensity and depth, and dominate the total. On validation it did not separate a good mask from a 3 mm-eroded one. Use it to answer *where* tissue is missing once something else established that some is. |
| `boundary_gradient_ratio` | Looks like it should measure boundary quality, but the sharpest edge in a T1 is skin-to-air, so a whole-head mask scores *higher* than a correct brain mask. Rating on it inverts the verdict. |
| `missed_tissue_below_mask_cm3` | Every tool cuts the brainstem at an arbitrary axial level; tissue below the mask floor is a convention, not an error. |
| `lr_asym_pct_by_axial_band_inf_to_sup` | Eight inferior→superior bands. Lets a text-only report say "asymmetry concentrated inferiorly" instead of just "asymmetric". |
| `mask_touches_fov_edge` | Apparent clipping at a field-of-view edge is an acquisition limit, not an extraction error. |

---

## Validation evidence

Thresholds were separated empirically on adult 1 mm T1w data
(`sub-M2001`, synthstrip mask) plus six synthetic corruptions. Every case is
classified correctly, and each failure is attributed to the intended criterion.

| Mask | Expected | Verdict | Criteria that fired |
|---|---|---|---|
| `good` (synthstrip) | PASS | **PASS** | — |
| `shift10mm` | FAIL | **FAIL** | symmetry FAIL; tightness BORDERLINE |
| `erode3mm` | FAIL | **FAIL** | tissue loss FAIL |
| `dilate5mm` | FAIL | **FAIL** | skull/scalp FAIL; tightness FAIL |
| `hemi_right` | FAIL | **FAIL** | tissue loss FAIL; symmetry FAIL |
| `holes` | FAIL | **FAIL** | topology FAIL |
| `scalp` (whole head) | FAIL | **FAIL** | skull/scalp FAIL; tissue loss FAIL |

Selected values, good vs corrupted:

| Metric | good | shift10mm | erode3mm | dilate5mm | hemi_right | holes | scalp |
|---|---|---|---|---|---|---|---|
| `brain_volume_cm3` | 1512.7 | 1512.7 | 1202.6 | 2101.1 | 752.1 | 1502.3 | 2303.6 |
| `brain_to_head_ratio` | 0.522 | 0.522 | 0.415 | 0.725 | 0.260 | 0.518 | 0.795 |
| `shallow_mask_frac_pct` | 0.27 | 0.85 | 0.00 | 1.98 | 0.28 | 0.27 | 13.41 |
| `bright_rim_frac_pct` | 0.030 | 0.093 | 0.027 | 0.461 | 0.054 | 0.048 | 0.431 |
| `lr_mirror_dice` | 0.967 | 0.751 | 0.964 | 0.973 | 0.021 | 0.961 | 0.919 |
| `lr_volume_asym_pct` | 9.06 | 12.38 | 9.69 | 8.22 | 100.0 | 8.93 | 5.57 |
| `hole_volume_cm3` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.37 | 0.0 |
| `dark_voxel_frac_pct` | 9.31 | 13.10 | 6.20 | 21.79 | 9.09 | 9.34 | 6.33 |
| `boundary_darkness_ratio` | 0.331 | 0.396 | 0.686 | 0.336 | 0.487 | 0.348 | 0.608 |

Reproduce with `make_test_masks.py` and `analysis_01_validate_qc_metrics.sh`
in the skill workspace. Rerun this after changing any threshold — the useful
question is not whether a good mask passes, but whether every corruption still
fails for the right reason.

Note what this validation does *not* establish: it is one subject, one field
strength, one tool, and the corruptions are synthetic and global. Real failures
are often focal and messier. Treat the thresholds as calibrated defaults, not
as validated clinical cut-offs.

---

## Retuning the thresholds

All cut-offs live in the `THRESHOLDS` dict at the top of `qc_metrics.py`, with
three shapes: `hi_bad` (larger is worse), `lo_bad` (smaller is worse), and
`band` (healthy inside a range, failing outside a wider one).

Retune when the population changes. Paediatric and neonatal brains have a
different brain-to-head ratio and a different volume range; rodent data changes
essentially every spatial constant; 7 T data changes the intensity assumptions
behind the rim and darkness metrics. Pass `--vol-range LO HI` for the volume
check rather than editing the file.

The honest way to retune is to run the corruption suite on a handful of subjects
from the new population and pick cut-offs that sit in the gap between good and
corrupted, rather than adjusting until a particular mask passes.
