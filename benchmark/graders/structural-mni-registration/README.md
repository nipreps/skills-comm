# Grader: `structural-mni-registration`

Grades a **T1w-to-MNI152NLin2009cAsym registration** by where the tissue lands, not by how much
the warped image resembles the template.

![What the registration grader measures: the subject's tissue segmentation is carried through the submitted transform and compared with the template's own tissue priors. A nonlinear warp places most white matter where the prior expects it; an affine-only warp leaves much of it outside, which is the gap the score reads.](registration_grading.png)

*Full size: [`registration_grading.png`](registration_grading.png). Axial slice through the
template, white matter shown; blue is tissue where the prior expects it, red is tissue placed
outside it.*

## The reference

The template's own tissue priors, which state where each tissue belongs in MNI space
independently of any registration software. The reference is not another tool's warp, and
it is the same for every subject.

What varies by subject is the scale: how well a panel of independent nonlinear
registrations lands that subject's tissue on those priors. Which registrations, and the
anchors they set, are in `calibration/structural-mni-registration/PROVENANCE.md` inside
the gated reference dataset [`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth),
because naming them would let a submission reproduce the scale instead of solving the
task. Everything governing how a submission is *graded* stays here and in
[`rubrics/`](rubrics/).

## What is graded

Not how much the warped T1w resembles the template — that is saturated once any affine has
been applied. Instead the subject's **tissue segmentation** is carried through the same
transform with nearest-neighbour interpolation, and the grader measures where that tissue
landed against the template's own tissue priors. The segmentation is an agent **input**,
not a reference. [`PROVENANCE.md`](PROVENANCE.md) gives the measurements behind that choice.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_registration.py --warped agent_T1w_in_mni.nii.gz \
                             --dseg   agent_dseg_in_mni.nii.gz --pack . [--json result.json]
```

Both submissions must be on the template grid: 193 × 229 × 193 at 1 mm.

## Scale

Full marks at the median of four independent nonlinear registrations; zero credit at the
median of three affine-only ones. The score reads as *how far between a 12-DOF affine and a
typical nonlinear warp this is*. The anchors are per subject and gated with the reference;
the weights are not:

| metric | weight |
|---|---|
| WM Dice | 0.30 |
| GM Dice | 0.25 |
| brain Dice | 0.20 |
| in-brain correlation | 0.15 |
| CSF Dice | 0.10 |

Correlation is measured inside the template brain mask, so leaving the skull on is not penalised.
CSF is weighted least because the template prior and the subject's CSF differ in definition,
capping Dice for everyone.

Verdict: `within_reference_variability` when every metric is at least as good as the weakest panel member
nonlinear registration; else `acceptable`/`marginal`/`unacceptable` by weighted quality;
`invalid` on a gate failure.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`, `valid_labels`,
`nonempty`, `brain_volume_plausible`, `brain_in_place` (propagated brain centre of mass close to
the template's). Both caps are set per subject in `rubrics/<subject>.json`.

`warped_finite_in_brain` rather than "no NaN anywhere": some resamplers write NaN
outside the field of view by convention. Non-finite values are zeroed on load and judged only
inside the brain.

## Diagnostics

`suspected_label_permutation` is reported, never scored. It fires when some other assignment of
the same labels would score better — the signature of an agent that re-segmented the image with a
different convention instead of warping the file it was given.

## Layout

```
structural-mni-registration/
├── rubrics/<subject>.json    # weights, gate caps, label convention; envelope and grid merged from the Hub
├── score_registration.py     # the scorer
├── reference/                # template + priors — fetched from the Hub
│   ├── README.md
│   └── .gitignore
├── registration_grading.png  # the explainer figure above
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-mni-registration/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubrics/<subject>.json`.

| verdict | meaning |
|---|---|
| `within_reference_variability` | inside the panel's own leave-one-tool-out spread — every metric is at least as good as the weakest the reference tools themselves achieve, so the submission cannot be told apart from a panel member |
| `acceptable` | `quality >= 60` |
| `marginal` | `quality >= 30` |
| `unacceptable` | below that |
| `invalid` | a validity gate failed; `quality` is forced to 0 |

A submission passes when the verdict is `within_reference_variability` or `acceptable`.
`within_reference_variability` is the top grade, not a hedge: it says the answer sits
inside the disagreement the reference itself carries, which is as close as this task can
measure.
