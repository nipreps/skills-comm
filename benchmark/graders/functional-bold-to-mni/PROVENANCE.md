# Provenance: `functional-bold-to-mni`

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/functional-bold-to-mni/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Item

| | |
|---|---|
| dataset | OpenNeuro `ds002790` (AOMIC PIOP1), tag `2.0.0` |
| subject | `sub-0019` |
| run | `task-restingstate_acq-seq_bold` |
| BOLD | 80 × 80 × 36 × 240 at 3 × 3 × 3.3 mm |
| anatomical | `sub-0019_T1w.nii.gz` |
| template | MNI152NLin2009cAsym, TemplateFlow `res-01`, 193 × 229 × 193 at 1 mm |

Acquisition is scripted in `analysis_00_download_data.sh`: a metadata-only `datalad clone` of
the OpenNeuro dataset, checkout of tag `2.0.0`, then `datalad get` for the BOLD, the T1w, and the
grader-side fMRIPrep derivatives. The template is fetched from TemplateFlow.

## Agent inputs

`input/bold.nii.gz`, `input/T1w.nii.gz`, and the template with its brain mask. No transform is
supplied. The shipped fMRIPrep T1w-to-MNI transform is an ANTs `.h5`; handing it over would force
an ANTs-shaped answer and tax every other toolchain with a format conversion, so the agent computes
the whole chain itself.

The goal text names the target space and the required outputs, not the route.

## Scored metrics and how they were chosen

Four metrics were computed for every arm before any rubric was written.

| arm | in-brain NMI | com offset (mm) | brain Dice | edge corr (σ=2) |
|---|---|---|---|---|
| `ANTs_correct` | 0.0580 | 1.21 | 0.9365 | 0.6807 |
| `fMRIPrep` | 0.0560 | 0.91 | 0.9151 | 0.6731 |
| `FSL_chain` | 0.0538 | 0.50 | 0.9297 | 0.5601 |
| `ANTs_no_epi` | 0.0539 | 2.99 | 0.9288 | 0.6247 |
| `ANTs_reversed` | 0.0289 | 3.02 | 0.9111 | 0.5576 |
| `Direct_affine` | 0.0220 | 3.34 | 0.8602 | 0.5211 |
| `Direct_SyN` | 0.0153 | 12.29 | 0.5919 | 0.1435 |

**NMI and centre-of-mass offset are scored.** Both split the panel the same way and with margin:
NMI puts the panel's band at 0.0538–0.0580 against ≤0.0289 for every wrong chain (1.9×), and
offset puts it at 0.50–1.21 mm against ≥2.99 mm (2.5×).

**Brain Dice is rejected.** Its whole range is 0.86–0.94 and it is *inverted* where it matters:
`ANTs_no_epi` (0.9288) outscores the accepted `fMRIPrep` (0.9151), which would place the floor
anchor above the full-marks anchor and make the subscore denominator negative.

**Edge correlation is rejected.** It ranks the arms correctly but measures registration fineness,
which differs legitimately between acceptable tools. A σ sweep over the panel:

| arm | σ=1 | σ=2 | σ=3 | σ=4 | σ=6 | σ=8 |
|---|---|---|---|---|---|---|
| `ANTs_correct` | 0.5609 | 0.6807 | 0.7499 | 0.7862 | 0.7966 | 0.8053 |
| `fMRIPrep` | 0.5563 | 0.6731 | 0.7344 | 0.7619 | 0.7634 | 0.7764 |
| `FSL_chain` | 0.4136 | 0.5601 | 0.6614 | 0.7306 | 0.7861 | 0.8082 |
| `ANTs_reversed` | 0.4194 | 0.5576 | 0.6581 | 0.7212 | 0.7634 | 0.7849 |
| `Direct_affine` | 0.3974 | 0.5211 | 0.6266 | 0.6946 | 0.7422 | 0.7816 |

At every σ where the metric separates at all, the FSL chain sits with the wrong arms; by
σ=8 it tops `ANTs_correct` while nothing separates. The blur is not an artifact of resampling —
a singly-resampled FSL output scores identically at every σ.

Gradient-based GM/WM contrast was also screened and discarded: 1.05–1.09 across the whole panel.

## Calibrated envelope

