---
name: lesion-segmentation
description: >
  Route a brain-lesion segmentation request when the lesion type is not yet
  established. Invoke for generic requests such as "segment this lesion" or
  "make a lesion mask", or when acute stroke, chronic stroke, WMH, MS, tumour,
  and haemorrhage remain ambiguous. Do not invoke when the user has already
  explicitly confirmed acute ischaemic stroke, chronic stroke, or WMH; use the
  corresponding pathology-specific segmentation skill directly.
---

# Lesion segmentation router

Do not segment from this skill. Establish whether the available evidence
supports a pathology-specific workflow, then hand off once or report why the
case cannot be routed safely.

## 1. Establish the lesion type

Do not require a prior radiology diagnosis before starting identification. The
available MRI is the evidence used to propose a lesion-type hypothesis; clinical
history is useful context but optional. If images or required modalities are
missing, report the limitation and stop without asking the user to supply a
diagnosis. Do not treat the model's hypothesis as a clinical diagnosis.

If the original request explicitly names acute ischaemic stroke, chronic stroke,
or WMH, invoke the corresponding specific skill directly. Do not run
identification again or require an extra confirmation for a task already
established by the request.

Invoke `lesion-identification`. Inventory the available modalities, run its
quantitative signature probe, and perform its visual review when image viewing
is available. The review should distinguish:

- restricted diffusion from T2 shine-through;
- chronic encephalomalacia/cavity from acute infarction;
- bilateral periventricular/deep WMH from focal infarct and MS-like morphology;
- in-scope disease from haemorrhage, tumour, or another focal lesion.

Record the proposed type, supporting measurements and visual features,
important missing modalities, and credible alternatives. Route only when the
request or existing task context establishes the pathology, or when
`lesion-identification` returns `segmentation_eligible: true` under its
evidence rule. If evidence is equivocal,
stop with the evidence and uncertainty; do not ask the user and do not create a
mask.

If the evidence suggests MS, tumour, haemorrhage, or another unsupported type,
stop after reporting the finding. Never force it into one of the supported
segmentation skills merely to produce a file.

## 2. Handoff

Pass the task-established or eligible candidate type, all input paths, requested output path/reference grid,
signature JSON, visual observations, and any validated brain mask to exactly
one of:

- `acute-stroke-segmentation`;
- `chronic-stroke-segmentation`; or
- `wmh-segmentation`.

Tool choice, execution, publication, and QC belong to that specific skill.

## Constraints

- Never make a clinical diagnosis or force an unsupported lesion into an
  available segmenter.
- Do not ask the user to choose a tool, supply a diagnosis, or confirm a
  hypothesis. If required evidence is missing or ambiguous, report the gap and
  stop without a mask.
- Preserve the input files and pass evidence and uncertainty to the selected
  skill.
