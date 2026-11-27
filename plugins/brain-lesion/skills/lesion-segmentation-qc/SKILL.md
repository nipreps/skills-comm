---
name: lesion-segmentation-qc
description: >
  Validate a brain lesion segmentation, with or without image vision. Runs a
  lesion-type-aware numeric battery (volume plausibility, containment within the
  brain, cluster pattern, laterality, and whether the labelled voxels carry the
  expected intensity signature), renders a QC overlay PNG, and writes a
  structured report plus a paired human verification form. Invoke after any
  lesion segmentation, or standalone with "QC the lesion mask", "check the
  lesion segmentation", "validate the WMH mask", "review the stroke
  segmentation", "is this lesion mask any good", or "lesion-segmentation-qc".
  Also invoke when the user references a file ending in `_lesion.nii.gz`,
  `_lesion_mask.nii.gz`, or `_wmh.nii.gz` and asks to check or validate it.
metadata:
  short-description: QC a lesion mask (type-aware numeric battery)
---

# Skill: lesion-segmentation-qc

Validate a lesion mask on measured evidence, then look at it if you can.

A lesion mask cannot be judged the way a brain mask can. There is no expected
volume, no expected shape, and no symmetry requirement — and the correct answer
differs by lesion type in ways that directly invert each other. One large
unilateral component can be appropriate for stroke and can be suspicious for
small-vessel WMH, although confluent WMH can form a dominant component.
**The lesion type is therefore a required input**, and QC that
does not know it is not QC.

Two checks carry most of the weight, and neither needs vision:

**Containment.** Lesion voxels outside the brain mask flag a containment
concern. They may reflect a lesion-mask error or an overly tight brain mask;
inspect both masks and report which interpretation the available evidence
supports.

**Signature.** Do the labelled voxels actually carry the intensity the lesion
type implies — FLAIR-bright for WMH, CSF-dark on T1 for a chronic cavity,
restricted diffusion for an acute infarct? This is the check that catches a
segmenter confidently outlining normal-appearing tissue, which is the failure
mode a plausible-looking mask hides best.

## Workflow

1. Establish the lesion type from the request or upstream evidence; never
   guess.
2. Resolve exact-grid upstream inputs through the producer skills.
3. Run the numeric battery and save `metrics.json`.
4. Render the overlay PNG for human review.
5. If image vision is available, inspect the overlay and reconcile it with the
   numeric results; otherwise mark boundary accuracy UNVERIFIED.
6. Write the report and blank human verification form.
7. Summarise the verdict and unresolved checks.

### 1. Establish the lesion type

Take it from the `lesion-segmentation` handoff or an established task context;
do not infer it from a filename. If it is unknown, run
`lesion-identification` first. If the type remains unresolved, report that QC
cannot select a type-specific signature and stop.

### 2. Resolve exact-grid upstream inputs

Read `references/upstream-artifacts.md` before creating or transforming a brain
mask or defining modality. The lesion mask, brain mask, and every modality used
for an intensity signature must match in both shape and affine.

If a validated brain mask on the lesion grid does not already exist, invoke
`brain-extraction` and explicitly pass the lesion-grid anatomical as
`REFERENCE_GRID`, even when extraction itself uses another coregistered image.
That producer skill owns tool selection, exact invocation, grid mapping, output
selection, publication, and its `references/*.md` contracts. Do not
independently invoke SynthStrip, BET, HD-BET, AFNI, or another extractor from
this QC skill, and do not reconstruct a command from memory.

The numeric QC option is exactly `--brain-mask <path>` (hyphenated). It is not
`--mask`, `--brain`, or `--brain_mask`. Run `--help` before the battery if the
interface is in doubt; do not infer flags from another QC skill.

If no suitable output-grid anatomical or validated registration exists, mark
containment or the intensity signature UNVERIFIED. Do not manufacture alignment
solely to turn an UNVERIFIED criterion into a pass.

If the brain mask is unavailable and the brain-extraction publisher does not
support the anatomy, report `QC incomplete: brain mask unavailable`. Leave
containment UNVERIFIED; do not improvise or hand-draw a replacement mask.

### 3. Run the numeric battery

In the retained SLURM script, set `SKILL_DIR` to the resolved installed
directory for this skill and resolve the host Python interpreter before loading
any neuroimaging module. Do not rely on agent variables being passed to Slurm.
These numeric and overlay helpers use the pinned host packages in the plugin's
`python-requirements.txt`; no FSL module is required for these helper calls.
Run all image reads and metrics in the submitted job.

```bash
SKILL_DIR="/absolute/path/to/lesion-segmentation-qc" # Replace with the installed path before submission.
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/lesion_qc_metrics.py"
"${HELPER_PYTHON}" -c "import numpy, nibabel, scipy, matplotlib"
mkdir -p qc logs
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
printf '%s\n' "${TIMESTAMP}" | tee "logs/qc_timestamp_${SLURM_JOB_ID}.txt"
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/lesion_qc_metrics.py" \
  --lesion "<lesion_mask>" \
  --type wmh \
  --brain-mask "<brain_mask>" \
  --flair "<FLAIR>" \
  --json "qc/<prefix>_<tool>_${TIMESTAMP}_lesion_qc.json"
```

