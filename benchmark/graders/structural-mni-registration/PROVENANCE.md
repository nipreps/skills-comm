# Provenance — how this grader pack was calibrated

One rubric per subject, in `rubrics/<subject>.json`, each the frozen output of a calibration
on that subject's own panel. Scoring a submission never re-derives them.

**ds002790**, T1w at 1 mm, registered to **MNI152NLin2009cAsym** (TemplateFlow, `res-01`,
193 × 229 × 193 at 1 mm). The template is the same for every subject, so the reference is
shared and only the rubric varies.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-mni-registration/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## What is graded, and why it is not the warped image

A registration is a spatial transform. The obvious thing to grade — how much the warped T1w
resembles the template — turns out to be nearly useless for separating a good registration from a
mediocre one: correlation is dominated by gross head position and is largely saturated once *any*
affine has been applied. The tissue that actually moved tells a much sharper story, and the
figure in [`README.md`](README.md) shows what that looks like.

So the task hands the agent the subject's **tissue segmentation** alongside the T1w and asks for
it to be carried through the same transform with nearest-neighbour interpolation. The grader then
measures **where the tissue landed**. This is label propagation, the standard way registration is
evaluated, and it is tool-agnostic: every registration package can apply its own transform to a
second image.

The segmentation is an agent **input**, not a reference.

## The reference is the template, not another tool

Grading against fMRIPrep's MNI output would measure agreement with one implementation of one
pipeline, not registration quality. The reference is instead the **template's own tissue priors** (`label-{GM,WM,CSF}_probseg`), which state where
each tissue belongs in MNI space independently of any registration software.

A population prior is not a per-subject truth, so no absolute Dice threshold would be defensible.
The scale is therefore relative and data-derived:

- **full marks** = the median of four independent nonlinear registrations on that subject;
- **zero credit** = the median of three affine-only registrations on the same subject.

The score reads directly as *"how far between a 12-DOF affine and a typical nonlinear warp is
this?"* Anchoring the floor on the affine rather than on a slack multiple of the accepted spread
matters here, because the nonlinear panel members agree closely with each other; a slack-based
floor would sit inside that spread and make scoring brittle.

## Label convention

The supplied segmentation uses **1 = GM, 2 = WM, 3 = CSF**. This was verified from the data, not
assumed: mean T1w intensity per label is 156 k / 233 k / 82 k, and WM is the brightest tissue on a
T1w, which fixes the mapping. `rubrics/<subject>.json` carries it as `tissue_labels` so the scorer never
guesses.

The scorer additionally reports (never scores) `suspected_label_permutation` when some other
assignment of the same labels would score better — the signature of an agent that re-segmented
the image with a different convention instead of warping the file it was given. That turns a
confusing near-zero into an actionable one.

## Metrics and weights

| metric | weight |
|---|---|
| WM Dice | 0.30 |
| GM Dice | 0.25 |
| brain Dice | 0.20 |
| in-brain correlation | 0.15 |
| CSF Dice | 0.10 |

The full-marks and zero-credit anchors behind each metric are per subject and gated with the
reference.

WM carries the most weight because it is the most sensitive to nonlinear quality. CSF carries the
least: the template CSF prior is mostly ventricles while the subject's CSF includes the sulci, so
the two definitions differ and Dice is capped low for everyone. It still moves in the right
direction between an affine and a nonlinear warp, and is kept at low weight.

Image correlation is measured **inside the template brain mask**, so an agent that leaves the
skull on is not penalised for it.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`, `valid_labels`,
`nonempty`, `brain_volume_plausible`, `brain_in_place` (propagated brain centre of mass close to
the template's). Both caps are set per subject from that subject's own panel.

`warped_finite_in_brain` is deliberately not "no NaN anywhere": some
resamplers write NaN outside the field of view rather than zero, which is a convention, not a
defect. Non-finite values are zeroed on load and judged only where they matter — inside the brain.

## Runtime

Not a barrier, which was worth checking before building the task: the slowest package in the build took about 25 minutes per
subject at 1 mm on 10 cores, and the fastest under 2. All fit inside a 45-minute agent budget, so
the skill arm cannot be penalised for choosing a slower-but-better tool.

## Reference data

`reference/template_*.nii.gz` are on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-mni-registration/`). They are unmodified TemplateFlow
files, redistributable under the template's own licence. Fetch them before grading; see
`reference/README.md`.
