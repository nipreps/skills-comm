# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **ds001226 (BTC_preop) `sub-CON02` `ses-preop`,
`acq-AP` diffusion series**, tag `5.0.1`. Not re-derived at grade time.

## Subject and input

The AP series is 96 × 96 × 60 at 2.5 mm isotropic, 102 volumes, shells b = 0 / 700 / 1200 / 2800
with 6 b = 0 volumes. The graded space is the **diffusion grid itself**: a submission masks
whatever b0 it extracts, and every b0 shares that grid, so no resampling is implied.

The panel is run on the **mean of the 6 b0 volumes** (`dwiextract -bzero` then `mrmath mean`).
Averaging is conventional and gives the reference tools a less noisy image; a submission is *not*
required to average, because the grid is the same either way.

The agent is given the **raw** series. Only `acq-AP` is fetched — the dataset also ships a
reverse-phase-encode PA series, but this task is masking, not distortion correction.

## What this task actually tests

**Whether the b0 is prepared before it is masked.** On the raw series, every intensity-threshold
method loses the same anatomy — the cerebellum, both temporal poles and the brainstem — because
the inferior receive-coil bias field drops those structures below threshold:

| tool | largest contiguous core missed | verdict |
|---|---|---|
| SynthStrip, HD-BET | 0 cm³ | reference |
| AFNI `3dSkullStrip` | 0 cm³ | reference |
| MRtrix `dwi2mask` (raw) | 127 cm³ | **invalid** |
| FSL `bet -f 0.5` (default) | 411 cm³ | **invalid** |
| AFNI `3dAutomask` | 704 cm³ | **invalid** |

There are two correct routes, and the task admits both:

1. **Use a contrast-agnostic stripper** — SynthStrip, HD-BET or `3dSkullStrip` all reach the
   panel band directly on the raw mean b0.
2. **Preprocess, then mask.** `dwidenoise` + `dwibiascorrect ants` before `dwi2mask` takes it
   from 1399 cm³ with 127 cm³ of missing cerebellum (**invalid**) to 1495 cm³ with 11 cm³
   (**within_reference_variability**, quality 90.5, Dice 0.959). `dwi2mask` is not a bad tool; it is a
   bias-sensitive one, used here on input MRtrix does not intend it for.

That second row is why the task is fair rather than merely strict: the obvious DWI-native tool
*can* pass, and what it needs is the preprocessing its own documentation recommends.

## Panel curation

Eight tool configurations were run and curated by mutual coherence **and** visual inspection
(`qc_01_panel.png`, `qc_05_dwi2mask_gap.png`):

| tool | volume | verdict |
|---|---|---|
| **FreeSurfer SynthStrip** | 1603 cm³ | **reference** |
| **HD-BET** | 1541 cm³ | **reference** |
| **AFNI `3dSkullStrip`** | 1556 cm³ | **reference** |
| MRtrix `dwi2mask` (raw) | 1399 cm³ | dropped — loses cerebellum, temporal poles, brainstem |
| MRtrix `dwi2mask` (preprocessed) | 1495 cm³ | candidate; **passes**, quality 90.5 |
| AFNI `3dAutomask` | 838 cm³ | dropped — contours follow white matter |
| FSL `bet -f 0.5` / `-R` | 1280 / 1328 cm³ | dropped — inferior loss |
| FSL `bet -f 0.2` / `-f 0.3` | 1812 / 1744 cm³ | dropped — retains skull and scalp |

The kept three are mutually coherent at **pairwise Dice 0.948–0.967**. They are not a
deep-learning monoculture: `3dSkullStrip` is a classical morphological surface-expansion method
and agrees with the two learned tools to within Dice 0.948.

Note that `bet -f 0.2` and `-f 0.3` are numerically coherent with SynthStrip (Dice ≈ 0.93) yet
were still dropped: the overlap statistic cannot see that the extra volume is skull. That is why
the panel was curated visually as well as numerically.

### Why `dwi2mask` on the raw series is not a reference tool

An earlier revision of this pack kept it, on the reasoning that it is the canonical MRtrix DWI
tool and its tighter boundary was a legitimate convention. Inspection showed otherwise: the
127 cm³ it excludes is **the whole cerebellum, both temporal poles and the brainstem**
(`qc_05_dwi2mask_gap.png`), tissue the other three tools all include, with a mean b0 intensity of
174 against 34 outside the head. It is dropped anatomy, not a boundary convention.

Keeping it had a concrete cost: the cerebellum landed in the **margin** zone, which is never
scored, so a submission that discarded the cerebellum entirely would not have been penalised —
directly contradicting this task's own pass criterion ("brain retained including cerebellum and
brainstem"). Dropping it moves the cerebellum into the scored core, where it belongs, and
tightens τ from 12.5 mm to 5.59 mm, and tightens the focal core-loss cap by an order of
magnitude.

### Geometry