For chronic stroke, use `--type chronic_stroke --t1 <T1w>` instead of the
WMH type and FLAIR option. For acute stroke, use
`--type acute_stroke --dwi <DWI> --adc <ADC>`. Do not put shell comments in
the middle of a continued command.

Check the pinned `numpy`, `nibabel`, `scipy`, and `matplotlib` versions in
`${SKILL_DIR}/../../python-requirements.txt`. If a dependency is missing,
report the environment limitation; do not install packages during the QC run.

**Supply an exact-grid brain mask.** Without it containment cannot be checked at all, and
the midline is estimated from the lesion itself, which makes laterality
meaningless — a unilateral lesion defines a "midline" through its own centre.
When an output-grid anatomical exists, failure to obtain this dependency leaves
the QC incomplete; do not call the overall QC done merely because the other
criteria ran.

**Supply the modality the lesion type is defined on.** Without it the signature
check is skipped, and a mask over normal-appearing tissue becomes
indistinguishable from a correct one. The script marks this UNVERIFIED and says
so rather than passing quietly.

Read `references/lesion-qc-criteria.md` for what each metric means, the
type-specific expectations, and the known limits.

### 4. Render the overlay PNG

Always produce it, vision or not — the human reviewer needs it, and it is what
the human form is filled in against.

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/lesion_overlay_qc.py" \
  "<anatomical>" "<lesion_mask>" "qc/<prefix>_<tool>_${TIMESTAMP}_lesion_qc.png"
```

Slices are chosen where the lesion actually is, not spread across the whole
volume. A montage of mostly lesion-free slices is how a small missed lesion
passes review.

### 5. Visual review — only if you can see images

Vision earns its keep on the things the battery cannot measure:

- **boundary accuracy** — whether the outline follows the actual lesion edge, as
  opposed to merely sitting somewhere plausible
- **missed lesions** — the battery scores what was labelled, and is largely blind
  to what was not. A segmenter that finds three of eight WMH foci can pass every
  numeric check.
- **is it really that lesion** — a tumour, abscess or demyelinating plaque can
  satisfy the intensity signature of the type you declared

If you cannot open images, say so, rate what the numbers support, mark boundary
accuracy and completeness UNVERIFIED, and cap confidence at Medium.

### 6. Reports

After the QC job completes, read its timestamp file using the captured Slurm
job ID. Use that value for both report names so they match the JSON and overlay
produced by the job.

```bash
TIMESTAMP="$(cat "logs/qc_timestamp_${JOB_ID}.txt")"
```

Write the QC report to `qc/<prefix>_<tool>_<timestamp>_lesion_ai_eval.md`, and a
blank human form from `references/human-verification-form.md` to
`qc/<prefix>_<tool>_<timestamp>_lesion_human_eval.md`.

Keep criterion labels identical across the numeric output, the report and the
form so AI/human agreement can be scored later. The human form carries two
criteria the battery has no counterpart for — boundary accuracy and completeness
— which makes it the only systematic record of what the numbers cannot see.

### 7. Summarise

Verdict, confidence, evidence basis, artefact paths, each Borderline/Fail
criterion with the number that drove it and a concrete recommended action, and
the standing caveats about completeness and boundary accuracy.

## What this cannot do

**It cannot find what the segmenter missed.** Every metric describes the mask
that exists. False negatives are close to invisible numerically, and on WMH in
particular a segmenter that under-calls burden can pass cleanly. Only visual
review, or comparison against the burden `lesion-identification` measured
independently, will catch it — do that comparison when the signature JSON is
available.

**It cannot confirm the diagnosis.** The signature check confirms the labelled
voxels look like the declared lesion type. Several pathologies share a
signature.

**Volume ranges are sanity bounds, not clinical norms.** They catch empty masks
and whole-hemisphere masks. A volume inside the range is not evidence of
correctness.

## Constraints

- Require the lesion type. Never infer it from a filename, and never run with a
  guessed type.
- Treat upstream artifacts as producer-owned dependencies. Invoke
  `brain-extraction` for a missing brain mask; never improvise an extraction
  command inside lesion QC.
- Require exact shape and affine agreement for the lesion mask, brain mask, and
  signature modalities. A same-sized image is not necessarily on the same grid.
- Always supply the brain mask and the defining modality when they exist; report
  explicitly when they do not and what that left unchecked.
- Never write a rating you did not measure or see.
- When a `lesion-identification` signature JSON exists, report its estimated
  burden beside the mask volume and the percent difference. Treat disagreement
  as a warning for review, not a failure by itself, because the probe may use
  an unreliable fallback mask or miss subtle lesions.
- The publisher's 0.5–500 cm3 interval is a software contract, not a clinical
  range. State when a candidate falls outside it; never inflate or clip a mask
  to satisfy the gate.
- Cap confidence at Medium for numeric-only runs and state the evidence basis.
- Quote actual numbers, not just ratings.
- Always produce the overlay PNG, even with no vision.
