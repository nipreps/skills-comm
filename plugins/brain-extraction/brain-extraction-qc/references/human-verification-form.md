# Human Verification Form

Blank template for the human reviewer. Write an unfilled copy to
`qc/<prefix>_<tool>_<timestamp>_human_eval.md`.

The criterion labels below match the numeric output and the AI report
word-for-word. Agreement between AI and human ratings is scored on those labels,
so a reworded criterion silently drops out of that comparison — leave the
wording alone.

Fill this in **before** reading the AI report where you can. An independent
rating is what makes the agreement number mean anything; a rating anchored on
the AI's answer mostly measures the anchoring.

```markdown
## Human Brain Extraction QC

**Subject:** <prefix>
**Tool:** <tool>
**Timestamp:** <YYYYMMDD-HHMMSS>
**Reviewer:** <name or initials>
**Date reviewed:** <YYYY-MM-DD>
**Reviewed before reading the AI report?** <yes / no>

**Images reviewed:**
- AFNI outline PNG: `qc/<...>_afni_outline_qc.png`   <- rate from this one
- Mosaic PNG: `qc/<...>_qc.png`                       <- supporting context
- Metrics JSON: `qc/<...>_metrics.json`               <- supporting context

### Criteria

Rate each Pass / Borderline / Fail. Base visual ratings on the outline PNG.

| Criterion | Rating | Notes |
|-----------|--------|-------|
| No residual skull or scalp signal | | |
| No excessive tissue loss at poles (frontal, temporal, occipital) | | |
| Symmetric left-right and anterior-posterior coverage | | |
| No internal holes or disconnected mask regions | | |
| Boundary tightness (not over-dilated into dura/CSF) | | |
| Dura / superior sagittal sinus inclusion | | |

### Symmetry observations
- Axial left/right: <balanced, or which side is clipped/expanded/shifted>
- Coronal left/right: <are both hemispheres tracked evenly>
- Anterior/posterior: <is coverage balanced in sagittal and axial>
- Anatomy/pathology explanation: <if asymmetry is visible, is it explained by
  stroke, resection, mass effect, atrophy, ventriculomegaly, or field of view —
  otherwise "none">

### Overall Verdict
**<Pass / Borderline / Fail>** — Confidence: <High / Medium / Low>

### Do you agree with the AI assessment?
<Complete after reading `qc/<...>_ai_eval.md>`

- Agreement: <full / partial / disagree>
- Criteria where you differ: <list criterion and both ratings>
- What the AI missed or over-called: <free text — this is the most useful
  field in the form; it is what improves the rubric and the thresholds>
- If the run was numeric-only, was the dura judgement it deferred actually a
  problem? <yes / no / n-a>

### Recommended action
<none | re-run with adjusted parameters: <specifics> | manual mask editing |
accept with documented caveat>

### Free-text notes
<Anything else worth recording for this subject.>
```

## Scoring agreement later

With matched labels across both files, agreement can be computed per criterion
across a batch — simple percent agreement, or Cohen's kappa treating
Pass/Borderline/Fail as ordered.

Two patterns are worth watching for specifically:

**Systematic direction.** If the AI is consistently more lenient than humans on
one criterion, the threshold or the rubric wording is off, not the individual
call. Fix it in `THRESHOLDS` or in the criterion description rather than
case-by-case.

**Numeric-only versus visual runs.** Agreement on numeric-only runs, compared
against runs where the model could see the image, is the direct measure of what
vision is actually buying. If it turns out to be buying little beyond dura, that
is worth knowing — and if it is buying a lot, that says the numeric battery has
a gap worth closing.
