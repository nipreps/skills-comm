# Provenance — how this grader pack was built

Frozen references for **five subjects of the WMH Segmentation Challenge 2017** (clinical FLAIR,
native FLAIR space), spanning the challenge's three scanner sites: Amsterdam GE3T 100 and 114,
Singapore 52, Utrecht 33 and 39. White-matter hyperintensities of presumed vascular origin
(dementia / small-vessel axis).

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/clinical-wmh-segmentation/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

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

## Reference-leak exposure

The expert masks for these five cases are **publicly downloadable**, from the same
DataverseNL deposit and the same `api/access/datafile/<id>` endpoint the task prompt
tells the agent to use for the FLAIR. The deposit holds 170 `wmh.nii.gz` files covering
both the challenge's training and test halves, and all five graded cases are in the
training half, so one listing call reaches them. The mask ids even sit in the same range
as the image ids in the prompt.

Nothing can be done about that upstream, and the task is worth keeping: the data is open
precisely because the challenge intended it to be used. What the pack does instead is
refuse the answer. The prompt fetches the two input files by id rather than listing the
deposit, so the mask is not pulled in by accident, and the grader fails a submission that
reproduces the reference too exactly: `copy_suspect_dice = 0.995` trips the
`not_reference_copy` gate and the run is **invalid** with quality 0.

The threshold cannot catch an honest answer. Inter-observer agreement on this reference
is far below it -- that agreement is what the pass thresholds are derived from -- so no
submission produced by segmenting the image can reach 0.995.

