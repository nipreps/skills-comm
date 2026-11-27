---
name: brain-extraction-qc
description: >
  Validate brain extraction / skull stripping results, with or without image
  vision. Computes a quantitative metric battery (volume, left-right mirror
  symmetry, mask centring, topology, scalp inclusion, boundary tightness),
  renders an AFNI @chauffeur_afni outline PNG, writes a structured QC report,
  and saves a paired human verification form. Invoke after brain extraction
  completes, or standalone on any existing brain mask with "check brain
  extraction", "QC the mask", "validate skull strip", "review brain
  extraction", "evaluate the mask", or "brain-extraction-qc". Also invoke when
  the user references a file ending in `_brain.nii.gz`, `_mask.nii.gz`, or
  `_brain_mask.nii.gz` and asks to check, review, or validate it.
metadata:
  short-description: QC a brain mask (numeric battery + outline PNG)
---

# Skill: brain-extraction-qc

Validate a brain mask on measured evidence, then look at it if you can.

Almost everything a human checks in a skull-strip QC image has a numeric
signature: whether the mask is centred, whether it covers both hemispheres
evenly, whether it swallows scalp, whether it is riddled with holes, whether it
is bloated into CSF. `scripts/qc_metrics.py` measures those directly. This
matters because a QC image is worthless to a model that cannot open it, and a
report written from filenames and hope is worse than no report at all.

One thing genuinely resists measurement: **dura and superior sagittal sinus
inclusion**. Dura is thin, its T1 intensity overlaps cortex, and it sits exactly
where a correct boundary also sits. Report it as UNVERIFIED rather than guessing.

## Workflow

1. Identify the anatomical image and brain mask.
2. Run the numeric battery and save `metrics.json`.
3. Render the AFNI outline PNG for human review.
4. Render the mosaic PNG when it adds context.
5. If image vision is available, inspect the outline and reconcile it with the
   numbers; otherwise mark dura inclusion UNVERIFIED.
6. Write the AI report and blank human verification form.
7. Summarise the numeric verdict and unresolved visual checks.

### 1. Identify inputs

Use the original anatomical NIfTI, the brain mask NIfTI, and any supplied
output prefix and tool name. If a required file is missing, report the exact
missing input and stop without requesting it from the user.

```bash
ls "<anat>" "<mask>"
```

Stop and report if either is missing. Infer the tool name from the path when you
can (`derivatives/synthstrip_*/...` → `synthstrip`); fall back to `unknown-tool`.

Create the run timestamp inside the retained Slurm script, not in the
interactive submission shell. Save it under the Slurm job ID so the report and
human form can reuse the exact same value after the job completes.

### 2. Run the numeric battery

Before loading the imaging module, set `SKILL_DIR` to this skill's resolved
installed directory and resolve the host Python interpreter. Do not rely on
agent environment variables being passed to Slurm. Verify required imports
inside the retained SLURM script. Keep all image reads and metrics in that job.

```bash
# Resolve the skill directory and host interpreter before module wrappers can
# change PATH.
SKILL_DIR="/absolute/path/to/brain-extraction-qc" # Replace with the installed path before submission.
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/qc_metrics.py"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p qc logs
printf '%s\n' "${TIMESTAMP}" | tee "logs/qc_timestamp_${SLURM_JOB_ID}.txt"
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
"${HELPER_PYTHON}" -c "import numpy, nibabel, scipy, matplotlib, PIL"
export HELPER_PYTHON

"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/qc_metrics.py" "<anat>" "<mask>" \
  --label "<prefix>_<tool>" \
  --json "qc/<prefix>_<tool>_${TIMESTAMP}_metrics.json"
```

Use the same Slurm script for the metrics, AFNI outline, and optional mosaic
steps so each artifact uses this timestamp.

The anatomical image and brain mask are positional arguments in that order.
This script does not accept lesion QC's `--brain-mask` option and does not use a
generic `--mask` flag. Run the bundled script with `--help` rather
than transferring flags between the two QC skills.

Requires the pinned `numpy`, `nibabel`, and `scipy` versions from
`${SKILL_DIR}/../python-requirements.txt`. Resolve
`HELPER_PYTHON` with `command -v python3` before loading the imaging module,
then check the imports in the SLURM script. If a dependency is missing, report
the environment limitation; do not install packages during the QC run.

It prints a metric table, a per-criterion PASS/BORDERLINE/FAIL roll-up, and a
`NUMERIC VERDICT`, and writes the same as JSON. Read
`references/numeric-criteria.md` for what each metric means, where the
thresholds came from, and which failure each one is good and bad at catching —
you need that to interpret a result rather than just transcribe it.
Read `references/qc-generation.md` for the bundled script and output contract.

Two habits worth keeping: quote the actual numbers in your report, and treat
`--vol-range` as adjustable. The 900–1900 cm³ default is adult T1w; paediatric,
neonatal or rodent data needs a different range, and a volume flag against the
wrong range is noise.

For an image in a Nipoppy dataset, read
`references/qcstudio-integration.md` when an additional human-facing QC Studio
view is useful. Keep the structured report and verification form as the
portable QC record.

### 3. Render the AFNI outline PNG

Always produce this, even with no vision — the human reviewer needs it, and it
is the artefact the human form is filled in against.

Before writing the job script, confirm the tested AFNI version rather than
assuming that every version listed by the module system is runnable:

```bash
module spider afni     # or: module -t avail afni
module spider afni/26.0.07
```

