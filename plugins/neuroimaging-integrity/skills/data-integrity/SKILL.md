---
name: data-integrity
description: >
  Check downloaded or task-input neuroimaging data for corruption, missing or
  duplicate files/slices, inconsistent acquisition metadata, and geometry
  problems. Invoke after download or before analysis when input integrity is
  unknown. Trigger on requests such as "check the DICOM series is complete",
  "audit these NIfTI files", or "verify the MRI data integrity". Does not
  diagnose image content or repair metadata.
metadata:
  short-description: Verify neuroimaging input integrity
---

# Neuroimaging data integrity

Establish whether the received files are complete enough, internally consistent,
and spatially interpretable for the requested analysis. Run after each download
or transfer and at task start when no trustworthy audit exists. Keep the audit
read-only: never rename, delete, decompress over, rewrite headers, or silently
repair source data. Write reports and any derived manifests separately.

**Execution boundary:** perform the audit through the environment's required
batch workflow. On Neurodesk, write a retained `analysis_<step>_data_integrity.sh`
with an explicitly version-pinned module, then submit it to Slurm and inspect
the job and logs. This applies to every audit operation that opens, decompresses,
parses, hashes, or computes from input files, including preliminary checks and
debugging retries. Do not run NIfTI/DICOM readers, voxel statistics, gzip tests
on image inputs, or the audit script directly in an interactive shell. Only
module/resource discovery that does not access the input data may run before
the batch script is submitted. Before submission, limit module discovery to the
single selected parser/tool and exact version (for example,
`module spider fsl/6.0.7.23`); do not dump or search the full module catalog.
Do not submit a separate environment-only probe job: put the module load and
runtime checks at the start of the audit script itself.
Safe pre-submit commands do not mention image paths. In particular, do not use
`fslhd`, `fslinfo`, `fslval`, `fslstats`, Python image libraries, `gzip -t`, or
any other reader/test against an input until that command is inside the Slurm
script. If a trustworthy current audit already exists, reuse it instead of
repeating its image reads.

Limit discovery to the supplied input, this task's output workspace, relevant
skill references, and the documented tool/module catalog. Do not search the
filesystem root, unrelated home directories, system or historic Slurm logs,
other datasets, or unrelated datasets. If required provenance or a tool is
not available in that scope, report the limitation instead of broadening the
search.

## 1. Establish the expected dataset

First identify the source and its completeness contract: BIDS dataset metadata,
download manifest, archive listing, DICOM study/series inventory, expected
subject/session/scan list, or a trusted checksum file. Record the source, audit
time, tool versions, and paths examined. If there is no independent expected
inventory or checksum, state that limitation: internal consistency cannot prove
that an entire scan, series, or slice was never omitted.

Use the host harness's normal, documented tools and execution constraints.
Prefer source-provided checksums or manifests. For remote datasets, compare the
local result with the provider's inventory and checksums when available. Do not
download or replace files unless the user requested that action. Avoid logging
identifying DICOM metadata beyond what is necessary for the audit.

## 2. Run the checks

### Transfer and file integrity

- Compare file counts, relative paths, byte sizes, and cryptographic hashes
  (prefer SHA-256) with a trusted source manifest when available.
- Verify archive integrity and expected member inventory before extraction or
  after transfer. Detect truncated files, zero-byte files, duplicate paths,
  unexpected members, and failed decompression.
- A newly generated local checksum manifest records current bytes; by itself it
  does not prove the download was complete or authentic.

### Dataset and metadata consistency

- For BIDS, validate required structure, names, entities, and JSON sidecars with
  a compatible BIDS validator when available. Check that sidecars are parseable
  and that required metadata is present for the requested analysis.
- Compare filenames and metadata with image headers and content: modality,
  dimensions, units, voxel spacing, orientation, acquisition parameters, and
  expected value ranges. Flag contradictions rather than selecting whichever
  field supports the expected analysis.
- Interpret intensity units using documented sidecars, conversion records,
  NIfTI scaling fields, or other source metadata when available. For ADC maps,
  common representations include values in mm²/s and values scaled by 10⁻⁶;
  do not infer a unit mismatch from raw quantiles alone. If the convention is
  undocumented or ambiguous, report the observed stored-value range and mark
  the unit check as WARNING or NOT CHECKED rather than calling the modality
  inconsistent. Keep this unit uncertainty separate from the overall
  completeness status.
- Check that each expected subject/session/acquisition exists and that related
  files (such as image, sidecar, gradients, and b-value files) have plausible
  matching identifiers and counts.

### DICOM series completeness

For per-frame inventory and slice-position checks, read
[`references/dicom-series-audit.md`](references/dicom-series-audit.md) before
writing the audit. It describes the metadata to compare without prescribing an
unavailable DICOM parser.

