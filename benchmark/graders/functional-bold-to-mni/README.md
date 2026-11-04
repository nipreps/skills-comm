# Grader: `functional-bold-to-mni`

Grades a **BOLD-to-MNI152NLin2009cAsym normalisation** by whether the functional data was taken to
the template through the subject's own anatomy, or matched to it directly.

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/functional-bold-to-mni/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

Gated so that a submission cannot reproduce the reference instead of solving the
task. Everything governing how a submission is *graded* stays here.

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
unevenly across the panel's band: fMRIPrep applies fieldmap-less (SyN-based) correction, while the
ANTs and FSL chains apply none. Standard fieldmap correction is not practically available here —
the dataset's phase-difference fieldmap names this run in `IntendedFor`, but the BOLD sidecar
carries no `TotalReadoutTime` or `EffectiveEchoSpacing`, so `fugue` cannot be scaled without
deriving echo spacing from the Philips `WaterFatShift`.

That unevenness does not confound the score, because the graded difference is far larger than the
preparation difference. Holding the route fixed and motion-correcting the reference moves quality
by 0.80; holding preparation fixed and switching from the anatomy-mediated route to the direct one
moves it by 72.11 — a factor of about 90. The decisive case is a well-prepared reference taken the
direct route: it still scores 20.80 and remains `unacceptable`. Preparation does not buy its way
out of the wrong route.

Residual distortion is common to accepted and candidate chains, so it caps achievable NMI for
everyone rather than favouring any arm. That three chains treating distortion differently — none,
fieldmap-less nonlinear, and BBR-affine — still agree to within 0.0042 NMI is what licenses the
panel band. Full numbers in `PROVENANCE.md`.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_registration.py --warped agent_boldref_in_mni.nii.gz \
                             --dseg   agent_boldmask_in_mni.nii.gz --pack . [--json result.json]
```

Both submissions must be on the template grid: 193 × 229 × 193 at 1 mm. `--dseg` takes the BOLD
brain mask here rather than a tissue segmentation; the scorer runs in `cross_modal` mode, set in
`rubric.json`.

## Scale

Full marks at the median of the three chains; zero credit at registering the BOLD straight to
the template with a 12-DOF affine, ignoring the subject's anatomy. The score reads as *how far
between the direct shortcut and a typical anatomy-mediated normalisation this is*.

| metric | weight | full marks | zero credit |
|---|---|---|---|
| in-brain NMI | 0.50 | 0.0560 | 0.0220 |
| brain centre-of-mass offset | 0.50 | 0.91 mm | 3.34 mm |

Normalised mutual information rather than correlation because BOLD and a T1w template share
structure but no intensity relationship. It is measured inside the template brain mask, so a
retained skull cannot dominate it. Centre-of-mass offset is measured on the propagated brain mask
and catches a chain that is globally displaced while still overlapping.

Verdict: `within_reference_variability` when both metrics are at least as good as the weakest chain in the panel;
else `acceptable`/`marginal`/`unacceptable` by weighted quality; `invalid` on a gate failure.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`, `binary_mask`,
`nonempty`, `brain_volume_plausible` (1230–3030 cm³), `brain_in_place` (propagated brain centre of
mass within 8 mm of the template's).

`warped_finite_in_brain` rather than "no NaN anywhere": resamplers write NaN outside the field of
view by convention. Non-finite values are zeroed on load and judged only inside the brain.

## Layout

```
functional-bold-to-mni/
├── rubric.json               # envelope, weights, gate caps, grid, scoring mode
├── score_registration.py     # the scorer, shared with structural-mni-registration
├── reference/                # template + brain mask — fetched from the Hub
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `fmri_gt/functional-bold-to-mni/`.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubric.json`.

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
