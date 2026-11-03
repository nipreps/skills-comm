# Provenance — how this grader pack was built

Frozen references for **five subjects of the WMH Segmentation Challenge 2017** (clinical FLAIR,
native FLAIR space), spanning the challenge's three scanner sites: Amsterdam GE3T 100 and 114,
Singapore 52, Utrecht 33 and 39. White-matter hyperintensities of presumed vascular origin
(dementia / small-vessel axis).

## Ground truth

Each `lesion_mask.nii.gz` is that subject's **primary expert WMH mask** (observers O1/O2 per the challenge's reference
standard [1], STRIVE-compliant), binarised to WMH (label 1; the dataset's label 2 "other pathology" is not
present for this subject). Native FLAIR space. Volumes and focus counts per subject are in the table below.

## Thresholds are data-derived from inter-rater agreement

This section is drawn as panel 1 of
[`wmh_grading.png`](wmh_grading.png) (linked from the README).

The WMH Challenge [1] ships two additional raters (O3, O4) on the training subjects. Scoring each
against the primary gives a *measured* envelope rather than a literature guess:

Each subject carries its own envelope, measured from its own two raters:

| subject | O3 Dice | O4 Dice | Dice full | Dice pass | F1 full | vol full |
|---|---|---|---|---|---|---|
| `Amsterdam_GE3T_100` | 0.7744 | 0.7921 | 0.783 | 0.574 | 0.835 | 8.6 |
| `Amsterdam_GE3T_114` | 0.8263 | 0.8494 | 0.838 | 0.626 | 0.907 | 3.8 |
| `Singapore_52` | 0.7194 | 0.8029 | 0.761 | 0.519 | 0.571 | 25.6 |
| `Utrecht_33` | 0.7437 | 0.7665 | 0.755 | 0.544 | 0.759 | 15.6 |
| `Utrecht_39` | 0.9061 | 0.9017 | 0.904 | 0.702 | 0.801 | 3.0 |

Rater agreement rises with lesion load, so the envelope does too — which is why subjects
below a mean agreement of 0.70 are excluded: their thresholds would ask almost nothing of a
submission. `subjects.tsv` in the build directory records every screened subject and the
reason it was or was not used.

Envelope: **full marks = mean rater-vs-primary** (as good as another expert); **zero point = a fixed
margin**: 0.20 below the weaker rater for Dice, 0.25 below the weaker rater for F1, and 40 points
above the rater mean for volume error.

The values above are what that rule produces per subject.

Weights: Dice 0.40, lesion-wise F1 0.40, volume error 0.20 — F1 raised to parity with Dice because WMH
are many small foci where detection, not just boundary overlap, is the point.

## Validation

Against the pack: primary self → `within_reference_variability` (q100); **O4 → `within_reference_variability`** and **O3 →
`acceptable` (q90)** — the two real raters land at "as good as another expert"; dilate the mask by 2
voxels → `marginal` (Dice 0.24, +636 % volume — tiny lesions are unforgiving); erode by 1 →
`unacceptable`; empty → `invalid`.

## Data access (open, agent-runnable)

Images: DataverseNL DOI `10.34894/AECRSD`, open Dataverse access API (`curl .../api/access/datafile/<id>`,
no auth/DUA). Per-subject file ids are listed in `subject_file_ids.json` in the build directory, derived from
the dataset's own file listing. The expert masks (primary, O3, O4) build this pack and the
envelope; only the FLAIR is given to the agent.

## Caveats

- **FLAIR is anisotropic** (~1.2 × 1.0 × 3.0 mm, 2D multi-slice) — realistic clinical WMH data.
- **Two extra raters, not a full distribution** — the envelope uses O3/O4 vs primary; more raters
  would tighten it.
- License CC-BY-NC-4.0 (non-commercial), fine for a benchmark.

## References

Thresholds here are **data-derived** (O3/O4 vs primary), not a literature prior — this reference is
*dataset / protocol provenance*, crediting the source of the reference standard and the multi-observer
masks the envelope is built on.

1. H. J. Kuijf, J. M. Biesbroek, J. de Bresser, et al., "Standardized Assessment of Automatic
   Segmentation of White Matter Hyperintensities and Results of the WMH Segmentation Challenge,"
   *IEEE Trans. Med. Imaging* 38(11):2556–2568, 2019. doi:10.1109/TMI.2019.2905770.
