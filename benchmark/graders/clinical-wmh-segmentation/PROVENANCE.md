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

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

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
