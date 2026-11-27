---
name: lesion-identification
description: >
  Identify an unspecified or ambiguous brain-lesion type using sequence
  inventory, quantitative signatures, and visual review when available. Invoke
  for "what kind of lesion is this", "is this acute or chronic", "identify the
  lesion". The generic lesion-segmentation router invokes this skill before
  pathology-specific segmentation when lesion type is not established. Do not
  invoke merely to reconfirm an explicitly stated acute stroke, chronic stroke,
  or WMH task.
metadata:
  short-description: Identify lesion type before segmenting
---

# Skill: lesion-identification

Decide what you are looking at before handing it to a pathology-specific
segmentation skill. A method applied to the wrong pathology can return a
confident, plausible, wrong mask that downstream checks may not detect.

This step is where a vision-capable model has a real advantage, so the skill
uses vision when it exists. It also has to work without it, because a text-only
model that guesses lesion type from a filename is the worst case of all. The
bypass is measurement: lesion types differ in ways that are quantifiable, not
merely visible.

| Lesion type | Measurable signature |
|---|---|
| Acute ischaemic stroke | restricted diffusion — DWI bright **and** ADC dark; usually one focal unilateral lesion |
| Chronic stroke | CSF-like cavity on T1, unilateral, no mirror counterpart, often with ex-vacuo ventricular asymmetry |
| WMH | FLAIR-bright, bilateral and roughly symmetric, many small foci hugging the ventricles |

## Workflow

```
1. Inventory the sequences            -> what questions the data can answer
2. Run the signature probe            -> ranked hypotheses + evidence
3. If you have vision: review the images and reconcile
   If you do not:      report the probe's ranking as a hypothesis
4. Report the proposed type and uncertainty
5. For a generic segmentation request, hand off only when the evidence meets
   the eligibility rule below; otherwise report uncertainty and make no mask
```

### 1. Inventory the sequences

Which sequences exist constrains what can be concluded, often more sharply than
the images do. Establish this first, including whether each file is a usable
3D image rather than trusting its suffix. Reuse a current `data-integrity`
report when one exists. Before probing, check that the report covers these exact
files. If no current report exists, the files changed, or a corruption or
completeness concern remains, invoke the `data-integrity` skill and save its
report before continuing. Do not treat a sequence/header inventory as a
substitute for that audit. When there is no independent expected inventory or
checksum, state that completeness cannot be proven. An integrity pass does not
establish that images are correctly labelled or clinically interpretable.

In Neurodesk, put voxel-wise probe and image-rendering commands in named,
version-pinned `analysis_<step>_<description>.sh` scripts and submit them to
Slurm. The probe is Python-based, but “runs anywhere Python does” is not
permission to run it interactively on a Neurodesk login node.

```bash
ls *.nii.gz            # or: find <bids_dir> -name '*.nii.gz'
```

Read BIDS suffixes (`_T1w`, `_FLAIR`, `_dwi`, `_T2w`, `_swi`) and JSON sidecars
for relevant acquisition metadata. Cross-check names against headers, value
ranges, units, and acquisition metadata. If naming is non-standard or metadata
conflicts, report the ambiguity and lower confidence; do not infer that an ADC
map is DWI (or vice versa) from filename alone. Never alter metadata to make
an expected signature appear. Continue with the evidence that is interpretable
instead of blocking for clarification. If the conflict prevents a supported
classification, report the result as indeterminate.

The hard constraints worth stating up front:

- **No DWI+ADC → acute ischaemia cannot be assessed.** DWI alone is not enough;
  T2 shine-through mimics restricted diffusion.
- **No FLAIR or T2 → WMH burden cannot be assessed.**
- **No T1 → chronic cavity detection and the ventricle proxy are unavailable.**

### 2. Run the signature probe

**This is a voxel-wise computation.** In Neurodesk, run it only from a
version-pinned `analysis_<step>_<description>.sh` script submitted to Slurm.
Resolve this skill's installed directory before writing the script, store that
absolute path as `SKILL_DIR` in the script, and do not rely on agent
environment variables being passed to Slurm. Do not run the probe in an
interactive shell or notebook.

