# AI Visual Evaluation Criteria

This rubric defines how to visually evaluate brain extraction QC images. Load
this file before completing Step 3 of the `brain-extraction-qc` skill.

The Python PNG mosaic shows three rows (Axial, Coronal, Sagittal) × nine
columns (evenly-spaced slices). The brain mask is overlaid in red. The AFNI
outline PNG shows an edge-only outline generated from the mask and rendered over
the anatomical image with `@chauffeur_afni`. Evaluate each criterion by
scanning both QC images in all visible planes — some failures are only visible
in one view or only become obvious with the outline.

---

## Evaluation Criteria

### 1. No residual skull or scalp signal

**What to look for:** Red mask extending into the bright ring of skull cortex
or scalp fat visible in T1w. In axial slices, residual skull appears as a bright
outer ring partially covered by red. In sagittal, look for red extending into
the scalp above and behind the brain. In the AFNI outline PNG, the edge should
not trace skull, scalp, eyes, dura, or other non-brain tissue.

| Rating | Visual Description |
|--------|--------------------|
| **Pass** | Red mask and AFNI outline are tight to the brain surface; no skull or scalp voxels included |
| **Borderline** | Small isolated patches of skull/scalp included at 1–2 locations; outline only briefly leaves the brain boundary |
| **Fail** | Continuous band of skull or scalp enclosed in the mask; AFNI outline clearly traces non-brain tissue |

---

### 2. No excessive tissue loss at poles (frontal, temporal, occipital)

**What to look for:** Grey brain tissue visible in the image but NOT covered by
the red mask, or an AFNI outline that cuts through visible cortex instead of
running along the outside of the brain. The most common failure sites are:
- Frontal poles (anterior-most axial and sagittal slices)
- Inferior temporal lobes (inferior coronal slices)
- Occipital poles (posterior axial and sagittal slices)
- Cerebellum (inferior axial and coronal slices)

| Rating | Visual Description |
|--------|--------------------|
| **Pass** | All brain tissue covered; AFNI outline stays outside visible cortex at the poles |
| **Borderline** | Minor clipping at one pole (thin sliver of tissue outside mask); outline cuts cortex only minimally at the periphery |
| **Fail** | Substantial brain tissue at one or more poles left outside the mask; outline repeatedly cuts through cortex; would compromise downstream analysis |

---

### 3. Symmetric left-right and anterior-posterior coverage

**What to look for:** In axial slices, the red mask should appear roughly
symmetric about the midline. In coronal slices, compare left vs. right
hemisphere coverage. Asymmetry suggests the mask centre of mass was
misaligned or the brain extraction failed on one side.

Do not grade symmetry from a single slice. Scan the full row and look for a
consistent directional pattern:
- One hemisphere repeatedly clipped while the other is covered
- One hemisphere repeatedly over-expanded into non-brain tissue
- Anterior or posterior slices systematically missing tissue or including
  non-brain compared with the opposite end
- A red mask centroid that is visibly shifted away from the brain centroid
- Mid-sagittal or mid-coronal slices that show the mask hugging one side while
  leaving brain visible on the other side

Use the quantitative symmetry diagnostics from the QC script as a warning
system, not as a replacement for visual review. If the script reports
`WARNING: symmetry`, this criterion should be **Borderline** or **Fail** unless
there is a specific visible reason the anatomy or field-of-view is genuinely
asymmetric.

Use the AFNI outline as the primary visual check for centering. A filled overlay
can hide a shifted boundary; the outline should track both hemispheres evenly
and should not hug one side while leaving cortex exposed on the other.

| Rating | Visual Description |
|--------|--------------------|
| **Pass** | Filled overlay and AFNI outline appear symmetric across the slice series; mask centroid is visually aligned with the brain; no consistent L/R or A/P imbalance; no symmetry warnings from the QC script |
| **Borderline** | Mild but repeatable asymmetry at the periphery, or one symmetry warning that is visually small and unlikely to affect core brain volume |
| **Fail** | Clear and consistent L/R or A/P asymmetry in the filled overlay or AFNI outline; one hemisphere or half substantially over/under-covered; visible centroid shift; multiple symmetry warnings; or asymmetry affecting cortex, deep grey matter, cerebellum, or large contiguous regions |

