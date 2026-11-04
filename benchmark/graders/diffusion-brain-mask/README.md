# Grader: `diffusion-brain-mask`

Grades a **brain mask made from a DWI b0** against a consensus of a masking-tool panel
(ds001226, five subjects, `ses-preop`, `acq-AP`, 2.5 mm isotropic).

**What it tests: whether the b0 is prepared before it is masked.** On the raw series every
intensity-threshold method loses the same anatomy — cerebellum, temporal poles, brainstem — to
the inferior receive-coil bias field, and a mask missing one of those regions fails a validity
gate rather than merely scoring low. The task is passable both by preparing the b0 and by
choosing a method that does not depend on intensity, so it is not a test of tool identity.

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/diffusion-brain-mask/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

Gated so that a submission cannot reproduce the reference instead of solving the
task. Everything governing how a submission is *graded* stays here.

## Scorer (shared with the brain-extraction packs)

```bash
# fetch the reference (see reference/README.md), then:
python3 score_brain_mask.py --mask agent_mask.nii.gz --pack . [--json result.json]
```

The submission is a **binary brain mask on the diffusion grid** (96 × 96 × 60, 2.5 mm).

## Metrics

Weighted quality over five metrics, each mapped to [0, 1] by the leave-one-tool-out envelope —
1.0 at the median panel tool, 0.0 at 1.5× beyond the worst:

- **NSD** within the task's surface tolerance τ (0.30) — boundary agreement
- **core recall** (0.25) — brain must not be cut
- **background false-positive fraction** (0.20) — skull and neck must not be retained
- **HD95** (0.15) — worst-case boundary excursion
- **absolute volume error %** (0.10)

Dice is reported but not scored: it is a function of the two directional errors, so scoring it
would weight the same information twice.

Verdict: `within_reference_variability` when every metric reaches full marks; else
`acceptable`/`marginal`/`unacceptable` by weighted quality; `invalid` on any gate failure.

## Gates

`binary`, `native_grid`, `nonempty`, `single_component`, `no_internal_holes`,
`volume_plausible` (1020–2290 cm³), `no_catastrophic_core_loss` (≤ 10 % of core),
`no_focal_core_loss` (a solid chunk surviving a max(1.5 mm, one voxel) shave — here one
voxel, 2.5 mm; a uniformly tighter boundary is priced by τ, NSD and HD95 instead),
`no_focal_bg_inclusion` (≤ 40 cm³, measured the same way),
`stripped_matches_mask`.

**The gates name the failure.** Dice alone would not separate these: `bet -f 0.2` reaches Dice
0.927 while retaining skull, higher than raw `dwi2mask` at 0.924 which loses the cerebellum.

## Layout

```
diffusion-brain-mask/
├── rubrics/<subject>.json   # per-subject calibrated numbers (tau, envelope, weights, gate caps, grid)
├── score_brain_mask.py   # shared scorer, unmodified
├── reference/            # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `diffusion_gt/diffusion-brain-mask/<subject>/`.

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