```bash
SKILL_DIR="/absolute/path/to/lesion-identification" # Replace with the installed path before submission.
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/lesion_signature.py"
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/lesion_signature.py" \
  --t1 T1w.nii.gz --flair FLAIR.nii.gz \
  --dwi dwi.nii.gz --adc adc.nii.gz \
  --mask brain_mask.nii.gz \
  --json lesion_id/signature.json
```

Pass only the modalities you have. Check the pinned `numpy`, `nibabel`, and
`scipy` versions in `${SKILL_DIR}/../../python-requirements.txt` before
submitting the job; report a mismatch instead of installing packages.
Use the documented CLI as a black box; do not read the full helper source just
to learn how to run it. Inspect its source only when debugging a demonstrated
implementation failure.

**Use a brain mask when one is already available and validated.** If the task is
identification-only and no mask is provided, run the probe's documented fallback
and state that its intensity statistics are less reliable because they may
include non-brain voxels. Do not expand an identification request into a
separate brain-extraction workflow just to avoid this limitation. If
segmentation is authorized, obtain a validated brain mask before proceeding.
For an identification-only fallback, treat mask-derived estimates as a
screening result and check their plausibility before interpreting the ranking.
For example, a clearly implausible estimated brain volume or very low
`head_symmetry_dice` means laterality and negative findings are unreliable. A
`none_detected` result from an implausible fallback is **inconclusive**, not
evidence that no lesion is present. Say which quality check failed, lower
confidence, and use visual review when available; if it is unavailable, finish
with an indeterminate assessment rather than a negative conclusion. Do not ask
the user to repair the analysis or supply missing context in an unattended run.

Keep discovery within the supplied case, this task's output workspace, the
relevant skill references, and the documented module catalog. Do not search the
filesystem root, unrelated home directories, system or historic Slurm logs,
other datasets, or unrelated datasets. If an expected tool or provenance
file is unavailable in that scope, report the limitation and continue only when
the remaining evidence supports the task.

**Group modalities by grid before probing.** Compare shape and affine and pass
only modalities that share a verified grid to one probe call (especially DWI
and ADC together). Run separate probe calls for other grid groups within the
same analysis script/job. The probe does not resample, because silently
resampling would manufacture cross-modal agreement the data do not support. If
a grid mismatch affects interpretation, report it; use only an existing
validated transform or an explicitly authorized registration workflow. Do not
treat equal dimensions as alignment. Verify DWI and ADC geometry rather than
assuming they match.

Read `references/signature-interpretation.md` for what each feature means, how
the ranking rules work, and the known false-positive modes. You need it to
interpret a result rather than transcribe it.

### 3. Visual review — if you can see images

Read `references/visual-identification.md` for the radiological patterns, then
generate and inspect an image. Vision earns its keep here on exactly the things
the probe cannot measure:

- **lesion morphology** — wedge-shaped and territorial (infarct) versus ovoid
  and perpendicular to the ventricles (MS) versus confluent caps and rims (WMH)
- **mass effect** — sulcal effacement, midline shift, ventricular compression,
  which point to tumour or a large acute infarct rather than small vessel disease
- **enhancement pattern**, if post-contrast imaging exists
- **the WMH/MS distinction**, which has no numeric rule (see below)

Reconcile with the probe. Where they disagree, say which you trusted and why.

### 4. Report the proposed type

State the leading hypothesis, evidence, alternatives, and limits. The probe
ranks hypotheses from image statistics with no access to the patient's age,
symptom onset time, stroke history, or referral question — information that
can change interpretation. For example, confluent periventricular FLAIR change
may be WMH in one context and require an MS workup in another. Reflect missing
context in the uncertainty; do not ask the user to supply it before completing
an identification-only report.

Present the ranked hypotheses, evidence for the top one, important visual
features, what could not be assessed, and your recommendation. Complete the
report without waiting for a reply. If the user explicitly asks for an
autonomous or unattended analysis, never ask a follow-up question: state
assumptions and uncertainty in the report instead.

