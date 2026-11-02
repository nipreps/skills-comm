# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on the benchmark subject
**MR-ART `ds004173`, `sub-000103`, `acq-headmotion2`** (native T1w space). Not re-derived at
grade time.

## Subject

MR-ART pairs a motion-free scan with two motion-corrupted scans of the same subject. The graded
input is the **high-motion** scan (`acq-headmotion2`, quality score 3/3 — the worst tier);
`acq-standard` is the clean control.

## Inputs and panel curation

Five tools were run on the motion scan (FSL BET, HD-BET, AFNI `3dSkullStrip`, SynthStrip, ANTs).
On this motion scan they diverge and partly fail, so the reference panel was curated using the
coherence check:

- **Kept (reference): HD-BET, AFNI, SynthStrip** — mutually coherent (pairwise Dice 0.94–0.96).
- **Dropped: ANTs** — coherence outlier (mean pairwise Dice 0.81 vs 0.90+); alone it blew τ to
  17.5 mm and pushed the margin to 53 % of the volume.
- **Dropped: FSL BET** — extended into the neck/spinal cord ventrally (~98 cm³ of retained
  background), the "too much left at the bottom" failure.

ANTs and BET remain as scored **candidates** (they come out `invalid`), which validates the grader.

## Calibration steps

1. **Geometry harmonisation** onto the reference grid; AFNI's header-only deoblique is read on the
   native grid (the grader carries `grid.raw_affine` to detect the same case in a submission).
2. **STAPLE consensus** of the three reference tools → binary consensus (`consensus_mask.nii.gz`).
3. **Zones** from the agreement fraction → `consensus_zones.nii.gz` (0=background, 1=margin, 2=core).
4. **τ** = 95th percentile of pairwise surface disagreement among the three tools (≈ 5.7 mm).
5. **Envelope** by leave-one-tool-out → per-metric median (full marks) / worst (pass line).
6. **Gate caps:** `focal_max_cm3` (5.0–14.5 cm³ here) for localised core loss, LOTO-calibrated with a
   floor, both sides measured as the largest component surviving a max(1.5 mm, one voxel) shave;
   `focal_bg_max_cm3` is measured the same way; and
   **`focal_bg_max_cm3` = 40 cm³ (fixed)** for localised background inclusion. The background cap is
   *not* LOTO-calibrated: a competent tool retains ~0 contiguous background by construction, and with
   a small panel leave-one-out would be fooled by the loosest tool's dura.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are **not** stored in git — they live on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-motion/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **Curating the panel uses judgement.** ANTs is dropped objectively (coherence); BET is dropped for
  neck over-inclusion.
- **Consensus leans on HD-BET.** The core ≈ HD-BET (the tightest, most trusted tool here). A more
  rigorous alternative is a clean-scan-derived truth (extract from `acq-standard`, register onto the
  motion scan), which does not depend on how tools behave under motion.
