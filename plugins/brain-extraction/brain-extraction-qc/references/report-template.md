# AI QC Report Template

Fill in every field. Where a value is unknown, write what is actually true
(`not measured`, `UNVERIFIED`, `no vision available`) rather than leaving a
placeholder or inventing a plausible number — a report whose gaps are visible
stays useful; one with invented content is worse than none.

Save to `qc/<prefix>_<tool>_<timestamp>_ai_eval.md`.

```markdown
## AI Brain Extraction QC

**Subject:** <prefix>
**Tool:** <tool>
**Timestamp:** <YYYYMMDD-HHMMSS>
**Original image:** <anat path>
**Brain mask:** <mask path>
**Metrics JSON:** <metrics json path>
**AFNI outline PNG:** <outline png path>
**Mosaic PNG:** <mosaic png path, or "not generated">

**Evidence basis:** <numeric-only | numeric + visual>
**Vision available:** <yes | no>

### Quantitative

| Metric | Value | Reference | Rating |
|--------|-------|-----------|--------|
| Brain volume | X cm³ | 900–1900 cm³ (adult T1w) | |
| Brain / head ratio | X | 0.44–0.62 | |
| Shallow mask fraction | X% | ≤2% | |
| Bright rim fraction | X% | ≤0.10% | |
| L-R mirror Dice | X | ≥0.95 | |
| L-R volume asymmetry | X% | ≤12% | |
| Centroid offset from midline | X mm | ≤6 mm | |
| Connected components / holes | N / X cm³ | 1 / ≤0.5 cm³ | |
| Dark voxel fraction | X% | 2–12% | |
| Rim / core intensity | X | 0.18–0.42 | |

Head symmetry Dice (midline search quality): <X — expect >0.97>

### Criteria

| Criterion | Rating | Evidence |
|-----------|--------|----------|
| No residual skull or scalp signal | Pass / Borderline / Fail | <cite the metric values; add visual observation if seen> |
| No excessive tissue loss at poles (frontal, temporal, occipital) | Pass / Borderline / Fail | <as above> |
| Symmetric left-right and anterior-posterior coverage | Pass / Borderline / Fail | <cite Dice, volume asymmetry, centroid offset; state which axial bands if localised> |
| No internal holes or disconnected mask regions | Pass / Borderline / Fail | <as above> |
| Boundary tightness (not over-dilated into dura/CSF) | Pass / Borderline / Fail | <as above> |
| Dura / superior sagittal sinus inclusion | Pass / Borderline / Fail / **UNVERIFIED** | <UNVERIFIED on any run without visual inspection> |

### Symmetry detail
- Mirror Dice about the mid-sagittal plane: <value and what it implies>
- Left vs right volume: <L cm³ vs R cm³, asymmetry %>
- Centroid offset from midline: <mm>
- Distribution across axial bands (inferior→superior): <list; note any concentration>
- Anatomy/pathology explanation: <stroke, resection, mass effect, atrophy,
  ventriculomegaly, partial FOV — or "none identified">

### Numeric / visual agreement
<Only on runs with vision. State any disagreement between what the metrics said
and what the image showed, which you trusted, and why. Write "consistent" if
they agreed, or "not applicable — numeric-only run" if there was no vision.>

### Overall Verdict
**<Pass / Borderline / Fail>** — Confidence: <High / Medium / Low>

<On numeric-only runs cap confidence at Medium and state:
"Dura / superior sagittal sinus inclusion could not be assessed without visual
review.">

<If overturning the script's numeric verdict, say so explicitly and give the
reason — anatomy, pathology, acquisition, or population mismatch.>

### Notes
<Image quality, unusual anatomy, artefacts, population mismatch with the
reference ranges, anything a later reader would want flagged.>

### Recommended action
<none | re-run with adjusted parameters: <specific flag changes> |
manual mask editing | human visual review required>
```

## Confidence

| Level | When |
|---|---|
| **High** | Metrics unambiguous and, where vision was available, image agrees |
| **Medium** | Numeric-only run (the ceiling), or moderate image quality, or metrics near a threshold |
| **Low** | Poor image quality, unusual anatomy or pathology, midline search degraded (`head_symmetry_dice` < 0.97), or metrics and vision disagree unresolved |
