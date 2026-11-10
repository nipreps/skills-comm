# Provenance — how this grader pack was built

Frozen references for **five patients of open_ms_data cross-sectional** (Ljubljana MS database, 3 T
FLAIR + T1w + T2w, co-registered and resampled to 1 mm isotropic, 154 × 240 × 240). Multiple
sclerosis white-matter lesions, native FLAIR space of the supplied images.

## How the reference was built

It was not built here. Three experts segmented each patient independently and the dataset
publishes their consensus; that published mask is the reference, unchanged except for the
header fix below. No tool was run to produce it, and there is no panel.

What the raters did, and the per-subject figures the grader merges at scoring time, are in
`calibration/clinical-ms-lesion-segmentation/PROVENANCE.md` inside the gated reference
dataset [`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).
It is gated because the mask is the answer to the task.

## Why the reference mask is re-headered

A NIfTI file carries both the voxels and a header saying where those voxels sit in space.
Upstream, the consensus mask and the three images it was drawn on disagree about the
second part: the mask's header is shifted by up to 0.4 mm relative to `FLAIR.nii.gz`,
`T1W.nii.gz` and `brainmask.nii.gz`, which all agree with each other.

That shift is not a real difference. It is smaller than one voxel, it is the same
everywhere, the volumes have identical shapes, and the mask sits exactly on the FLAIR
hyperintensities when the two are overlaid by voxel index (`qc_00_lesion.png`). It is a
bookkeeping slip in the upstream resampling.

It matters because the grader requires a submission to be on the grid of the image it was
given — the `native_grid` gate. An agent segments `FLAIR.nii.gz` and inherits that
header, so if the reference kept the shifted one, every submission would be compared
against a mask the grader considers to be on a different grid, and all of them would fail
the gate.

The pack therefore stores the published mask's voxels on the FLAIR's header. Nothing is
resampled and no voxel changes value; only the spatial metadata is made consistent with
the image the task hands out.

## Reference-leak exposure

The upstream repository stores `consensus_gt.nii.gz` **in the same directory as the images**, in
all three variants (`raw/`, `coregistered/`, `coregistered_resampled/`). An agent that clones the
repository, or finds the file by other means, could submit the reference as its own result.

Two things stand against that. The task prompt fetches the three input files individually by URL
rather than cloning, so the mask is not pulled in by accident. And the grader refuses a submission
that reproduces the reference too exactly: `copy_suspect_dice = 0.995` fails the
`not_reference_copy` gate, making the run **invalid** with quality 0.

The threshold is far above anything segmentation reaches on this reference — the best published
method sits at Dice 0.74, and the raters themselves do not agree to 0.995 — so it cannot catch an
honest answer, however good. `suspected_reference_copy` is still reported in the result so the
reason is visible rather than only the gate name.

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