An identification-only request ends with the ranked hypothesis and uncertainty.
For a generic segmentation request, apply step 5's explicit eligibility rule;
never present that research workflow classification as a clinical diagnosis.

If the probe returns `none_detected`, report that no in-scope type was
established only when the relevant inputs and measurements were usable. If the
mask, geometry, or acquisition quality makes the probe unreliable, label the
result inconclusive and state that a lesion is not excluded. Do not invent a
type merely to produce an output.

When the top hypothesis is **out of scope** (`focal_lesion_not_wmh`,
`ms_cannot_exclude`, or anything suggesting tumour or haemorrhage), say so
plainly and do not route it into a stroke or WMH segmenter. Recommend visual or
clinical review instead.

### 5. Hand off when the segmentation request and evidence support it

Treat a generic "segment this lesion" request as authorization to create a
research mask. Invoke exactly one of `acute-stroke-segmentation`,
`chronic-stroke-segmentation`, or `wmh-segmentation` only when (a) the task
already states that type, or (b) the report marks `segmentation_eligible: true`.
Set eligibility only when the required defining modalities are present and
interpretable, their spatial relationship is verified, the defining numeric
signature is present, and visual review finds no credible alternative that
would change the workflow. For acute stroke require concordant DWI-bright/ADC-
dark evidence; for chronic stroke require a T1 CSF-like cavity pattern; for
WMH require FLAIR-bright white-matter distribution without a credible MS-like
or focal-lesion alternative. If vision is unavailable and the quantitative
probe cannot distinguish a competing pathology, set eligibility false. Never
call the result a clinical diagnosis. Pass the candidate type, evidence,
uncertainty, modalities, requested grid/output, and signature JSON. An
identification-only task ends with the report; do not ask for confirmation.

### Output contract

This skill produces the signature JSON and an evidence-backed proposed lesion
type. It never turns a probe threshold or diagnostic region into the requested
segmentation. Mask execution and publication belong exclusively to the
confirmed pathology-specific skill.

## What this cannot do

State these limits in your report rather than letting them pass silently.

**WMH versus MS has no numeric rule.** Both are multifocal FLAIR hyperintensity,
often both periventricular. What separates them is morphology (ovoid, Dawson's
fingers), location (juxtacortical, infratentorial), and clinical context — none
of which this probe measures. When multifocal FLAIR change is found, it reports
`ms_cannot_exclude` and expects a human or a vision-capable model to settle it.
Treating that as WMH by default is a real misdiagnosis risk, not a formality.

**A bilateral symmetric cavity will be suppressed.** Chronic cavity detection
works by discarding CSF-like regions that have a mirror counterpart, since
normal cisterns, fissures and ventricles come in pairs. Genuinely bilateral
symmetric damage — bilateral watershed infarction, for instance — is filtered
out with them. The probe reports the pre-filter volume so this is visible.

**Absence of signature is not absence of lesion.** Thresholds are calibrated for
adult brain MRI at typical clinical contrast. Subtle, early, or unusual lesions
fall below them, and an unusual protocol can shift every intensity statistic.

**It does not diagnose.** It narrows the field and shows its reasoning. The
diagnosis belongs to a clinician.

## Constraints

- Run the probe before proposing a type for an unspecified or ambiguous lesion.
- Never route an out-of-scope lesion type into a segmenter. For a generic
  segmentation request, set `segmentation_eligible: true` only when the
  modality, geometry, defining-signature, and competing-pathology checks in
  step 5 all pass.
- State the evidence basis (numeric-only or numeric + visual) in every report.
- Quote the measured numbers, not just the ranking; they are what makes the
  conclusion checkable later.
- Say which sequences were missing and what that made unassessable.
- Do not resample or reorient modalities merely to force cross-modal features;
  establish a valid spatial relationship first.
- Treat metadata as evidence to cross-check, not ground truth when headers,
  filenames, and image content disagree.
