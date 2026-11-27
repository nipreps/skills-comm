---
name: acute-stroke-segmentation
description: >
  Segment a confirmed acute ischaemic stroke or acute infarct from diffusion
  MRI and publish a publication-gated lesion mask. Invoke for "segment the
  acute infarct", "acute stroke mask", or an established acute ischaemic stroke.
  A generic segmentation request may route here only after lesion-identification
  marks it eligible. Do not use for chronic stroke, WMH, MS, haemorrhage, tumour,
  or an unresolved lesion type.
---

# Acute ischaemic stroke segmentation

This skill supplies task knowledge and the execution contract. Select a
compatible documented method based on its evidence, inputs, and availability.

## 1. Check the imaging evidence

Acute ischaemic tissue is supported by spatially concordant high DWI signal and
low ADC. DWI brightness without ADC reduction may be T2 shine-through. FLAIR
can be normal early and becomes hyperintense later; it is supportive rather
than required for defining restricted diffusion.

Expect a focal or territorial pattern, commonly unilateral. Check for motion,
distortion, susceptibility, low-signal ADC artifacts, and lesions outside
brain. Do not convert these observations into a hand-thresholded deliverable.

## 2. Establish the input and output contract

Keep discovery within the supplied case, this task's output workspace, the
relevant skill references, and the documented module catalog. Do not search the
filesystem root, unrelated home directories, system or historic Slurm logs,
other datasets, or unrelated datasets. If a required tool or provenance
file is unavailable in that scope, report the limitation.

On Neurodesk, do not read or compute from image files in the interactive shell.
This includes preliminary integrity checks, header reads, voxel summaries, and
debugging retries. Put those operations and segmentation in the retained,
version-pinned Slurm script below; only resource/module discovery that does not
open input images may happen before submission. Reuse a current integrity audit
when the inputs are unchanged.

Require 3D DWI and ADC; accept FLAIR when available. Reuse a current
`data-integrity` report when one exists; invoke that skill only when no current
report exists, files changed since its audit, or a specific integrity concern
arises. Verify modality identity against filenames, metadata, headers,
and image content; inspect shape, affine, voxel sizes, dtype, finite values,
coverage, and DWI/ADC grid compatibility. Report unresolved metadata conflicts
or evidence of incomplete/corrupt input and stop segmentation until resolved.
Use the output grid named by the request, normally DWI. Preserve any existing
final output unless replacement was explicitly requested.

## 3. Select a compatible documented tool

Use the available modalities and task constraints to identify plausible
methods, then read only those method references. Read another candidate
reference only when it could change the choice. Do not load unrelated tool
references or other skills' QC and extraction references during initial
selection. Compare documented compatibility, GPU/CPU availability, live Slurm
capacity, expected runtime, and output grid. The references do not rank tools.
Record the reason for the selected compatible tool in one line.

Run and retain these discovery probes before writing Slurm directives:

```bash
mkdir -p logs/tool-probes
nvidia-smi >logs/tool-probes/00_nvidia-smi.log 2>&1 || true
{
  sinfo -h -o 'partition=%P state=%a time=%l cpus=%c memory_mb=%m gres=%G'
  sinfo -N -h -o 'node=%N state=%T cpus=%c memory_mb=%m gres=%G'
  scontrol show partition
} >logs/tool-probes/00_slurm_resources.log 2>&1
```

Use only a reference-documented method whose availability probe succeeds.
Record probe failure and consider another documented compatible tool. Exhausting
the documented tools is a reportable failure; intensity thresholding, nonzero
input masks, and handwritten morphology are not substitutes.

Select autonomously using modality fit, validation evidence, actual
availability, and the requested output grid. Record the rationale and continue
without asking the user. If no compatible method is available, report the
failure and stop.

Copy the selected reference's validated invocation and pinned module exactly.
Do not substitute a merely available version, add flags from memory, or tune a
candidate until the publisher accepts it.

## 4. Execute and publish

Put substantive work in a retained `src/analysis_<step>_acute_stroke.sh`, pin
the documented module, use a job-specific attempt directory, and submit through
Slurm with resources fitting the live report. Require a captured job ID,
`sacct` `COMPLETED` with `ExitCode 0:0`, inspected logs, and the exact documented
candidate filename.

