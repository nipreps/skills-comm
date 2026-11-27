---
name: chronic-stroke-segmentation
description: >
  Segment a confirmed chronic stroke, old infarct, or encephalomalacic stroke
  cavity from structural brain MRI and publish a publication-gated lesion mask.
  Invoke for "segment the old infarct", "chronic stroke mask", or an established
  chronic stroke. A generic segmentation request may route here only after
  lesion-identification marks it eligible. Do not use for acute stroke, WMH,
  MS, haemorrhage, tumour, or an unresolved lesion type.
---

# Chronic stroke segmentation

This skill supplies task knowledge and the execution contract. SynthStroke is
the default for compatible T1w input; LINDA is a documented fallback.

## 1. Check the imaging evidence

Chronic infarction typically appears as tissue loss or a CSF-like cavity with
surrounding gliosis, volume loss, widened sulci, and possible ex-vacuo
ventricular enlargement. On T1 it is usually hypointense; T2/FLAIR can show a
bright gliotic rim while a mature cavity approaches CSF signal. Confirm that
the pattern is not restricted diffusion, an old haemorrhagic cavity, tumour,
normal ventricle, or an isolated WMH focus.

Chronic lesions can be large, irregular, disconnected, and internally
cavitated. Those properties are not by themselves segmentation failures.
Restricted diffusion is not expected in a mature cavity, but its absence does
not establish chronic stroke; age of lesion and diagnosis must come from the
confirmed task and clinical context. A small lacune may be below a tool's
reliable detection limit.

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

Require a 3D T1w image and accept coregistered T2w/FLAIR when available. Reuse a
current `data-integrity` report when one exists; invoke that skill only when no
current report exists, files changed since its audit, or a specific integrity
concern arises. Verify modality identity against filenames, metadata, headers,
and image content; check shape, affine, voxel size, dtype, finite values, and
cross-modal alignment. Stop on corruption, unresolved modality identity, or
unexplained geometry mismatch. Establish the requested output grid explicitly;
a structural tool may produce a T1-grid candidate even when the requested
deliverable is on T2w. Equal array dimensions alone do not establish alignment.

## 3. Select a compatible documented tool

Use `synthstroke/0.0.0` as the default when it is available and the T1w input is
compatible. Read its reference and check that module first; read the LINDA
reference only if SynthStroke is unavailable or incompatible. Record the
selected tool and rationale in one line; do not pause for a user choice. If
SynthStroke is unavailable or incompatible, consider the documented LINDA
method. If neither is compatible, report that limitation and stop without
asking the user to rescue the run. Treat small lesions cautiously and report
the tool's known limitations from its reference.

Apply this as a short decision gate: inspect the SynthStroke reference and probe
`synthstroke/0.0.0` first. If both succeed and the input is T1w, select
SynthStroke and stop comparing methods. Do not read the LINDA reference or
inspect fallback commands unless that gate fails. Do not search or grep across
all installed skills or their references to infer commands; use this skill's
selected method reference and load only the specific handoff skill when needed.

If a SynthStroke candidate fails or remains Borderline in lesion QC,
run LINDA only as a separate comparison candidate in a new attempt directory.
Retain both candidates and reports, never overwrite the first output, and use a
distinct output path for any alternate publication. Report if neither candidate
is adequate. A failed, Borderline, or incomplete QC report means the associated
mask is not approved for downstream use.

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
the documented tools is a reportable failure; intensity thresholding,
probability retuning, nonzero-input masks, and handwritten morphology are not
substitutes.

Once the selected method and required inputs are known, stop environment
exploration and write the analysis script. Do not scan unrelated directories,
skills, or historical logs.

Copy the selected reference's validated invocation and pinned module exactly.
Do not infer output locations from conventional `--outdir` behaviour; wrappers
may have verified non-standard placement documented in their reference.

## 4. Execute and publish

Put substantive work in a retained `src/analysis_<step>_chronic_stroke.sh`, pin
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

Resolve the skill directory inside the retained Slurm script; it is not an
automatically defined shell variable:

```bash
SKILL_DIR="/absolute/path/to/chronic-stroke-segmentation" # Replace with the installed path before submission.
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/publish_mask.py"
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
```

When a documented candidate differs from the requested grid, use the bundled
nearest-neighbour helper only when the candidate and reference have a known
valid physical relationship (same acquisition space or a documented validated
transform). This helper maps grids; it does not register images. Do not
improvise an affine transform:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/resample_mask.py" \
  --candidate "${CANDIDATE_MASK}" --reference "${REFERENCE_INPUT}" \
  --output "${ATTEMPT_DIR}/candidate_on_reference_grid.nii.gz"
CANDIDATE_MASK="${ATTEMPT_DIR}/candidate_on_reference_grid.nii.gz"
```

Then publish only with:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/publish_mask.py" \
  --kind lesion --candidate "${CANDIDATE_MASK}" \
  --reference "${REFERENCE_INPUT}" --output "${FINAL_MASK}"
```

The mask must be binary, non-empty, exactly on the reference grid, and 0.5–500
cm3. This is a software plausibility gate, not a clinical size range; small
lacunar infarcts can fall below the 0.5 cm3 floor. If supported evidence points
to a genuinely smaller lesion, report that the publisher cannot accept it and
do not enlarge the mask to pass. Internal holes and multiple components are
recorded for QC rather than rejected. Publication writes exact `uint8` `{0,1}`,
copies the reference affine/header, clears scaling, verifies the stored file,
and renames atomically. The publisher refuses an existing output by default.
Do not pass `--replace` unless replacement was explicitly authorized and the
old output was preserved.

Invoke `lesion-segmentation-qc` after publication. Inspect brain containment,
laterality, cavity/gliosis correspondence, cluster pattern, volume, and the
rendered overlay before making a quality claim. Hand off the output-grid
anatomical, a T1w only when it is on that grid, and any validated exact-grid
brain mask. Let QC delegate a missing brain mask to `brain-extraction`; do not
improvise an extractor command in this skill.

## Constraints

- Invoke only when chronic stroke is stated in the task, or a generic requested
  mask is handed off with `segmentation_eligible: true` by
  `lesion-identification`. Do not use for acute stroke, WMH, haemorrhage,
  tumour, or unresolved lesion type.
- Run image reads and neuroimaging tools inside the retained, pinned SLURM
  script. Never create a mask by thresholding or editing the source image.
- Preserve existing outputs unless replacement was explicitly authorized, and
  report unresolved lesion-size or modality limitations.
- The publisher's 0.5–500 cm3 volume interval is a software contract, not a
  clinical range. Report candidates outside it without inflating or clipping
  the mask.