---

### 4. No internal holes or disconnected mask regions

**What to look for:** Dark (unmasked) regions entirely enclosed within the red
mask. Appears as black patches inside the red overlay in any plane. Also watch
for small isolated red islands or outline loops outside the main brain region
(disconnected fragments — e.g., eyes, dural sinuses, cerebellum detached from
the main mask).

| Rating | Visual Description |
|--------|--------------------|
| **Pass** | Mask is continuous; no internal holes; AFNI outline shows one coherent boundary without disconnected islands outside the main brain |
| **Borderline** | 1–2 small internal holes or 1 small isolated outline loop; not in critical regions |
| **Fail** | Multiple large internal holes or multiple disconnected fragments/outline loops; mask is not topologically valid |

---

### 5. Boundary tightness (not over-dilated into dura/CSF)

**What to look for:** The red boundary and AFNI outline should follow the pial
surface closely. Over-dilation appears as a soft/bloated mask edge extending
well into the dark CSF space surrounding the brain. Common near the
interhemispheric fissure and the Sylvian fissure. The outline view is especially
important here because it makes small boundary offsets easier to see.

| Rating | Visual Description |
|--------|--------------------|
| **Pass** | Mask boundary and AFNI outline follow the brain surface; CSF ring visible outside the mask |
| **Borderline** | Mask/outline extends a few voxels into CSF/sulci; boundary not sharp but brain volume unlikely to be substantially overestimated |
| **Fail** | Mask is clearly bloated; AFNI outline runs through CSF/dura rather than the brain edge; boundary tracking is poor |

---

## Overall Verdict

| Verdict | Criteria |
|---------|---------|
| **Pass** | All 5 criteria rated Pass or at most 1 Borderline; quantitative volume within expected range |
| **Borderline** | 2–3 criteria rated Borderline, OR 1 minor criterion rated Fail with others Pass; may be usable with caution |
| **Fail** | 2+ criteria rated Fail, OR any single Fail that affects core brain volume, tissue inclusion/exclusion over a large contiguous region, or symmetry/centering |

Hard-stop rules:
- Overall **Pass** is not allowed if the symmetry criterion is Borderline or
  Fail.
- Overall **Pass** is not allowed if any quantitative warning is present unless
  the report explicitly explains why the warning is benign.
- Overall **Borderline** is the best possible verdict when a mask is visibly
  asymmetric but the affected region is small.
- Overall **Fail** is required when asymmetry is large, consistent across
  several slices, or likely to bias downstream registration, segmentation, or
  volumetry.
- If the AFNI outline contradicts the filled overlay, use the worse rating.
  A clean-looking filled overlay must not override an outline that is shifted,
  asymmetric, or anatomically misplaced.

---

## Confidence Levels

| Confidence | When to use |
|-----------|-------------|
| **High** | Image quality is good; criteria are clearly identifiable in all planes |
| **Medium** | Image quality is moderate (motion, noise, low contrast) but criteria are mostly assessable |
| **Low** | Image quality is poor, unusual anatomy, or pathology makes visual assessment genuinely uncertain |

---

## Common Artefacts Reference

| Artefact | Typical location | Which criterion |
|---------|-----------------|----------------|
| Temporal pole clipping | Inferior coronal, sagittal | Criterion 2 |
| Frontal pole erosion | Anterior axial, sagittal | Criterion 2 |
| Dural sinus inclusion | Superior sagittal sinus region | Criterion 5 |
| Eye orbit inclusion | Inferior axial slices | Criterion 1 |
| Disconnected cerebellar fragment | Inferior axial/coronal | Criterion 4 |
| Interhemispheric fissure bloat | Mid-axial, coronal | Criterion 5 |
| Scalp fat ring included | Outer ring, all axial | Criterion 1 |
