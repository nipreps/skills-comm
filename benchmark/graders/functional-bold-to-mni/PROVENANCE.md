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

Motion is not the only thing that varies, and the other axis was found rather than
screened for. Every run is 36 slices at 3.3 mm, a 119 mm slab that does not cover a whole
head, and where the slab sits differs between subjects: four of the five miss 14-20 mm of
inferior brain that the template covers, while the fifth is close to complete. That is a
property of the acquisition, not of the registration, and it is why the centre-of-mass
offset is not comparable between subjects in absolute terms -- the panel's own chains sit
4-8 mm from the template brain centroid on a truncated run and under 1.5 mm on a complete
one. The scale is relative to each subject's own panel, so this cancels; the
`brain_in_place` cap, which is derived from that subject's worst accepted chain, is
correspondingly wider on a truncated run.

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

## Where zero credit sits

Full marks at the median accepted chain, the pass line at the weakest, and zero credit at
`worst + slack x (worst - median)`. Substituting the weakest accepted chain gives
`slack / (1 + slack)`, independent of the metric and of its values, so at `slack = 1.5` it
scores exactly 60 and `verdict_thresholds.acceptable = 60` means *no worse than the
weakest chain in the reference panel*.

The direct-to-template arms are not used as the anchor, although anchoring on the mistake
a task is about is the better construction where it works. It does not work here. On a
run whose slab covers the whole brain a direct 12-DOF affine is a plausible wrong answer,
and on the one subject of that kind it lands mid-scale. On a truncated run the same
command inflates the slab about 2.5x to fill the template, reaching roughly twice a
plausible brain volume and failing `brain_volume_plausible`. An anchor that far out
compresses the scale above it: measured against it, a reversed transform list -- a real
bug -- reached the pass mark on two of the four subjects. Against the slack anchor it is
`unacceptable` or `marginal` on all five, and every accepted chain is at or above 60. The
direct arms stay as scored candidates, where coming out invalid exercises the gates. The
figures are in the gated file.

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
  whatever brain extraction the agent used on the BOLD reference, and the slab the run
  covers. Both the volume-plausibility gate and the placement cap are wide for that
  reason, and both are set per subject.
