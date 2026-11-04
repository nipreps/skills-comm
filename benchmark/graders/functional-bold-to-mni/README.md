# Grader: `functional-bold-to-mni`

Grades a **BOLD-to-MNI152NLin2009cAsym normalisation** by whether the functional data was taken to
the template through the subject's own anatomy, or matched to it directly.

## The reference

The template and its brain mask, which say where a brain belongs independently of any
registration software. What a correct answer looks like is set by a panel of independent
BOLD-to-MNI chains, whose agreement — not any single tool's opinion — defines the scale.

Which chains, in what configuration, and the calibrated anchors are in
`calibration/functional-bold-to-mni/PROVENANCE.md` in the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth),
because naming them would let a submission reproduce the reference instead of solving the
task. Everything governing how a submission is *graded* is here and in [`rubrics/`](rubrics/).

## What this task discriminates

The BOLD is a distorted 3 mm EPI; the template is a 1 mm T1w. Registering one to the other
directly is a cross-modal, cross-resolution match with no subject anatomy to mediate it, and it is
a common shortcut. Routing through the subject's T1w — EPI-to-anatomical, then
anatomical-to-template — is the standard route and the one every reference pipeline takes.

The goal text does not name the route. Both the BOLD and the subject's T1w are supplied as inputs;
choosing what to do with the T1w is the task.

## What is graded

Mask overlap and edge correlation both saturate here, so neither separates a good
normalisation from a mediocre one. The grader scores mutual information inside the brain
together with the centre-of-mass offset, which do.
[`PROVENANCE.md`](PROVENANCE.md) gives the measurements behind that choice.

## Preparation and distortion

The agent receives the **unpreprocessed** 4D series, and susceptibility distortion is handled
differently by different members of the panel. Standard fieldmap correction is not practically
available here — the dataset's phase-difference fieldmap names this run in `IntendedFor`, but the
BOLD sidecar carries no `TotalReadoutTime` or `EffectiveEchoSpacing`, so `fugue` cannot be scaled
without deriving echo spacing from the Philips `WaterFatShift`.

That unevenness does not confound the score, because the graded difference is far larger than the
preparation difference: holding the route fixed and motion-correcting the reference moves quality
by less than a point, while holding preparation fixed and switching from the anatomy-mediated
route to the direct one moves it by about ninety times as much. A well-prepared reference taken
the direct route is still `unacceptable`. Preparation does not buy its way out of the wrong route.

Residual distortion is common to accepted and candidate chains, so it caps achievable NMI for
everyone rather than favouring any arm.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_registration.py --warped agent_boldref_in_mni.nii.gz \
                             --dseg   agent_boldmask_in_mni.nii.gz --pack . [--json result.json]
```

Both submissions must be on the template grid: 193 × 229 × 193 at 1 mm. `--dseg` takes the BOLD
brain mask here rather than a tissue segmentation; the scorer runs in `cross_modal` mode, set in
`rubrics/<subject>.json`.

## Scale

Full marks at the median of the accepted chains; zero credit at registering the BOLD straight to
the template with a 12-DOF affine, ignoring the subject's anatomy. The score reads as *how far
between the direct shortcut and a typical anatomy-mediated normalisation this is*. The anchors
are per subject and gated with the reference; the weights are not:

| metric | weight |
|---|---|
| in-brain NMI | 0.50 |
| brain centre-of-mass offset | 0.50 |

Normalised mutual information rather than correlation because BOLD and a T1w template share
structure but no intensity relationship. It is measured inside the template brain mask, so a
retained skull cannot dominate it. Centre-of-mass offset is measured on the propagated brain mask
and catches a chain that is globally displaced while still overlapping.

Verdict: `within_reference_variability` when both metrics are at least as good as the weakest chain in the panel;
else `acceptable`/`marginal`/`unacceptable` by weighted quality; `invalid` on a gate failure.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`, `binary_mask`,
`nonempty`, `brain_volume_plausible`, `brain_in_place` (propagated brain centre of mass close to
the template's). Both caps are set per subject in `rubrics/<subject>.json`.

`warped_finite_in_brain` rather than "no NaN anywhere": resamplers write NaN outside the field of
view by convention. Non-finite values are zeroed on load and judged only inside the brain.

## Layout

```
functional-bold-to-mni/
├── rubrics/<subject>.json    # weights, gate caps, scoring mode; envelope and grid merged from the Hub
├── score_registration.py     # the scorer, shared with structural-mni-registration
├── reference/                # template + brain mask — fetched from the Hub
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `fmri_gt/functional-bold-to-mni/`.

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