- Group by Study Instance UID and Series Instance UID; do not combine distinct
  series merely because their descriptions match. Check consistent patient/study
  identifiers where appropriate, modality, rows/columns, pixel spacing,
  orientation, frame of reference, and relevant acquisition parameters.
- Detect duplicate SOP Instance UIDs, repeated instance numbers, missing or
  non-monotonic instance numbers, inconsistent slice orientation, and gaps in
  ImagePositionPatient. For enhanced multi-frame DICOM, inspect per-frame
  functional groups; a single file may contain many slices.
- Infer missing slices only when ordering and expected spacing/count are
  trustworthy. Account for localizers, interleaved acquisitions, variable
  spacing, gantry tilt, and multiframe objects. Report suspected gaps with the
  evidence and uncertainty; do not fabricate expected slice counts.

### NIfTI and derived-volume checks

When using FSL for NIfTI checks, read
[`references/fsl-nifti-audit.md`](references/fsl-nifti-audit.md) before
writing the batch script. It documents the relevant commands, statistic field
order, and safe handling of parser failures.

- Confirm files decompress and parse; inspect dimensionality, datatype, finite
  voxel values, qform/sform codes and affines, voxel sizes, orientation, and
  plausible coverage. Compare expected dimensions and geometry across modalities.
- Check for empty volumes, all-zero data, extreme non-finite values, obvious
  truncation, and implausible slice spacing or field of view. For masks, check
  label values and whether the mask grid matches its stated reference.
- When using FSL `fslstats`, parse its requested statistics as whitespace-
  separated fields in the documented option order; multiple requested values
  are normally emitted on one line. Do not assume one statistic per line. If
  output parsing is unexpected or a required value is absent, mark that check
  NOT CHECKED or WARNING and retain the raw output; do not report an image as
  empty because a parser failed.
- A structurally valid NIfTI does not reveal whether source DICOM slices were
  omitted before conversion. Verify conversion logs, source-to-output counts,
  and geometry against the original series or a trusted manifest when possible.

## 3. Report the outcome and next action

Write a concise audit with one status for each relevant check: PASS, FAIL,
WARNING, or NOT CHECKED. Include evidence (counts, hashes or mismatch paths,
UIDs where safe, dimensions, spacing, affine comparison), the expected source,
tools and versions, and limitations.

When the request asks whether a dataset or series is complete, also give an
overall status that reflects completeness. Do not let a PASS for one internal
consistency check stand in for an overall PASS. If no independent expected
inventory, count, or source comparison exists for a material completeness
question, the overall status is WARNING even when file-level checks pass. You
may report that individual check as PASS while keeping overall completeness
WARNING or NOT CHECKED.

For enhanced multi-frame DICOM, `files = 1`, `SOP instances = 1`, and a plausible
frame count can PASS the packaging/count-consistency check. If no expected frame
count or source inventory is available, the overall completeness status remains
WARNING; present per-frame positions alone do not prove that all expected
frames were transferred.

- **PASS:** required checks agree with an independent inventory or source of
  truth. State any checks that were unavailable.
- **WARNING:** data are internally plausible, but no independent source proves
  completeness, or an ambiguity needs review. Continue only if the downstream
  task can tolerate the named uncertainty, and pass the audit note forward.
- **FAIL:** corruption, missing expected files/instances, duplicate identifiers,
  irreconcilable metadata, or unusable geometry. Stop dependent analysis until
  the source is corrected or the user explicitly chooses a documented
  workaround.

Never “fix” a failed integrity check by changing metadata, dropping unexpected
files, interpolating missing slices, or relabeling a modality. Preserve the
original evidence. If a repair or re-download is requested, retain the original,
record the action and provenance, then rerun the affected checks on the repaired
copy.

## 4. State the limits

- Without a trusted expected inventory, checksum, or source-series comparison,
  completeness is not proven.
- Missing DICOM slices cannot always be inferred from instance numbers alone;
  geometry, acquisition type, multiframe structure, and localizers matter.
- Metadata can be self-consistent and still be wrong. Compare independent
  sources and image content, and describe unresolved conflicts.
- Integrity checks establish file and metadata properties, not diagnosis,
  segmentation accuracy, or clinical acceptability.

## Constraints

- Keep the audit read-only. Never repair metadata, drop files, infer missing
  slices, or overwrite source data.
- Run all commands that read input data inside a retained script submitted to
  SLURM, with the exact parser/tool module version pinned.
- Do not download replacement data or claim completeness without an independent
  inventory, checksum, or source-series comparison.
- Report unresolved uncertainty; integrity checks do not diagnose image
  content or establish clinical validity.
