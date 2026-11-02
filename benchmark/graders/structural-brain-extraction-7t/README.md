# Grader: `structural-brain-extraction-7t`

A **consensus-calibrated grader** for skull-stripping a **7 Tesla MP2RAGE** scan
(CEREBRUM-7T `ds003642`; sub-025, sub-045 and sub-075, 0.63 mm isotropic). It is the companion to
`structural-brain-extraction` (healthy 3T baseline) on the **field-strength / sequence axis**.

Same design as the baseline: score a submission against a STAPLE consensus of a tool panel split
into core (must keep) / margin (free, not scored) / background (must exclude), with all thresholds
calibrated from the tools' own disagreement. See [`PROVENANCE.md`](PROVENANCE.md).

## Shared scorer (no duplication)

This pack carries **only the calibration** (`rubrics/<subject>.json`) and the reference pointer — it does
**not** ship its own scorer. Grade with the shared scorer from the baseline pack, pointing `--pack`
here:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

## What's hard here

The MP2RAGE **UNI** image (BIDS-named `T1w`) has salt-and-pepper noise filling the entire
background — there is no clean air boundary. On top of that the 7T contrast and bias field defeat
intensity-based extraction. The result:

- **Intensity-based `bet` fails catastrophically** — it retains ~557 cm³ (roughly half a brain),
  tripping `volume_plausible` + `no_catastrophic_core_loss` → `invalid`. This holds whether or not
  the background is cleaned first, so it is a genuine tool-choice failure, not a preprocessing slip.
- **Contrast-robust deep-learning tools succeed on the raw image** — HD-BET at its defaults scores
  `within_reference_variability` on all three subjects. A competent agent reaches for one of these
  (or denoises the UNI via the INV2 image first).

So this task discriminates on **tool choice for a high-field sequence**, where the common `bet`
default is the wrong call.

## Reference panel

Three independent algorithms, each run on the image its assumptions fit:

| tool | image | why |
|---|---|---|
| **HD-BET** | cleaned UNI | deep learning, contrast-tolerant |
| **SynthStrip `-b -2`** | cleaned UNI | deep learning, border pulled in 2 mm off the dura |
| **ANTs** | INV2 | template registration with the OASIS cerebellum prior |

**AFNI `3dSkullStrip` and FSL BET are not in the panel.** Both are surface-expansion methods
and need a real skull edge, which the MP2RAGE UNI does not give them: measured against the
dataset's own CEREBRUM7T labels, AFNI retains 32.8–86.4 % of the cerebellum and returns the mask
in 5–10 pieces, BET retains 0.0–0.1 %. No shrink factor or fractional-intensity threshold recovers
it. Both are still run and reported as non-reference comparisons, and both come out `invalid`,
which is what validates the gates.

**ANTs runs on INV2, not the UNI**, for the same reason: INV2 is a plain magnitude image with
ordinary tissue contrast. On the UNI it keeps 96.5 % of the cerebellum, on INV2 99.5 %. INV2 shares
the UNI's grid and affine, so the mask needs no resampling.

**SynthStrip uses `-b -2`, not `--no-csf`.** Both pull the mask off the dura, but `--no-csf`
removes CSF everywhere including the interior cisterns the other two keep — 3.06 of 3.1 cm³ of
sub-075's interior margin, against 0.00 for HD-BET and ANTs. A negative border erodes the boundary
uniformly and leaves the interior alone.

- **τ = 3.85–4.15 mm** across the subjects — the 95th percentile of pairwise surface
  disagreement. The panel is tight because all three members are run on an image that suits them.

## Layout

```
structural-brain-extraction-7t/
├── rubrics/<subject>.json  # per-subject frozen calibration: τ, envelope, weights, gate caps, grid.raw_affine
├── reference/           # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md        #   dataset path + fetch command
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-7t/<subject>/`.
The pack is frozen once; scoring never re-calibrates.

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
