# Provenance — how this grader pack was built

Frozen reference for **open_ms_data cross-sectional `patient01`** (Ljubljana MS database, 3 T
FLAIR + T1w + T2w, co-registered and resampled to 1 mm isotropic, 154 × 240 × 240). Multiple
sclerosis white-matter lesions, native FLAIR space of the supplied images.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/clinical-ms-lesion-segmentation/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Geometry harmonisation

Upstream, `consensus_gt.nii.gz` carries a header translated by up to **0.4 mm** from `FLAIR.nii.gz`,
`T1W.nii.gz` and `brainmask.nii.gz`, which are mutually identical. The offset is sub-voxel and
constant, the shapes are identical, and the mask overlays the FLAIR hyperintensities exactly in
index space (see `qc_00_lesion.png`) — a bookkeeping slip in the upstream resampling, not a real
transform. The pack therefore takes the **voxel data of the published consensus mask on the header
of the FLAIR the task hands out**, so a submission left in the input's own space passes the
`native_grid` gate. Without this step every submission would fail that gate.

## Reference-leak exposure

The upstream repository stores `consensus_gt.nii.gz` **in the same directory as the images**, in all
three variants (`raw/`, `coregistered/`, `coregistered_resampled/`). The task prompt therefore
fetches the three input files individually by URL rather than cloning the repository, and the pack
sets `copy_suspect_dice = 0.995`: a submission that reproduces the reference too exactly is reported
as `suspected_reference_copy` in the scorer output. That flag never changes the verdict — the
harness decides what to do with a flagged run.

## Reference data

`reference/lesion_mask.nii.gz` is **not** in git — it lives on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`clinical_gt/clinical-ms-lesion-segmentation/<subject>/`). Fetch it before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`. The Ljubljana database
is CC-BY, so the mask is redistributable with attribution.

## References

1. Lesjak Ž, Galimzianova A, Koren A, Lukin M, Pernuš F, Likar B, Špiclin Ž. A Novel Public MR Image
   Dataset of Multiple Sclerosis Patients With Lesion Segmentations Based on Multi-rater Consensus.
   *Neuroinformatics* 16:51–63, 2018. doi:10.1007/s12021-017-9348-7
2. Wiltgen T, McGinnis J, Schlaeger S, et al. LST-AI: A deep learning ensemble for accurate MS
   lesion segmentation. *NeuroImage: Clinical* 42:103611, 2024. doi:10.1016/j.nicl.2024.103611
