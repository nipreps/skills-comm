---
name: wmh-segmentation
description: >
  Segment confirmed cerebral white matter hyperintensity or small-vessel
  disease burden from coregistered structural MRI and publish a publication-gated
  WMH mask. Invoke for "segment the WMH", "WMH mask", or established WMH. A
  generic segmentation request may route here only after lesion-identification
  marks it eligible. Do not use for MS, stroke, haemorrhage, tumour, or an
  unresolved lesion type.
---

# White matter hyperintensity segmentation

This skill supplies task knowledge and the execution contract. DeepWMH is the
default for compatible structural MRI; prefer a method developed for
vascular/age-related WMH over an MS-trained transfer model.

## 1. Check the imaging evidence

WMH are FLAIR-hyperintense lesions in cerebral white matter, commonly bilateral
and distributed in periventricular and deep regions. Record punctate, early
confluent, and confluent patterns without treating normal ventricular CSF,
cortical lesions, infarct cavities, or image artifacts as burden.

MS can also be multifocal and periventricular. Ovoid lesions perpendicular to
the ventricles, juxtacortical or infratentorial involvement, and relevant
clinical context require confirmation rather than automatic WMH routing.

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

Require a 3D FLAIR and accept/require a coregistered T1w according to the chosen
documented tool. Reuse a current `data-integrity` report when one exists; invoke
that skill only when no current report exists, files changed since its audit,
or a specific integrity concern arises. Verify modality identity against
filenames, metadata, headers, and image content; inspect shape,
affine, voxel size, dtype, finite values, coverage, and cross-modal alignment.
Report unresolved metadata conflicts or evidence of incomplete/corrupt input
and stop segmentation until resolved. The requested output normally follows the
FLAIR grid.

## 3. Select a compatible documented tool

Use the supplied modalities and task constraints to identify plausible
vascular-WMH methods, then read only those method references. Read a second
candidate reference only when it could change the choice. Do not load unrelated
tool references or other skills' QC and extraction references during initial
selection. Compare documented pathology fit, modality requirements,
availability, live Slurm capacity, runtime, output label/file, validation
population, and output grid. When `deepwmh/1.0.1` is available, use it as the default:
it is a direct FLAIR-only WMH method with a validated Neurodesk invocation and
supporting evaluation evidence. Read its reference, check that module and
invocation, and proceed without comparing every alternative. Read another
vascular-WMH reference only if DeepWMH is unavailable, incompatible with the
input or output contract, or completes with failed/borderline QC. In an
unattended request, choose autonomously, record the choice and trade-off in
one line, and continue without asking the user. If no compatible
documented method is available, report that and stop.

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
Exhausting documented tools is a reportable failure; intensity thresholding,
nonzero-input masks, and handwritten morphology are not substitutes for a
confirmed WMH task.

If a DeepWMH candidate has failed or Borderline lesion QC, run the next
compatible documented vascular-WMH method as a separate candidate in a new
job-specific attempt directory. Retain both candidates and reports; never
overwrite one with the other. Compare their numeric and visual evidence. Keep
the original final path unchanged; if the alternate is better supported, write
it to a distinct final path and identify both outputs in the report. Report if
neither candidate is adequate. A failed, Borderline, or incomplete QC report
means the associated mask is not approved for downstream use.

Treat MS-trained tools as second-line experimental transfer methods, not the
first choice. Do not read their references during primary vascular-WMH tool
selection. Consider one only after a vascular-WMH method has completed but
failed or remained Borderline on lesion QC, or after every compatible
vascular-WMH method is unavailable. Do not launch this out-of-domain fallback
automatically; preserve the first candidate and its QC, report why a vascular
method failed or was unavailable, and state that no fallback was run. Use an
experimental fallback only when the task explicitly authorizes it, document
the domain shift, and never tune it against a case reference or silently
replace an already published mask. Never present its output as evidence of MS
or another aetiology.

Copy the selected reference's validated invocation and pinned module exactly.
Do not substitute another available version or invent an operating point.

## 4. Execute and publish

Put substantive work in a retained `src/analysis_<step>_wmh.sh`, pin the
documented module, use a job-specific attempt directory, and submit through
Slurm with resources fitting the live report. Require a captured job ID,
`sacct` `COMPLETED` with `ExitCode 0:0`, inspected logs, and the exact documented
candidate label/file.

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
SKILL_DIR="/absolute/path/to/wmh-segmentation" # Replace with the installed path before submission.
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/publish_mask.py"
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
```

When a documented candidate differs from the requested FLAIR grid only because
of tool reorientation or header rounding, map it with the bundled
nearest-neighbour helper before publication:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/resample_mask.py" \
  --candidate "${CANDIDATE_MASK}" --reference "${FLAIR}" \
  --output "${ATTEMPT_DIR}/wmh_on_flair_grid.nii.gz"
CANDIDATE_MASK="${ATTEMPT_DIR}/wmh_on_flair_grid.nii.gz"
```

This helper is not registration. Stop if the inputs lack a declared valid
spatial relationship or if its volume-preservation gate fails. Publish only
with:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/publish_mask.py" \
  --kind lesion --candidate "${CANDIDATE_MASK}" \
  --reference "${FLAIR}" --output "${FINAL_MASK}"
```

The mask must be binary, non-empty, exactly on the reference grid, and 0.5–500
cm3. Internal holes and multiple components are recorded for QC rather than
rejected. Publication writes exact `uint8` `{0,1}`, copies the reference
affine/header, clears scaling, verifies the stored file, and renames atomically.
The publisher refuses an existing output by default. Do not pass `--replace`
unless replacement was explicitly authorized and the old output was preserved.

Invoke `lesion-segmentation-qc` after publication. Inspect FLAIR signal
correspondence, periventricular/deep distribution, brain containment, lesion
clusters, volume, and the rendered overlay before making a quality claim. Hand
off the output-grid FLAIR and a validated exact-grid brain mask. If none exists,
QC must delegate to `brain-extraction` with `REFERENCE_GRID` set to the FLAIR;
do not improvise an extractor command in this skill. Do not call the QC complete
while containment remains UNVERIFIED when an output-grid anatomical is present.
For WMH, treat component counts and largest-component share as descriptive:
confluent periventricular disease can legitimately form one dominant component.
Numeric QC cannot establish completeness, so retain the overlay and require a
human completeness/boundary review or reference-mask comparison before calling
the segmentation validated.

## Constraints

- Invoke only when WMH is stated in the task, or a generic requested mask is
  handed off with `segmentation_eligible: true` by `lesion-identification`.
  Do not use for MS, stroke, haemorrhage, tumour, or unresolved lesion type.
- Run image reads and neuroimaging tools inside the retained, pinned SLURM
  script. Do not use hand-thresholding or handwritten morphology as a
  substitute for a documented WMH method.
- Preserve existing outputs unless replacement was explicitly authorized and
  report known small-lesion and modality limitations.
- The publisher's 0.5–500 cm3 volume interval is a software contract, not a
  clinical range. Report candidates outside it without inflating or clipping
  the mask.