`3dSkullStrip` returns its output with obliquity stripped from the header — same shape, same
origin, same 2.5 mm zooms, rotation zeroed (max |Δaffine| = 0.371). The data is still
index-aligned to the input, so it is read on the native grid rather than resampled by the now
wrong affine. `score_brain_mask.py` implements this as `is_header_only_deoblique`.

**`grid.raw_affine` must be the affine as stored on disk, not the canonicalised one.** The scorer
compares it against a submission's *un-canonicalised* header, so a canonical affine silently
disables the deoblique path. It matters here and not in the T1w packs because this b0 is **LAS**
on disk — as diffusion and EPI data commonly are — whereas the T1w inputs behind the other packs
are already RAS, making raw and canonical identical for them. Scored against a rubric holding the
canonical affine, the real `3dSkullStrip` output is resampled by a wrong affine and drops to
**Dice 0.731**; with the raw affine it is read natively at **Dice 0.966**.

The reference tool `AFNI_SS` is the *binarised* `3dSkullStrip` output. The tool itself emits a
skull-stripped image with 7375 distinct intensities, so submitting that file unmodified fails the
`binary` gate — correctly, since the task asks for a binary mask.

## Calibration steps

1. **Consensus**: STAPLE (p ≥ 0.5) over the three reference tools → `consensus_mask.nii.gz`,
   **1576.9 cm³**.
2. **Zones** from the vote fraction → `consensus_zones.nii.gz` (0 = background, 1 = margin,
   2 = core); core **1458.7 cm³**, margin **206.4 cm³**. Intersecting masks leaves specks and
   pinholes that are artefacts rather than anatomy, so the core is hole-filled and reduced to its
   largest component — it is one solid component with zero enclosed holes.
3. **τ** = 95th percentile of pairwise surface disagreement among the reference tools =
   **5.59 mm** (2.24 voxels).
4. **Envelope** by leave-one-tool-out — hold out each reference tool, rebuild the consensus from
   the other two, score the held-out tool against it → per-metric median (full marks) and worst
   (zero credit).
5. **Gate caps**: `focal_max_cm3` = max(1.5 × worst held-out focal miss, 5 cm³ floor) = **5.0–12.9 cm³**
   across the five subjects, the miss and the submission's loss both measured as the largest
   component surviving a max(1.5 mm, one voxel) shave, one voxel on this grid;
   `focal_bg_max_cm3` = **40 cm³** (fixed policy, measured the same way);
   `plausible_volume_cm3` =
   **[1020, 2290]** cm³, which rejects the 838 cm³ `3dAutomask` outright.

### Leave-one-tool-out

| held out | Dice | NSD | core recall |
|---|---|---|---|
| SynthStrip | 0.970 | 0.997 | 0.994 |
| HD-BET | 0.958 | 0.986 | 0.969 |
| AFNI 3dSkullStrip | 0.953 | 0.940 | 0.959 |

## Validation

### Every candidate scored through the frozen pack

| tool | role | verdict | quality | Dice | gates failed |
|---|---|---|---|---|---|
| SynthStrip | reference | within_reference_variability | 100.0 | 0.986 | — |
| HD-BET | reference | within_reference_variability | 100.0 | 0.981 | — |
| AFNI 3dSkullStrip | reference | within_reference_variability | 92.1 | 0.967 | — |
| **dwi2mask, preprocessed** | candidate | **within_reference_variability** | **90.5** | 0.959 | — |
| dwi2mask, raw | candidate | **invalid** | 0 | 0.924 | core loss, focal core loss |
| BET -f 0.2 / -f 0.3 | candidate | **invalid** | 0 | 0.93 | focal bg inclusion |
| BET -f 0.5 / -R | candidate | **invalid** | 0 | 0.79 | core loss, focal core loss, focal bg |
| AFNI 3dAutomask | candidate | **invalid** | 0 | 0.670 | volume, core loss, focal core loss |

Dice alone would not separate these: `bet -f 0.2` reaches Dice 0.927 while retaining skull,
higher than raw `dwi2mask` at 0.924 which loses the cerebellum. The zone gates are what tell them
apart, and they name the failure.

### Perturbing the consensus

| perturbation | verdict | quality | Dice |
|---|---|---|---|
| self | within_reference_variability | 100.0 | 1.000 |
| erode 1 vox | acceptable | 73.9 | 0.950 |
| dilate 1 vox | acceptable | 71.4 | 0.953 |
| erode 2 vox | **invalid** | 0 | 0.898 |
| dilate 2 vox | **invalid** | 0 | 0.908 |
| shift 5 mm | **invalid** | 0 | 0.940 |
| empty | **invalid** | 0 | 0.000 |

Symmetric within a voxel, and both two-voxel failures are caught — erosion on core loss,
dilation on retained background.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Reference data

`reference/consensus_mask.nii.gz` and `consensus_zones.nii.gz` are **not** in git — they belong
on the Hugging Face Hub (`neurodeskorg/skills-comm-ground-truth`,
`diffusion_gt/diffusion-brain-mask/<subject>/`). Fetch them before grading; see
`reference/README.md`. Everything else the grader needs is in `rubric.json`.
