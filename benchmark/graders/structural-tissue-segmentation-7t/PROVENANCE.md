# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **CEREBRUM-7T `ds003642`, `sub-025` `ses-003`** (7T
MP2RAGE, 0.63 mm isotropic, native T1w space). Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-tissue-segmentation-7t/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

That material sits with the reference because it describes the answer: during
one benchmark wave, agent runs retrieved this file from GitHub and one rebuilt
the panel consensus from it. Access is granted on request.

## Why consensus, not a single truth

Every tissue/structure segmenter draws slightly different boundaries, especially at the fuzzy
partial-volume interfaces (GM↔WM, GM↔CSF). Grading against one tool's output would bake in that
tool's idiosyncrasies. Instead the reference is a **majority vote of the panel's segmentations**, split
into per-class zones — unanimous core (must match) and majority boundary (partial-volume, softly
scored) — and only the calibrated envelope decides pass/fail.

## Label legend (confirmed by intensity on the UNI)

`1=GM  2=basal ganglia  3=WM  4=ventricles/CSF  5=cerebellum  6=brainstem` (0 = background). The
integer mapping is not published by CEREBRUM-7T; it was pinned by class volume + median UNI
intensity (WM brightest 2564, basal ganglia 2187, GM 1407, ventricles darkest 691).

## Consensus and calibration

1. **Fuse** the three tools by per-voxel majority vote (≥ 2/3) over the 7 classes →
   `consensus_seg.nii.gz`; `consensus_agreement.nii.gz` records the winning vote count (3 = unanimous
   core, 2 = majority boundary). Three-way ties are 1.4 cm³ total.
2. **Class volumes (cm³):** GM 485, basal ganglia 42, WM 360, ventricles 10, cerebellum 76,
   brainstem 14. Unanimous-core fraction ranges 67 % (GM — fuzziest) to 87 % (WM — tightest).
3. **Per-class τ** = 95th percentile of pairwise surface disagreement among the three tools (mm):
   GM 1.77, basal ganglia 1.77, WM 1.25, ventricles 1.53, **cerebellum 7.56** (widest — the
   cerebellar boundary is genuinely fuzzy at this resolution), brainstem 3.12.
4. **Envelope** by leave-one-tool-out → per-class median (full marks) / worst (pass line). LOTO Dice
   median/worst: GM 0.785/0.760, basal ganglia 0.881/0.880, WM 0.905/0.901, ventricles 0.816/0.805,
   cerebellum 0.855/0.741, brainstem 0.858/0.836.

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
