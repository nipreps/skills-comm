# Human Brain Extraction QC Verification Form

Complete this form after reviewing both QC PNGs: the Python filled-mask overlay
and the AFNI edge-outline overlay. Use the same rating scale as the AI
evaluation (Pass / Borderline / Fail) so that agreement can be computed.

The AI evaluation for this case is at: `qc/<subject>_<tool>_<timestamp>_ai_eval.md`

---

## Case Information

| Field | Value |
|-------|-------|
| **Subject** | |
| **Tool used** | |
| **Original image** | |
| **Brain mask** | |
| **Python QC PNG reviewed** | |
| **AFNI outline QC PNG reviewed** | |
| **Rater name** | |
| **Date reviewed** | |
| **Time spent (minutes)** | |

---

## Quantitative Review

| Metric | Value (from PNG title or AI eval) | Within expected range? |
|--------|-----------------------------------|----------------------|
| Brain volume (cm³) | | Yes / No / Uncertain |
| Coverage fraction (%) | | — |

*Expected adult T1w range: 900–1800 cm³. Flag if outside this range.*

---

## Visual Criteria

Rate each criterion: **Pass**, **Borderline**, or **Fail**.
Add brief notes explaining any Borderline or Fail rating.

### 1. No residual skull or scalp signal

Check whether the filled overlay or AFNI outline includes skull, scalp, eyes,
dura, or other non-brain tissue.

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 2. No excessive tissue loss at poles (frontal, temporal, occipital)

Check whether the AFNI outline cuts through visible cortex, especially at the
frontal, temporal, occipital, inferior, and cerebellar boundaries.

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 3. Symmetric left-right and anterior-posterior coverage

Check the full axial and coronal rows, not just a single slice. Use the AFNI
outline as the primary check for whether the mask boundary tracks both
hemispheres evenly. Mark this criterion **Fail** if one side or one
anterior/posterior end is consistently clipped, over-expanded, or shifted enough
to bias registration, segmentation, or volumetry. Mark it **Borderline** if
asymmetry is repeatable but small and peripheral.

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 4. No internal holes or disconnected mask regions

Check for internal holes in the filled overlay and disconnected outline loops or
islands in the AFNI outline PNG.

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 5. Boundary tightness (not over-dilated into dura/CSF)

The AFNI outline should hug the brain edge. Downgrade this criterion if the
outline runs through CSF/dura, cuts cortex, or follows a bloated boundary.

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

## Overall Verdict

| | |
|-|-|
| **Overall rating** | Pass / Borderline / Fail |
| **Confidence** | High / Medium / Low |

---

## Free-Text Notes

*(Anything not captured above: unusual anatomy, image artefacts, pathology, scanner characteristics, etc.)*

---

## Recommended Action

- [ ] None — extraction is acceptable for downstream use
- [ ] Re-run with adjusted parameters: *(specify)*
- [ ] Manual mask editing recommended
- [ ] Exclude this subject from analysis

---

## Agreement Check (optional — fill in after reviewing AI eval)

*Compare your ratings to the AI evaluation and note any discrepancies.*

| Criterion | Your rating | AI rating | Agreement? |
|-----------|-------------|-----------|------------|
| No residual skull or scalp | | | Yes / No |
| No excessive tissue loss at poles | | | Yes / No |
| Symmetric coverage | | | Yes / No |
| No internal holes or disconnected regions | | | Yes / No |
| Boundary tightness | | | Yes / No |
| **Overall verdict** | | | Yes / No |

**Notes on disagreements:**
