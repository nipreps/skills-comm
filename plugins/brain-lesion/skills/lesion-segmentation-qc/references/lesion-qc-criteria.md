# Lesion QC Criteria

What `scripts/lesion_qc_metrics.py` checks, why the checks are type-dependent,
and what they cannot see.

## Why the lesion type is required

A brain mask has a right answer that barely varies between subjects: roughly
this volume, roughly this shape, roughly symmetric. A lesion mask has none of
that. Worse, the expectations for different lesion types directly contradict
each other:

| | acute / chronic stroke | WMH |
|---|---|---|
| Cluster count | one dominant | many |
| Largest cluster share | high (≥50%) | low (≤70%) |
| Laterality | unilateral (≥25%) | bilateral (≤40%) |

A single check cannot serve both. Running with the wrong type produces a
confident wrong verdict in whichever direction the mistake points — which is why
the type is a required argument rather than an optional hint.

## Criteria

### Lesion volume is plausible for the stated type

| Type | Range (cm³) |
|---|---|
| acute_stroke | 0.5 – 300 |
| chronic_stroke | 1.0 – 400 |
| wmh | 0.5 – 200 |

Deliberately wide. These catch order-of-magnitude failures — an empty mask, a
whole-hemisphere mask, a segmenter that returned its input. They are **sanity
bounds, not clinical norms**, and a volume inside the range is not evidence of
correctness.

### Lesion is contained within the brain mask

Lesion voxels in skull, scalp or air are unambiguous failures with no benign
reading. PASS ≤1%, BORDERLINE ≤5%, FAIL above.

Requires a brain mask. Without one this is UNVERIFIED *and* the midline falls
back to the lesion's own centroid, which makes laterality meaningless — a
unilateral lesion defines a midline through itself and then measures itself as
perfectly central. Supply the mask.

### Spatial pattern matches the stated lesion type

Compares largest-cluster fraction and laterality against the expectations above.
This is what catches a WMH mask presented as a stroke, or a stroke tool's output
accepted as WMH.

**Genuine anatomy can fail this legitimately.** Bilateral strokes exist.
Strongly asymmetric WMH exists, particularly alongside an old infarct. A failure
here is a prompt to look, and a reviewer may overturn it in writing.

### Labelled voxels carry the expected intensity signature

The check that catches a segmenter confidently outlining normal-appearing
tissue — the failure a plausible-looking mask hides best.

| Type | Modality | Measure | PASS |
|---|---|---|---|
| wmh | FLAIR | median robust-z inside mask vs normal-appearing brain | ≥1.5 |
| chronic_stroke | T1 | median mask intensity ÷ normal brain | ≤0.7 |
| acute_stroke | DWI + ADC | DWI robust-z, ADC ratio | ≥1.0 and ≤0.85 |

Self-calibrating: the comparison is against non-lesion brain in the same scan,
dilated away from the mask so the reference is not contaminated by lesion edge.

Skipped, and reported UNVERIFIED, when the defining modality is absent. That
gap matters — without it a mask over normal tissue is numerically
indistinguishable from a correct one.

### Mask is not dominated by noise specks

Flags when most clusters are under 0.02 cm³ across more than 20 clusters. Usually
means a probability threshold is too low, or a minimum-cluster filter is missing.
Rarely fatal on its own; often the reason a volume is inflated.

## Verdict

Any failing criterion fails the mask. Each maps to a defect that would propagate
into volumetry or lesion-symptom mapping. Overturn it in writing, with a reason —
"bilateral infarcts, confirmed visually" is a reason; "looks fine" is not.

## What this cannot see

**Missed lesions.** Every metric describes the mask that exists. A segmenter
finding three of eight WMH foci can pass every check here. Only visual review, or
comparison against the burden `lesion-identification` measured independently,
will catch it — and that cross-check is cheap whenever the signature JSON exists.
It is the single most valuable thing to do beyond this script.

**Boundary accuracy.** Whether the outline follows the true lesion edge, rather
than merely sitting somewhere plausible, is not measured at all.

**Whether it is really that lesion.** The signature check confirms the labelled
voxels look like the declared type. Tumour, abscess and demyelination can all
satisfy a FLAIR-bright signature.

## When ground truth exists

This battery judges a mask on its own, because usually there is nothing to
compare against. When there *is* a reference — a manual tracing, a second
rater, or another tool's output — overlap metrics answer a different and
sharper question, and `panoptica/2.1.3` is installed for exactly this. It gives
instance-wise evaluation (matching, panoptic quality, Dice) rather than a single
whole-mask Dice, which matters for multifocal disease: a WMH segmenter that
merges eight foci into three blobs can score well on voxel Dice while getting
the lesion count badly wrong.

It is a Python library with no command-line tool — load the module and import it.

Use it in addition to this battery, not instead: overlap against one rater says
nothing about containment, and nothing about whether both you and the rater
missed the same lesion.

## Validation status

Validated on synthetic phantoms with derived ground-truth masks and deliberate
failures. All eight cases classify correctly:

| Case | Expected | Result |
|---|---|---|
| correct WMH mask, type=wmh | PASS | PASS |
| correct acute mask, type=acute_stroke | PASS | PASS |
| correct chronic mask, type=chronic_stroke | PASS | PASS |
| WMH mask declared as acute_stroke | FAIL | FAIL (pattern + signature) |
| mask shifted outside the brain | FAIL | FAIL (containment + signature) |
| empty mask | FAIL | FAIL |
| whole hemisphere | FAIL | FAIL (volume + pattern + signature) |
| blob over normal-appearing tissue | FAIL | FAIL (pattern + signature) |

Phantoms, not patients. The checks and threshold directions are right; the exact
cut-offs are not calibrated against clinical data. Retune `VOLUME_RANGE_CM3` and
`EXPECT` for a different population, and rerun the suite in
`skills/lesion-workspace/` after any change.