In the retained `analysis_<N>_<description>.sh` job, resolve the host Python
before loading AFNI, export it for the helper, then load the pinned module.
The bundled script is parameterised, so run it directly instead of editing a
copy. Do not run the rendering step on the login node.

```bash
export HELPER_PYTHON
module load afni/26.0.07
bash "${SKILL_DIR}/scripts/afni_outline_qc.sh" \
  -a "<anat>" \
  -m "<mask>" \
  -o "qc/<prefix>_<tool>_${TIMESTAMP}_afni_outline_qc.png"
```

The calling job pins `afni/26.0.07`; the helper checks for the loaded
`@chauffeur_afni` executable and exposes no version-override flag. Do not edit
the script or add a guessed `-v` option merely because an older version appears
in `module spider`; Neurodesk can retain module entries
for containers later disabled for a security or runtime defect. If 26.0.07 is
unavailable, stop and report the outline dependency rather than guessing a
replacement.

An outline beats a filled overlay here: a translucent blob looks equally fine
whether its edge is on the pial surface or four millimetres out in the dura,
which is precisely the distinction being checked. The script crops to the mask
bounding box first so montage panels are not wasted on empty air, and converts
2dcat's output to real PNG — some AFNI builds cannot write PNG and quietly emit
`.ppm` instead, which most viewers and vision models will not open.

Verify it landed: `ls -lh "<outline_png>"`. If it is missing, say so; the numeric
QC still stands on its own, but the human review step is blocked.

### 4. Render the mosaic PNG (optional)

Supporting context for a human — filled mask plus cyan contour, three planes.

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/qc_mosaic.py" "<anat>" "<mask>" \
  "qc/<prefix>_<tool>_${TIMESTAMP}_qc.png"
```

### 5. Visual review — only if you can actually see images

**If you have image-viewing capability:** open the outline PNG at high detail
and read `references/ai-evaluation-criteria.md` for the visual rubric. Check
each plane. Then reconcile what you see with the numbers.

When vision and metrics disagree, neither automatically wins — say which you
trusted and why. Vision is better at dura, vessels, focal pathology and
anything where anatomy explains an odd number. Metrics are better at small
consistent biases, subtle centring errors, and anything requiring counting.
A documented disagreement is a useful QC result; a silently overridden one is not.

**If you cannot open images:** say so plainly and write the report from the
metrics. Do not fill visual criteria from filenames, logs, memory, or the fact
that a file exists. Rate every numerically-testable criterion, mark dura
UNVERIFIED, cap confidence at Medium, and record `Evidence basis: numeric-only`.
This is a complete numeric QC report. Visual boundary review remains pending
for criteria the numeric battery cannot assess, including dura.

### 6. Write the reports

Save the AI report to `qc/<prefix>_<tool>_<timestamp>_ai_eval.md` using the
template in `references/report-template.md`, then write a blank human form from
`references/human-verification-form.md` to
`qc/<prefix>_<tool>_<timestamp>_human_eval.md`.

The criterion labels must match word-for-word across the numeric output, the AI
report and the human form. Agreement between AI and human ratings is scored on
those labels later, and a renamed criterion silently drops out of that analysis.

Verify both exist and are non-empty before reporting done:

```bash
TIMESTAMP="$(cat "logs/qc_timestamp_${JOB_ID}.txt")"
test -s "qc/<prefix>_<tool>_${TIMESTAMP}_ai_eval.md" \
  && test -s "qc/<prefix>_<tool>_${TIMESTAMP}_human_eval.md"
```

Leave the human form blank and report that human verification remains pending.
Provide the form and outline paths without soliciting a response.

### 7. Summarise

Report the verdict and confidence, the evidence basis (numeric-only or
numeric+visual), paths to every artefact, each Borderline/Fail criterion with
the number that drove it and a specific recommended action, and the standing
dura caveat.

## Interpreting the verdict

The script fails the whole mask on any single failing criterion. That is
deliberate — each criterion maps to a defect that propagates into registration,
segmentation or volumetry, so "fails one but is otherwise fine" is not a
meaningful state. You may overturn it, but only in writing and only with a
concrete reason.

The reason that matters most in practice is **real anatomy**. Stroke,
resection, mass effect, focal atrophy, large ventricles and a partial field of
view all produce genuine asymmetry, and a mask that correctly follows an
asymmetric brain is a good mask. The metrics cannot tell that apart from a
lateralised extraction failure; you often can, from the clinical context, the
referring request, or the image itself. When you overturn a rating on those
grounds, name the anatomy and say what evidence you used.

The reverse error is worse and more common: waving through a bad mask because
the numbers were not quite over a threshold. Thresholds are conservative
defaults calibrated on adult 1mm T1w data, not physical constants.

## Constraints

- Never write a criterion rating you did not measure or see. Numeric ratings
  come from the script; visual ratings require actually opening the image.
- Always produce the outline PNG, even with no vision — it is what the human
  reviewer signs off against.
- Keep the AFNI step in a numbered `analysis_<N>_*.sh` script with a pinned
  `module load afni/<version>`, per the project's execution rules.
- Report dura / superior sagittal sinus inclusion as UNVERIFIED on any run
  without visual inspection. Do not infer it from boundary metrics.
- Cap confidence at Medium for numeric-only runs, and state the evidence basis
  explicitly in the report.
- Quote actual metric values in the report, not just ratings — the numbers are
  what make the assessment checkable by someone else later.
- Save the metrics JSON alongside the reports; it is the reproducible record of
  what was measured.
- If metrics and vision disagree, state the disagreement and which you trusted.
  Do not silently drop either.
