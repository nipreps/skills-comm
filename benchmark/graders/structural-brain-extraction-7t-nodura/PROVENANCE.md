# Provenance — how this grader pack was calibrated

Frozen output of a one-time calibration on **CEREBRUM-7T `ds003642`, `sub-025` `ses-003`** (7T
MP2RAGE, 0.63 mm isotropic, native T1w space) — the same subject as `structural-brain-extraction-7t`,
with an explicit **"remove the dura"** prompt and an added over-inclusion gate. Not re-derived at
grade time.

## What this pack adds over `-7t`

The consensus reference (`consensus_mask.nii.gz`, `consensus_zones.nii.gz`) and every consensus-side
number in `rubric.json` are identical to the `-7t` pack — the brain-keeping requirement is the same.
This pack adds:

- **`reference/dura_envelope.nii.gz`** — the dura-out pial envelope.
- **`dura_max_cm3` = 30.0** — the one-sided over-inclusion cap.
- **`no_dura_inclusion`** in the gate list.

## The dura envelope

A "no dura" requirement cannot be graded from a tool consensus: skull-strippers disagree on the dura,
so a consensus blurs it into the (unscored) margin. It needs a **dura-out reference**. CEREBRUM-7T
ships four whole-brain tissue segmentations (CEREBRUM7T, FreeSurfer v6/v7, nighres), all dura-out by
construction.

Envelope construction:

1. **Union** of the four segmentations. Union (not majority) is used because the cerebrum-focused
   segmentations under-cover the cerebellum + brainstem; FreeSurfer supplies them, and the union
   keeps them. (Majority-of-4 and FreeSurfer-alone both cut across the cerebellum, which would
   wrongly flag the inferior brain of a good mask as "dura".)
2. **Sulci-fill** by a 5-voxel (3.1 mm) ball closing + hole-fill + largest component, so the
   boundary is the outer **pial** surface. This makes the gate penalise dura (outside the pial
   envelope), **not** sulcal CSF (inside it). Volume ≈ 1202 cm³.

The 3.1 mm radius was chosen from a sweep: 1.9 mm leaves some sulci open (risking false dura flags),
4.4 mm starts bulging toward the dura. 3.1 mm bridges the sulci while hugging the pial surface.

## The cap

`dura_over_env_cm3 = volume(mask AND NOT envelope)` measured on the subject's tools:

| mask                      | over-envelope | reading                           |
|---------------------------|---------------|-----------------------------------|
| the consensus reference   | 15.2–33.7 cm³   | the floor the cap must clear      |
| HD-BET (panel)            | 7.3–17.7 cm³   | small inferior brainstem nub      |
| SynthStrip `-b -2` (panel)| 28.0–55.0 cm³  | border pulled in, most dura gone  |
| ANTs INV2 (panel)         | 33.2–73.1 cm³  | template fit carries a dura rim   |
| HD-BET, defaults          | 5.2–15.9 cm³    | dura-out                          |
| SynthStrip, defaults      | 117.7–194.8 cm³ | thick CSF + dura rim             |

**`dura_max_cm3` = 50 cm³ (fixed)** sits between the reference's own worst over-envelope
volume (33.7 cm³, which a perfect answer must clear) and the smallest
rim-retaining failure (117.7 cm³). It is a *fixed* cap, not
LOTO-calibrated: the panel is not the target here. The task asks for a mask **tighter** than the
panel consensus, so calibrating the cap from the panel's own spread would defeat it.

**Two panel members fail this gate** — ANTs INV2 on sub-025 and sub-045, SynthStrip `-b -2` on
sub-045. That is a consequence of the above rather than a miscalibration: both carry a dura rim,
which is exactly what the prompt asks a submission not to do, and the STAPLE consensus they
produce passes comfortably. It does mean this gate, alone among the gates here, is not satisfied
by every tool that built the reference — worth knowing before reading a failure on it.

## Caveats

- **HD-BET's 7.3–17.7 cm³ is mostly an inferior
  brainstem/cord nub, not dura.** The cap tolerates it. A stricter reading of "no dura" would tighten
  the cap, at the risk of failing an otherwise good mask.
- **The envelope leans on the shipped segmentations.** It is a curated dura-out reference, not a
  hand-drawn gold standard; a fully manual dura label would be more rigorous.
