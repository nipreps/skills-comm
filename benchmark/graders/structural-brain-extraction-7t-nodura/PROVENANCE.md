# Provenance — how this grader pack was calibrated

Frozen per-subject calibrations across 3 subjects of **CEREBRUM-7T `ds003642`** (7T MP2RAGE, 0.63 mm isotropic, native T1w space) — with an explicit **"remove the dura"** prompt and an added over-inclusion gate. Not re-derived at grade time.

## How the reference was built

The panel or raters behind this reference, the calibration steps, the surface
tolerance, the calibrated caps and the reference volumes are documented in
`calibration/structural-brain-extraction-7t-nodura/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth), with the per-subject
calibration the grader merges at scoring time.

It is gated so that a submission cannot reproduce the reference instead of
solving the task.

## Scoring scale and weights

The subscore mapping, what `acceptable = 60` means (a submission as good as the weakest
panel tool), the `slack` relationship behind it, and the weight rationale with its
sensitivity analysis are documented once in
[`../structural-brain-extraction/PROVENANCE.md`](../structural-brain-extraction/PROVENANCE.md)
and apply unchanged here.

## Caveats

- **The dura-aware tool's small over-envelope volume is mostly an inferior
  brainstem/cord nub, not dura.** The cap tolerates it. A stricter reading of "no dura" would tighten
  the cap, at the risk of failing an otherwise good mask.
- **The envelope leans on the shipped segmentations.** It is a curated dura-out reference, not a
  hand-drawn gold standard; a fully manual dura label would be more rigorous.
