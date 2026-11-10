# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 3 subjects of **CEREBRUM-7T `ds003642`** (7T MP2RAGE, 0.63 mm isotropic, native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-tissue-segmentation-7t/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Why consensus, not a single truth

Every tissue/structure segmenter draws slightly different boundaries, especially at the fuzzy
partial-volume interfaces (GM↔WM, GM↔CSF). Grading against one tool's output would bake in that
tool's idiosyncrasies. Instead the reference is a **majority vote of the panel's segmentations**, split
into per-class zones — unanimous core (must match) and majority boundary (partial-volume, softly
scored) — and only the calibrated envelope decides pass/fail.

## Label legend

`1=GM  2=basal ganglia  3=WM  4=ventricles/CSF  5=cerebellum  6=brainstem` (0 = background). This
is the output contract, so it is stated in the task prompt too.

The integer mapping is not published by CEREBRUM-7T. It was pinned rather than assumed, from each
class's volume and its median intensity on the UNI, which order the tissues unambiguously at 7T.
The measurements behind the pinning are in the gated provenance.

## Consensus and calibration

The segmentations shipped with CEREBRUM-7T are fused by per-voxel majority vote into a six-class
label map, with a companion map recording how many sources agreed on each voxel: unanimous voxels
form the core, which is scored, and majority-only voxels form the boundary, which is not. The
per-class surface tolerance and the pass and full-mark anchors are then taken from the sources'
own leave-one-out spread, so each class is judged against how well they agree on that class
rather than against a fixed number.

Which sources, their agreement, the class volumes and every calibrated value are in
`calibration/structural-tissue-segmentation-7t/PROVENANCE.md` in the gated reference dataset.

## Scoring

Per class: Dice, NSD (within τ), core-recall; each mapped through its envelope with `slack` 1.5.
Overall quality = mean of the six class qualities. Gates → `invalid`: `valid_labels`, `native_grid`,
`no_class_collapse` (each class recovers ≥ 50 % of its unanimous core).

## Reference data

`reference/consensus_seg.nii.gz` + `consensus_agreement.nii.gz` are on the Hugging Face Hub
(`neurodeskorg/skills-comm-ground-truth`, `structural_gt/structural-tissue-segmentation-7t/<subject>/`). Fetch them before grading;
see `reference/README.md`. Everything else is in `rubric.json`.

## Caveats

- **Six-structure parcellation, not classic 3-class GM/WM/CSF.** The classes follow the CEREBRUM-7T
  protocol (basal ganglia, cerebellum, brainstem are their own labels; CSF is ventricular). An agent
  must output this exact legend.
- **The panel are DL/atlas segmentations, not a manual gold standard** — a curated consensus, not
  ground truth in the strict sense. Two of three are FreeSurfer versions, so the consensus leans
  toward one lineage; the 7T-specialised member adds independent signal.
