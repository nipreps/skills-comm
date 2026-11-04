# Provenance — how this grader pack was calibrated

One rubric per subject, in `rubrics/<subject>.json`, each the frozen output of a
calibration on that subject's own panel. Scoring a submission never re-derives them.

## How the reference was built

A panel of independent BOLD-to-MNI chains, each run on the subject's own data and each
emitting a BOLD reference and a BOLD brain mask on the template grid, plus arms that take
the routing shortcuts the task exists to separate.

Which chains, in what configuration, the calibrated anchors and the measurements behind
the metric choice are in `calibration/functional-bold-to-mni/PROVENANCE.md` in the gated
reference dataset, because naming them would let a submission reproduce the reference
instead of solving the task.

## Item

| | |
|---|---|
| dataset | OpenNeuro `ds002790` (AOMIC PIOP1), tag `2.0.0` |
| run | `task-restingstate_acq-seq_bold`, 240 volumes |
| BOLD | 80 × 80 × 36 at 3 × 3 × 3.3 mm |
| anatomical | the subject's `T1w.nii.gz` |
| template | MNI152NLin2009cAsym, TemplateFlow `res-01`, 193 × 229 × 193 at 1 mm |

Acquisition is scripted: a metadata-only `datalad clone` of the OpenNeuro dataset,
checkout of tag `2.0.0`, then `datalad get` for the BOLD, the T1w, and the grader-side
derivatives. The template is fetched from TemplateFlow.

## Which subjects, and why those

Eight files are needed per subject, and 224 of the 226 have all of them, so availability
does not narrow the pool. The choice is made on head motion instead: the chain starts from
a temporal mean of the raw series, and motion blurs that mean. It does not favour one
routing over another, but it widens the band the panel agrees within, and a subject whose
reference image is smeared would make the task measure the subject rather than the answer.

`analysis_09_screen_pool.sh` reads mean framewise displacement from the shipped confounds
tables — the standard summary of that (Power et al. 2012,
[doi:10.1016/j.neuroimage.2011.10.018](https://doi.org/10.1016/j.neuroimage.2011.10.018))
— with no image fetched. The pool is homogeneous: every run is 240 volumes and mean FD
spans 0.067–0.357 mm with a median of 0.117. Subjects with more than 5% of volumes above
0.5 mm, or any single jump above 2 mm, are dropped, and the graded subjects are those
nearest the 10th, 35th, 60th and 85th percentile of mean FD among the rest. Subjects used
by another ds002790 task are excluded up front, so an agent cannot reuse an answer it has
already produced.

The selection and its rejections are in `pool_bold.json` and `subjects.tsv`.

## What is graded, and why not the obvious things

The BOLD is a distorted 3 mm EPI; the template is a 1 mm T1w. Mask overlap and edge
correlation both fail to separate a correct chain from a wrong one here — overlap because
the outline of a brain-shaped object stays put even when its interior is displaced, edge
correlation because it measures registration fineness, which differs legitimately between
acceptable tools. Both were computed for every arm and rejected on the numbers, which are
in the gated file.

What remains separates the panel cleanly and in the same order: **mutual information
inside the template brain mask**, and **where the brain physically landed**. NMI rather
than correlation because BOLD and a T1w template share structure but no intensity
relationship; measured inside the brain mask so a retained skull cannot dominate it.
Centre-of-mass offset catches a chain that is globally displaced while still overlapping.

Weights are 0.50 / 0.50: the two metrics are independent of each other and neither is
gated elsewhere, so nothing argues for favouring one.

## Gates

`warped_on_template_grid`, `dseg_on_template_grid`, `warped_finite_in_brain`,
`binary_mask`, `nonempty`, `brain_volume_plausible`, `brain_in_place`. The last two carry
caps set per subject from that subject's own panel.

`warped_finite_in_brain` is deliberately not "no NaN anywhere": some resamplers write NaN
outside the field of view rather than zero, which is a convention, not a defect.
Non-finite values are zeroed on load and judged only where they matter — inside the brain.

`binary_mask` tests the submitted values rather than their rounding. Rounding maps anything
in `[0, 1]` onto `{0, 1}`, which would let a probability map pass silently while failing a
`{0, 255}` mask — a form several tools write. A mask is binary when it holds a single
non-zero value, whatever that value is.

## Reproduction

```
analysis_00_download_data.sh        # datalad + TemplateFlow acquisition
analysis_09_screen_pool.sh          # motion screen over the dataset
analysis_10_panel_subject.sh        # the panel, one array task per subject
analysis_11_calibrate_subjects.py   # per-subject envelopes and rubrics
```

The single-subject scripts the method was first established with — the metric screen, the
edge-correlation sigma sweep, the perturbation validation and the preparation-sensitivity
test — are numbered `analysis_01` to `analysis_08` and are kept so the choices behind the
rubric stay reproducible.

## Known limitations

- **The panel band is tight** and reflects three chains on one dataset rather than
  population variability.
- Susceptibility distortion is only partly corrected, and not uniformly across the panel.
  It therefore caps achievable NMI for every arm rather than favouring one; that chains
  treating it differently still agree closely is what licenses the band.
- The centre-of-mass metric is computed on the propagated brain mask, so it inherits
  whatever brain extraction the agent used on the BOLD reference. The volume-plausibility
  gate is wide for that reason.
