# Provenance — how this grader pack was built

Frozen reference for **Aphasia Recovery Cohort (ARC), OpenNeuro `ds004884`, `sub-M2191` `ses-681`**
(chronic left-MCA stroke, native T1w space).

## Ground truth

The reference `lesion_mask.nii.gz` is the dataset's **expert manual lesion tracing** — drawn in T2w
space by trained raters — rigid-registered (FSL FLIRT, 6 DOF, nearest-neighbour) into the native T1w
space so both stroke tasks share one space. Volume 82.8 cm³. This is a genuine gold standard, not a
tool consensus (see the README for why lesion segmentation cannot use a consensus).

## Thresholds are fixed, not calibrated by LOTO

A single subject gives no leave-one-tool-out envelope, and a tool-consensus would be untrustworthy for
lesions. So the pass/fail lines are **fixed from the literature** [1–3]:

| metric | full marks | pass line | basis |
|---|---|---|---|
| Dice | 0.70 | 0.50 | full = manual-tracing **inter-rater ceiling** on T1w (Dice 0.727 [1]); pass ≈ **automated SOTA** on ATLAS v2.0 (Dice ≈ 0.50–0.58 [3]) |
| lesion-wise F1 | 1.0 | 0.5 | detect the lesion instance(s) |
| abs. volume error | 15 % | 50 % | gross size plausibility |

Weights: Dice 0.7, lesion-wise F1 0.1, volume error 0.2. A connected component counts as detected
when a prediction overlaps ≥ 10 % of it. F1 was lowered from 0.3 and the weight given to Dice:
every subject here carries exactly one expert lesion, so detection F1 can only report "found it"
or "did not", and at 0.3 a single stray voxel cost about 12 quality points because the metric
counts a one-voxel component as a whole false lesion. That is a policy choice, not a calibrated
threshold — with one expert tracing there is no inter-rater disagreement to derive one from.

## Validation

Perturbing the expert mask against the pack: self → `within_reference_variability` (q100, Dice 1.0); dilated 3
vox → `acceptable` (q80, Dice 0.74, volume +72 %); eroded 4 vox → `unacceptable` (Dice 0.48, F1 0.40);
empty → `invalid` (nonempty gate).

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
