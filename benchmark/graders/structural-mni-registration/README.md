# Grader: `structural-mni-registration`

Grades a **T1w-to-MNI152NLin2009cAsym registration** by where the tissue lands, not by how much
the warped image resembles the template.

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/structural-mni-registration/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

That detail is gated because it describes the answer: in one benchmark wave, agent runs
retrieved these files from GitHub and one rebuilt the panel consensus from them. Access
is granted on request, and everything needed to audit *how* grading works — the gates,
weights, verdict thresholds and the scoring scale — stays here.

## Why label propagation, not image similarity

A registration is a spatial transform, so the question is where anatomy ends up. Correlation
between a warped T1w and the template is dominated by gross head position and is largely
saturated once *any* affine has been applied — on this subject it is 0.57 for an affine and
0.78–0.84 for a nonlinear warp, a difference that would not carry a benchmark on its own.

So the task supplies the subject's **tissue segmentation** and asks for it to be carried through
the same transform with nearest-neighbour interpolation. The grader measures the overlap of that
propagated tissue with the **template's own tissue priors** — a reference that says where GM, WM
and CSF belong in MNI space independently of any registration software, rather than agreement
with one pipeline's warp.

The segmentation is an agent **input**, not a reference.

## Scorer (ships in this pack)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_registration.py --warped agent_T1w_in_mni.nii.gz \
                             --dseg   agent_dseg_in_mni.nii.gz --pack . [--json result.json]
```

Both submissions must be on the template grid: 193 × 229 × 193 at 1 mm.

## Scale

Full marks at the median of four independent nonlinear registrations; zero credit at the median of
three affine-only ones. The score reads as *how far between a 12-DOF affine and a typical
nonlinear warp this is*.

| metric | weight | full marks | zero credit |
|---|---|---|---|
| WM Dice | 0.30 | 0.843 | 0.698 |
| GM Dice | 0.25 | 0.754 | 0.629 |
| brain Dice | 0.20 | 0.977 | 0.960 |
| in-brain correlation | 0.15 | 0.805 | 0.579 |
| CSF Dice | 0.10 | 0.343 | 0.255 |

Correlation is measured inside the template brain mask, so leaving the skull on is not penalised.
CSF is weighted least because the template prior and the subject's CSF differ in definition,
capping Dice for everyone.

Verdict: `within_reference_variability` when every metric is at least as good as the weakest panel member
nonlinear registration; else `acceptable`/`marginal`/`unacceptable` by weighted quality;
`invalid` on a gate failure.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`, `valid_labels`,
`nonempty`, `brain_volume_plausible` (1270–2420 cm³), `brain_in_place` (propagated brain centre
of mass within 5 mm of the template's).

`warped_finite_in_brain` rather than "no NaN anywhere": NiftyReg and other resamplers write NaN
outside the field of view by convention. Non-finite values are zeroed on load and judged only
inside the brain.

## Diagnostics

`suspected_label_permutation` is reported, never scored. It fires when some other assignment of
the same labels would score better — the signature of an agent that re-segmented the image with a
different convention instead of warping the file it was given.

## Layout

```
structural-mni-registration/
├── rubric.json               # envelope, weights, gate caps, grid, label convention
├── score_registration.py     # the scorer
├── reference/                # template + priors — fetched from the Hub
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-mni-registration/`.

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
