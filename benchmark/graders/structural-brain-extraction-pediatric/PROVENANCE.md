# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **ds000228 `sub-pixar017`** (~3.6 yo, native T1w space).
Not re-derived at grade time.

## Subject selection

ds000228 (Richardson, "Development of the social brain") — children + adults. An earlier pick,
**sub-pixar009, was rejected**: its T1w has a field-of-view truncation (a planar zero-cut through the right
side of the brain — not defacing; ~6-8 % of the brain surface sat on the cut). Candidates were screened with
an FOV-completeness metric (SynthStrip mask, % of brain surface adjacent to zero-data); **sub-pixar017** was
the cleanest (0.2 %) with full coverage.

## Inputs and panel

Four tools were run on the T1w and were all mutually coherent (pairwise Dice ~0.95-0.96, volumes 1059-1173 cm³):

- **HD-BET** (deep learning)
- **AFNI** `3dSkullStrip` (mask taken from the skull-stripped brain, solidified onto the native grid)
- **SynthStrip** (deep learning; the loosest — keeps a thin outer CSF rim, 95 % of its surplus is CSF)
- **FSL BET** with `-R` (robust centre)

**ANTs was excluded** — the adult OASIS template does not fit a 3.6-yo brain.

## Calibration steps

1. Geometry harmonisation onto the reference grid (AFNI's header-only deoblique is read on the native grid;
   the grader carries `grid.raw_affine` to detect the same case in a submission).
2. **STAPLE consensus** of the four tools → binary consensus (`consensus_mask.nii.gz`).
3. **Zones** from the agreement fraction → `consensus_zones.nii.gz` (0=background, 1=margin, 2=core).
4. **τ** = 95th percentile of pairwise surface disagreement (≈ 4.5 mm).
5. **Envelope** by leave-one-tool-out → per-metric median (full marks) / worst (pass line).
6. **Gate caps:** `focal_max_cm3` (5.0 cm³ here) for localised core loss, LOTO-calibrated with a
   floor, both sides measured as the largest component surviving a max(1.5 mm, one voxel) shave so
   a uniformly tighter boundary is not read as a missing structure; and `focal_bg_max_cm3` = 40 cm³,
   measured the same way
   (fixed) for localised background inclusion.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-pediatric/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **Consensus leans on the tighter tools.** SynthStrip's CSF rim lands in the margin, not the core.