Resolve this skill's installed directory before writing the script and store
its absolute path in `SKILL_DIR`. Resolve `HELPER_PYTHON` with
`command -v python3` before loading the neuroimaging module when using bundled
helpers; do not rely on agent environment variables being passed to Slurm.

Submit one job per selected method. Capture `JOB_ID=$(sbatch --parsable
<script>)`, monitor that ID with `squeue -j "${JOB_ID}"`, and inspect it with
`sacct -j "${JOB_ID}"`. Never run `sbatch --wait "${JOB_ID}"` (sbatch treats
the ID as a script path). If a job fails, inspect its logs and resubmit only
after correcting a demonstrated cause, using a new attempt directory.

Resolve the skill directory in the retained Slurm script; `SKILL_DIR` is not an
automatically defined shell variable:

```bash
SKILL_DIR="/absolute/path/to/acute-stroke-segmentation" # Replace with the installed path before submission.
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/publish_mask.py"
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
```

Some documented tools preserve physical DWI space but reorient the voxel axes.
When their reference says so, restore the requested raw DWI grid with the
bundled nearest-neighbour helper before publication:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/resample_mask.py" \
  --candidate "${CANDIDATE_MASK}" --reference "${REFERENCE_INPUT}" \
  --output "${ATTEMPT_DIR}/lesion_on_requested_grid.nii.gz"
CANDIDATE_MASK="${ATTEMPT_DIR}/lesion_on_requested_grid.nii.gz"
```

This is grid mapping, not registration. Use it only when the tool output and
reference are declared to represent the same physical image or are linked by a
validated transform. Publish only with the bundled script:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/publish_mask.py" \
  --kind lesion --candidate "${CANDIDATE_MASK}" \
  --reference "${REFERENCE_INPUT}" --output "${FINAL_MASK}"
```

The mask must be binary, non-empty, exactly on the reference grid, and 0.5–500
cm3. Internal holes and multiple components are recorded for QC rather than
rejected automatically. Publication writes exact `uint8` `{0,1}`, copies the
reference affine/header, clears scaling, verifies the stored file, and renames
atomically.
The publisher refuses an existing output by default. Do not pass `--replace`
unless replacement was explicitly authorized and the old output was preserved.

The 0.5 cm3 floor is a plausibility guard, not a clinical threshold. A small
acute lacunar infarct can fall below it and be refused as implausible. If the
candidate is genuinely a sub-0.5 cm3 lesion and the diffusion signature supports
it, that is a reportable limit of this contract — raise it rather than inflating
the mask to clear the gate.

Invoke `lesion-segmentation-qc` after publication. Cross-check spatial overlap
with restricted diffusion, brain containment, laterality, cluster pattern, and
volume; inspect the rendered overlay before making a quality claim. Hand off
the output-grid anatomical, exact-grid DWI/ADC, and any validated exact-grid
brain mask. Let QC delegate a missing brain mask to `brain-extraction`; do not
improvise an extractor command in this skill.

Report three outcomes separately: whether the tool completed and the mask was
published, whether numeric QC passed, and whether boundary accuracy and
completeness were visually reviewed or compared with an independent reference.
A published mask with passing numeric checks is not by itself a validated
segmentation. If QC fails, is Borderline, or is incomplete, retain the report,
mark the mask as not approved for downstream use, and state the unverified
criteria. Do not describe it as fully validated without boundary review or an
independent reference comparison.

## Constraints

- Invoke only when acute stroke is stated in the task, or a generic requested
  mask is handed off with `segmentation_eligible: true` by
  `lesion-identification`. Do not use for chronic stroke, WMH, haemorrhage,
  tumour, or unresolved lesion type.
- The publisher's 0.5–500 cm3 volume interval is a software contract, not a
  clinical range. Report candidates outside it without inflating or clipping
  the mask.
- Run image reads and neuroimaging tools inside the retained, pinned SLURM
  script. Never use hand-thresholded masks as a substitute.
- Preserve existing outputs unless replacement was explicitly authorized. Do
  not claim full validation when boundary review or an independent reference
  comparison is absent.
