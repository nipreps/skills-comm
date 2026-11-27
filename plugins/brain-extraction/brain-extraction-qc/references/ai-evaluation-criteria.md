# Visual Evaluation Criteria

The visual layer of `brain-extraction-qc`. Read this **only if you can actually
open images** — if you cannot, work from `numeric-criteria.md` and mark dura
UNVERIFIED.

Base visual ratings on the **AFNI outline PNG**. The mosaic PNG is supporting
context. An outline is the more sensitive instrument: a translucent filled
overlay looks equally acceptable whether its edge lies on the pial surface or
four millimetres out in the dura, and that is exactly the distinction under
test.

## What vision adds

The numeric battery covers most of the ground. Vision is worth the effort for
the things measurement handles badly:

- **Dura and superior sagittal sinus** — the one criterion with no numeric
  substitute at all. Dura is thin, overlaps cortex in T1 intensity, and sits
  where a correct boundary also sits.
- **Focal defects** — a single clipped temporal pole barely moves whole-mask
  averages but is obvious in one coronal panel.
- **Anatomy that explains a flagged number** — a stroke cavity, resection,
  shift from mass effect, or a partial field of view turns "asymmetric mask" into
  "correct mask of an asymmetric brain".
- **Failures nothing anticipated** — wrap-around, bias field, motion ghosting,
  a mask from the wrong subject.

Where the numbers are already decisive — hole volume, component count, mirror
Dice — vision mostly confirms. Spend attention where it changes the answer.

## Reading the outline

Across all three planes, the outline should:

- follow the cortical and cerebellar boundary closely
- stay outside visible grey matter without cutting into it
- track both hemispheres evenly rather than hugging one side
- avoid skull, scalp, eyes, dura and large CSF regions
- form one coherent boundary with no disconnected islands

Do not grade from a single slice. Scan the full row for a *consistent
directional pattern* — one hemisphere repeatedly clipped, one end repeatedly
over-included. A single odd panel is usually anatomy; a repeated bias is a mask
error.

---

## 1. No residual skull or scalp signal

Look for the outline tracking the bright outer skull ring in axial panels, or
extending into scalp above and behind the brain in sagittal.

Ignore tiny isolated inferior or orbital-adjacent fragments unless they appear
across multiple slices, connect to the main mask problematically, or would
affect registration, segmentation or volumetry.

| Rating | What it looks like |
|---|---|
| **Pass** | Outline tight to the brain surface; no meaningful skull or scalp inclusion |
| **Borderline** | Small but definite skull/scalp inclusion at 1–2 locations, unlikely to affect core analysis |
| **Fail** | Continuous band of skull or scalp enclosed; outline clearly traces non-brain tissue |

## 2. No excessive tissue loss at poles

The outline should run outside cortex, not through it. Common failure sites:
frontal poles (anterior axial/sagittal), inferior temporal lobes (inferior
coronal), occipital poles (posterior axial/sagittal), cerebellum (inferior
axial/coronal).

| Rating | What it looks like |
|---|---|
| **Pass** | All brain tissue covered; outline stays outside cortex at the poles |
| **Borderline** | Minor clipping at one pole; a thin sliver of tissue outside the mask |
| **Fail** | Substantial tissue at one or more poles left out; outline repeatedly cuts cortex |

## 3. Symmetric left-right and anterior-posterior coverage

Check that the outline tracks both hemispheres evenly about the midline in axial
and coronal panels, and that anterior and posterior coverage is balanced.

Cross-check against `lr_mirror_dice`, `lr_volume_asym_pct` and the axial-band
breakdown. If the metric flags asymmetry and the image shows the outline
correctly following an asymmetric brain, that is a **Pass with documentation** —
name the anatomy. If the metric is clean but the image shows a consistent
one-sided error, trust the image and say so.

| Rating | What it looks like |
|---|---|
| **Pass** | Outline tracks the visible boundary evenly; any metric flag explained by anatomy |
| **Borderline** | Mild repeatable peripheral asymmetry, or one unexplained flag that looks visually small |
| **Fail** | Consistent L/R or A/P over- or under-coverage from mask error across multiple slices |

## 4. No internal holes or disconnected mask regions

Look for outline loops fully inside the brain (internal holes) and small
isolated loops outside the main region (detached fragments — eyes, sinuses,
detached cerebellum).

| Rating | What it looks like |
|---|---|
| **Pass** | Continuous mask, one coherent boundary, no islands |
| **Borderline** | 1–2 small internal holes or one small isolated loop, not in critical regions |
| **Fail** | Multiple large holes or several disconnected fragments |

## 5. Boundary tightness (not over-dilated into dura/CSF)

The outline should follow the pial surface. Over-dilation appears as a bloated
edge extending into the dark CSF space, commonly near the interhemispheric and
Sylvian fissures.

| Rating | What it looks like |
|---|---|
| **Pass** | Outline follows the brain surface; CSF ring visible outside the mask |
| **Borderline** | Extends a few voxels into CSF/sulci; brain volume not substantially overestimated |
| **Fail** | Clearly bloated; outline runs through CSF/dura rather than the brain edge |

## 6. Dura / superior sagittal sinus inclusion

**This criterion exists because it is the one thing the metrics cannot do.**
Check the superior sagittal sinus along the vertex in sagittal and coronal
panels, the transverse sinuses inferiorly, and the tentorium between cerebrum
and cerebellum.

| Rating | What it looks like |
|---|---|
| **Pass** | Outline excludes the sinuses and tentorium |
| **Borderline** | Thin dural strip included along the vertex or tentorium |
| **Fail** | Sinuses or a broad dural sheet enclosed in the mask |
| **UNVERIFIED** | No visual inspection was performed — the only honest rating on a numeric-only run |

---

## Overall verdict

Start from the script's `NUMERIC_VERDICT`, which fails the mask on any single
failing criterion. Adjust it only with a stated reason.

Overturning **downward** (numbers pass, you rate worse) needs no special
justification beyond describing what you saw — dura inclusion and focal defects
are exactly the cases the metrics miss.

Overturning **upward** (numbers fail, you rate better) requires naming a
concrete explanation: anatomy, pathology, acquisition, field of view, or a
population mismatch with the reference ranges. "Looks fine to me" is not one.
The failure mode this guards against — waving a bad mask through because the
image gave a general impression of acceptability — is the most common way QC
becomes ceremonial.

## Common artefacts

| Artefact | Typical location | Criterion |
|---|---|---|
| Temporal pole clipping | Inferior coronal, sagittal | 2 |
| Frontal pole erosion | Anterior axial, sagittal | 2 |
| Dural sinus inclusion | Superior sagittal sinus | 6 |
| Eye orbit inclusion | Inferior axial | 1 |
| Disconnected cerebellar fragment | Inferior axial/coronal | 4 |
| Interhemispheric fissure bloat | Mid-axial, coronal | 5 |
| Scalp fat ring included | Outer ring, all axial | 1 |
| Tentorium included | Between cerebrum and cerebellum | 6 |
