# Interpreting the Lesion Signature Probe

What `scripts/lesion_signature.py` measures, how the ranking rules work, and
where each measurement misleads. Read this before acting on a result — the
output is a ranked hypothesis with evidence, not an answer, and it is only
useful to someone who knows what it can be wrong about.

## The reference frame

Two choices underpin everything else.

**Canonical RAS reorientation.** Volumes are reoriented so axis 0 is
left→right. Laterality is central to telling a focal infarct from bilateral
small-vessel disease, and it means nothing computed on raw voxel axes.

**A searched mid-sagittal plane.** The midline is found by maximising the brain
mask's own mirror overlap, reported as `head_symmetry_dice` (expect > 0.97). The
centroid is not good enough: whatever the field of view includes of neck and jaw
drags it sideways by several millimetres, the same order as the asymmetries
being measured. If `head_symmetry_dice` is low, every laterality number below it
is suspect and should be reported as such.

## Features

### Restricted diffusion — the acute stroke signature

`restricted_diffusion` counts voxels that are DWI-bright **and** ADC-dark. When
DWI and ADC are both present this is the most decisive measurement the probe
makes; nothing else distinguishes acute ischaemia so cleanly.

With DWI but no ADC the probe refuses to compute it and says so. That refusal
matters: DWI hyperintensity alone does not separate acute infarct from T2
shine-through, and reporting it as though it did would be a confident error at
the point where confidence is most consequential.

**Misleads on:** subacute lesions past pseudonormalisation (roughly a week),
where restriction fades and the lesion becomes invisible to this test.

### FLAIR/T2 hyperintensity — burden and pattern

`flair_hyper` gives total load, cluster count, largest-cluster fraction, and
laterality. The pattern matters more than the load. WMH is many small bilateral
foci hugging the ventricles; a focal infarct or tumour is one dominant
unilateral mass. The same total volume means different things in those two
shapes.

`periventricular_fraction` uses a ventricle proxy (deep, near-midline CSF on
T1). It is a proxy, and it feeds a *relative* measure, so being consistently a
little off still separates ventricle-hugging from peripheral lesions.

**Misleads on:** anything else that is FLAIR-bright — oedema, gliosis, MS
plaques, incomplete CSF suppression, flow artefact.

### T1 cavity — the chronic stroke signature

`t1_cavity` looks for tissue that is CSF-dark **where the mirror location is
normal tissue**. That contrast is what makes a region a lesion rather than
anatomy, and testing it directly is far more robust than trying to enumerate and
subtract every normal CSF space: ventricles are dark on both sides and drop out,
as do sulci, cisterns and fissures.

**This detector has a measured noise floor of roughly 13 cm³.** On a healthy
adult T1 it still returns that much asymmetric CSF-like tissue after every
filter, because head tilt, partial volume and genuinely asymmetric CSF spaces do
not cancel under a single reflection. The threshold sits at 25 cm³, above the
floor. The consequence is deliberate and worth stating plainly:

> **Lacunes and small chronic infarcts will not be detected.** Absence of a
> cavity finding is not evidence of no chronic infarct.

That trade is right for a router whose fallback is to ask, and wrong if you were
hoping to use this as a detector. Use a real segmenter for that.

**Misleads on:** large asymmetric ventricles, porencephalic cysts, post-surgical
cavities, arachnoid cysts — all CSF-dark, all unilateral, none of them stroke.

## Ranking rules

Rules, not a classifier, so the output can state its own reasoning. Confidence
comes from how many independent expectations line up:

- **acute_ischaemic_stroke** — restricted diffusion above 1 cm³. HIGH when it is
  also focal (largest cluster ≥60% of load) and unilateral (laterality >25%).
- **chronic_stroke** — asymmetric CSF-like cavity above 25 cm³. Raised to HIGH
  by ventricular asymmetry >20%, but only when the ventricle proxy is itself a
  plausible size (≥5 cm³) — a tiny proxy makes that ratio noise.
- **wmh** — FLAIR burden scored on four expectations: bilateral, distributed
  rather than focal, ≥5 foci, periventricular fraction ≥40%. Three or more gives
  HIGH.
- **focal_lesion_not_wmh** — FLAIR burden that is unilateral *and* dominated by
  one cluster. Flagged out of scope: this is not the WMH pattern and may be
  infarct, tumour, demyelination or abscess.
- **ms_cannot_exclude** — raised whenever there are ≥3 FLAIR foci. Not a
  positive finding; a standing reminder that the discriminating features are not
  measured here.

## Known failure modes

**WMH and MS are not numerically separable.** Both are multifocal FLAIR
hyperintensity, both often periventricular. What separates them — ovoid
morphology, Dawson's fingers, juxtacortical and infratentorial involvement,
patient age and clinical history — is not measured. Treating a WMH ranking as
settled without addressing the MS flag is a real misdiagnosis risk.

**Bilateral symmetric cavities are suppressed** by the mirror test. Bilateral
watershed infarction is the case to watch. The pre-filter volume is reported so
the suppression is visible.

**Co-occurring pathology is common and the probe ranks rather than partitions.**
An elderly stroke patient usually also has WMH. Multiple hypotheses with real
evidence behind them is the correct output there, not a defect.

**Thresholds are calibrated for adult brain MRI at typical clinical contrast.**
Paediatric, neonatal and animal data need retuning of every spatial and
intensity constant in `CFG`.

## Validation status

Validated on synthetic multi-modal phantoms built on real adult brain anatomy:
normal, acute stroke, WMH and chronic stroke all rank correctly, and the WMH
case correctly raises the MS referral flag.

Phantoms reproduce the *signatures* the probe keys on. They do not reproduce
real lesion appearance, partial volume, bias field, motion, or the pathology
mimics listed above. **Passing means the logic and threshold directions are
right; it does not mean the cut-offs are calibrated for clinical data.** Real
validation needs a labelled clinical cohort, and until that exists the probe's
output should be treated as a hypothesis to confirm, never as a finding.
