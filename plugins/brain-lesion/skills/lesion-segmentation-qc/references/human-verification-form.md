# Human Verification Form — Lesion Segmentation

Blank template for the human reviewer. Write an unfilled copy to
`qc/<prefix>_<tool>_<timestamp>_lesion_human_eval.md`.

Criterion labels match the numeric output and the AI report word-for-word so
agreement can be scored later. Leave the wording alone.

Fill this in **before** reading the AI report where you can — an independent
rating is what makes the agreement number mean anything.

```markdown
## Human Lesion Segmentation QC

**Subject:** <prefix>
**Lesion type:** <acute_stroke | chronic_stroke | wmh>
**Segmentation tool:** <tool/version>
**Timestamp:** <YYYYMMDD-HHMMSS>
**Reviewer:** <name or initials>
**Reviewed before reading the AI report?** <yes / no>

**Reviewed:** `qc/<...>_lesion_qc.png`  (metrics: `qc/<...>_lesion_qc.json`)

### Criteria

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Lesion volume is plausible for the stated type | | |
| Lesion is contained within the brain mask | | |
| Spatial pattern matches the stated lesion type | | |
| Labelled voxels carry the expected intensity signature | | |
| Mask is not dominated by noise specks | | |
| Lesion boundary follows the true lesion edge | | |
| No lesions were missed | | |

The last two are yours alone — the numeric battery cannot assess either. Boundary
accuracy needs an eye on the image, and completeness cannot be judged from a mask
that by definition does not contain what was missed.

### Missed lesions
<List anything the segmenter did not find, with slice numbers. This is the most
valuable thing in the form: false negatives are close to invisible numerically,
so this field is the only systematic record of them.>

### Is it actually this lesion type?
<Does the pathology match the declared type, or does it look like something else
— tumour, MS, abscess, perivascular spaces, artefact?>

### Overall Verdict
**<Pass / Borderline / Fail>** — Confidence: <High / Medium / Low>

### Do you agree with the AI assessment?
- Agreement: <full / partial / disagree>
- Criteria where you differ: <criterion, both ratings>
- What the AI missed or over-called: <free text>

### Recommended action
<none | re-run with different parameters | switch tools | manual editing |
exclude this subject>
```

## Scoring agreement later

Two patterns are worth watching across a batch.

**Systematic direction.** If the AI is consistently more lenient on one
criterion, fix the threshold or the criterion wording rather than the individual
cases.

**Completeness.** Because "No lesions were missed" is human-only, it is the one
criterion with no numeric counterpart — and therefore the clearest measure of
what the numeric battery is failing to see. If reviewers keep finding missed
lesions on masks that passed every numeric check, that is a gap in the battery,
not reviewer noise.