| metric | best | median (full marks) | worst | floor (zero credit) |
|---|---|---|---|---|
| in-brain NMI | 0.0580 | 0.0560 | 0.0538 | 0.0220 |
| com offset (mm) | 0.50 | 0.91 | 1.21 | 3.34 |

Weights 0.50 / 0.50. Gate caps: brain volume 1230–3030 cm³, centre of mass within 8 mm.

## Is the task measuring routing, or BOLD preparation?

The agent is handed the unpreprocessed 4D series, and the panel's band is asymmetric: fMRIPrep's
reference is motion- and distortion-corrected while the ANTs and FSL arms average the raw series.
If the score mostly tracked how well the reference was prepared, the task would not be measuring
the routing choice it claims to. Held one fixed and varied the other
(`analysis_08_prep_sensitivity.sh`):

| reference preparation | route | NMI | offset (mm) | verdict | quality |
|---|---|---|---|---|---|
| raw temporal mean | anatomy-mediated | 0.0580 | 1.21 | within_reference_variability | 93.71 |
| motion-corrected mean | anatomy-mediated | 0.0570 | 1.25 | acceptable | 92.91 |
| motion-corrected mean | direct to template | 0.0240 | 2.47 | unacceptable | 20.80 |
| raw temporal mean | direct to template | 0.0220 | 3.34 | unacceptable | 0.00 |

Preparation moves quality by 0.80; routing moves it by 72.11 — a factor of about 90. The reason
preparation matters so little is that this subject barely moved: the raw temporal mean and the
motion-corrected mean correlate at 0.9999, with a mean relative difference of 0.0064.

The decisive row is the third. A well-prepared reference taken the wrong way still scores 20.80 and
stays `unacceptable`: good preparation does not rescue the wrong route. Better preparation does
lift the direct arm from 0.00 to 20.80, which is the expected direction and well inside the failing
band.

## Why composition order is not what this task discriminates

`antsApplyTransforms` applies its transform list right-to-left, and getting that backwards is a
classic bug — but on this data it is not measurable as displacement, so it cannot anchor a grader.

The reason is the near-identity transform above. Reversing a 1.6 mm rigid transform against a large
nonlinear warp perturbs the result by less than the metrics resolve: brain-mask Dice puts the
reversed arm at 0.9111 against the panel's 0.9151, and in the QC panel every arm is the same brain
in the same place. Same-session BOLD and T1w is the normal case for a BIDS dataset rather than a
quirk of this subject, so no choice of subject would change that.

The bug is real as *code*. It appears here as the `ANTs_reversed` candidate arm, where the scored
metrics do separate it (16.7), but the failure the task is built to discriminate is the routing
choice, not the ordering of a transform list.

## Reproduction

```
analysis_00_download_data.sh    # datalad + TemplateFlow acquisition
analysis_01_panel.sh            # ANTs arms + fMRIPrep comparator
analysis_03_probe_arms.sh       # direct-to-template arms
analysis_05_fsl_arm.sh          # FSL chain against the 2009cAsym reference
analysis_04_metric_screen.sh    # candidate-metric screen
analysis_06_edge_sigma.sh       # edge-correlation sigma sweep
analysis_02_calibrate.py        # envelope, rubric, QC panel
analysis_07_validate.sh         # perturbation validation
```

QC panel: `qc_01_panel_pack.png` — template brain in green, propagated BOLD brain in red, axial
and coronal, one column per arm.

## Known limitations

- **The panel band is tight** (NMI 0.0538–0.0580) and reflects three tools on one dataset
  rather than population variability.
- Susceptibility distortion is only partly corrected, and not uniformly across the panel's band.
  The dataset ships a phase-difference fieldmap whose `IntendedFor` lists this run, but fMRIPrep's
  report states it used fieldmap-less (SyN-based) correction instead; the ANTs and FSL arms apply
  none. Standard fieldmap correction is in practice unavailable here, because the BOLD sidecar
  carries no `TotalReadoutTime` or `EffectiveEchoSpacing` and `fugue` cannot be scaled without
  deriving echo spacing from the Philips `WaterFatShift`. Residual distortion therefore caps
  achievable NMI, and the three accepted arms do not all treat it the same way. That they still
  agree to within 0.0042 NMI is what licenses the band.
- The centre-of-mass metric is computed on the propagated brain mask, so it inherits whatever
  brain extraction the agent used on the BOLD reference. The volume-plausibility gate is wide
  (1230–3030 cm³) for that reason.
