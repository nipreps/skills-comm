# Human Brain Extraction QC Verification Form

Complete this form after reviewing the QC PNG. Use the same rating scale as the
AI evaluation (Pass / Borderline / Fail) so that agreement can be computed.

The AI evaluation for this case is at: `qc/<subject>_<tool>_<timestamp>_ai_eval.md`

---

## Case Information

| Field | Value |
|-------|-------|
| **Subject** | |
| **Tool used** | |
| **Original image** | |
| **Brain mask** | |
| **QC PNG reviewed** | |
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

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 2. No excessive tissue loss at poles (frontal, temporal, occipital)

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 3. Symmetric left-right and anterior-posterior coverage

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 4. No internal holes or disconnected mask regions

| | |
|-|-|
| **Rating** | Pass / Borderline / Fail |
| **Notes** | |

---

### 5. Boundary tightness (not over-dilated into dura/CSF)

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
