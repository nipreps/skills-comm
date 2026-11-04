# Provenance — how this grader pack was built

Frozen references for **five subjects of the Aphasia Recovery Cohort (ARC), OpenNeuro `ds004884`**
(chronic left-MCA stroke, native T1w space).

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/clinical-stroke-lesion-segmentation/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Reference data

`lesion_mask.nii.gz` is on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`clinical_gt/clinical-stroke-lesion-segmentation/<subject>/`). Fetch before grading; see
`reference/README.md`.

## Caveats

- **One large single lesion.** The lesion-wise F1 machinery applies to multi-focal cases, but the
  thresholds were not tuned on one.
- **Registration error** from the T2w→T1w mapping is possible (small; intra-session, rigid, 1 mm).
- **Fixed thresholds** are a literature prior [1–3], not this subject's inter-rater spread (ARC ships
  one tracing per subject). A multi-rater subset would let the tolerance be data-derived. The prior is
  on-population — chronic stroke, T1w, manual tracing — but general, not this subject's own spread.

## References

1. Tavenner BP, Donnelly MR, Barisano G, Liew S-L. "A standardized protocol for manually segmenting
   stroke lesions on high-resolution T1-weighted MR images." *Frontiers in Neuroimaging* 1:1098604,
   2023. doi:10.3389/fnimg.2022.1098604. — inter-rater manual-tracing **Dice = 0.727** (six trained
   tracers, high-res 3D T1w). Sets the full-marks 0.70 ceiling.
2. Liew S-L, Tavenner BP, Donnelly MR, et al. "A large, curated, open-source stroke neuroimaging
   dataset to improve lesion segmentation algorithms" (ATLAS v2.0). *Scientific Data* 9:320, 2022.
   doi:10.1038/s41597-022-01401-7. — canonical **chronic-stroke, T1w** manual-lesion dataset; the
   population this prior is drawn from. (Reports automated methods scoring Dice < 0.7.)
3. Deb P, Baru LB, Dadi K, S BR. "BeSt-LeS: Benchmarking Stroke Lesion Segmentation using Deep
   Supervision." *MICCAI BrainLes* 2023, arXiv:2310.07060. — automated **state-of-the-art on ATLAS
   v2.0, Dice ≈ 0.50–0.58**. The 0.50 pass line sits at this automated floor.
