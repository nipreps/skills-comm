# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on the benchmark subject **CEREBRUM-7T `ds003642`,
`sub-025` `ses-003`** (7T MP2RAGE, 0.63 mm isotropic, native T1w space). Not re-derived at grade time.

## Subject and inputs

CEREBRUM-7T provides MP2RAGE INV1 / INV2 / UNI (BIDS `T1w`) at 0.63 mm on a 7T scanner. The graded
input is the **UNI** image. Its background is salt-and-pepper noise (≈ 80 % of background voxels are
"bright"); the **INV2** magnitude is clean outside the head and is used only to build the reference's
cleaned image.

## Cleaned UNI (reference construction only)

To run the tool panel coherently, the UNI background is zeroed with an INV2-derived head mask
(threshold → largest component → close → fill → light dilation, keeping skull/scalp). This cleaned
image is used **only to build the reference**; submissions are graded on whatever they produce from
the raw dataset, and the robust tools do not require the cleaning (see below).

## Panel curation

Three independent algorithms, each run on the image its assumptions fit: **HD-BET** on the cleaned
UNI, **SynthStrip `-b -2`** on the cleaned UNI, **ANTs** on INV2.

- **AFNI `3dSkullStrip` and FSL BET are excluded.** Both expand a surface and need a real skull
  edge, which the MP2RAGE UNI does not provide. Against the dataset's own CEREBRUM7T labels AFNI
  retains 32.8–86.4 % of the cerebellum and returns the mask in 5–10 pieces; BET retains 0.0–0.1 %.
  No shrink factor or fractional-intensity threshold recovers either. Both remain scored
  **candidates** and come out `invalid`, which validates the gates.
- **ANTs runs on INV2, not the UNI.** INV2 is a plain magnitude image with ordinary tissue
  contrast: ANTs keeps 96.5 % of the cerebellum on the UNI against 99.5 % on INV2. INV2 shares the
  UNI's grid and affine, so no resampling is involved.
- **SynthStrip uses `-b -2`, not `--no-csf`.** Both pull the mask off the dura, but `--no-csf`
  also removes the interior cisterns the other two keep — 3.06 of 3.1 cm³ of sub-075's interior
  margin, against 0.00 for HD-BET and ANTs.

`decision_7t_panel.ipynb` in the build directory carries the measurements behind each choice.

## Difficulty is tool choice, not preprocessing

Scored on the raw (uncleaned) UNI against this pack:

| tool (raw UNI)        | verdict                      | note                                      |
|-----------------------|------------------------------|-------------------------------------------|
| naive FSL `bet`       | **invalid** (557 cm³)        | under-extracts; fails volume + core gates |
| FSL `bet -R`          | **invalid**                  | 390–477 cm³ of solid core gone            |
| AFNI `3dSkullStrip`   | **invalid**                  | 13–59 cm³ of solid core gone              |
| SynthStrip, defaults  | marginal (33.8–55.5)         | complete, but carries dura                |
| HD-BET, defaults      | within_reference_variability (97.2–100) | robust to the noise + 7T contrast |

`bet` fails on the cleaned image too (~546 cm³), so the failure is intrinsic to the tool at 7T, not
a missed denoising step.

## Calibration steps

1. **Geometry harmonisation** onto the reference grid (GRID_TOOL = HD-BET). A header-only
   deoblique, as AFNI writes, is read on the native grid; the grader carries `grid.raw_shape` and
   `grid.raw_affine` so it recognises the same case in a submission rather than failing it.
2. **STAPLE consensus** of the three reference tools → binary consensus
   (`consensus_mask.nii.gz`, 1165–1227 cm³; core 1109–1131 /
   margin 162–193 across the three subjects).
3. **Zones** from the agreement fraction → `consensus_zones.nii.gz` (0 = background, 1 = margin, 2 = core).
4. **τ** = 95th percentile of pairwise surface disagreement, 3.85–4.15 mm. The
   panel is tight because each member runs on an image that suits it.
5. **Envelope** by leave-one-tool-out → per-metric median (full marks) / worst (pass line).
6. **Gate caps:** `focal_max_cm3` (5.0 cm³ here) for localised core loss, LOTO-calibrated with a
   floor and measured as the largest component surviving a max(1.5 mm, one voxel) shave; and
   `focal_bg_max_cm3` = 40 cm³ (fixed), measured the same way. At this task's 0.63 mm voxels a
   one-voxel erosion asks for only 1.9 mm of thickness, which a dura rind clears, so it is the
   millimetre floor rather than the voxel floor that binds here on both gates.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

The `reference/` NIfTIs are **not** in git — they live on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`structural_gt/structural-brain-extraction-7t/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.

## Caveats

- **τ is wide.** The quality score is permissive by design here; the gates do the discrimination.
