# Visual Lesion Identification

The vision path. Read this only if you can actually open images; otherwise work
from `signature-interpretation.md` and report a numeric-only hypothesis.

Vision is worth the effort here for what measurement handles badly: morphology,
mass effect, distribution relative to anatomy, and the WMH/MS distinction that
has no numeric rule at all.

## Generate something to look at

Any 3-plane mosaic works. The `brain-extraction-qc` skill's `qc_mosaic.py` will
render an anatomical with a mask overlay, and the AFNI `@chauffeur_afni` route
works equally well. Look at the sequence the lesion is defined on: FLAIR for
WMH and MS, DWI+ADC side by side for acute stroke, T1 for chronic cavities.

## Patterns

### Acute ischaemic stroke
DWI-bright with matching ADC-dark. Wedge-shaped, respecting a vascular
territory, reaching the cortical surface in a territorial infarct. Usually one
lesion, unilateral. Check DWI and ADC together — a lesion bright on both is not
restricted diffusion.

### Chronic stroke
CSF-like cavity on T1, often with a FLAIR-bright gliotic rim. Sharply
demarcated, unilateral, respecting a territory. Ex-vacuo dilation of the
ipsilateral ventricle and widened adjacent sulci are strong confirmatory signs
and are what distinguish it from a cyst.

### WMH
FLAIR-bright, T1 iso- to mildly hypointense. Periventricular caps and rims,
punctate to confluent deep white matter foci, **bilateral and roughly
symmetric**. Spares the cortex and the U-fibres. Increases with age and vascular
risk.

### MS — recognise and refer
Also FLAIR-bright and periventricular, which is precisely the problem. What
separates it from WMH:
- **ovoid** lesions oriented **perpendicular** to the ventricles (Dawson's
  fingers), rather than confluent caps
- **juxtacortical** involvement touching the U-fibres, which WMH spares
- **infratentorial** lesions — brainstem, cerebellar peduncles, cord
- **T1 black holes**, hypointense on T1 where WMH is not
- younger patient

Any of these should stop a WMH routing.

### Tumour — recognise and refer
Mass effect is the giveaway: sulcal effacement, ventricular compression, midline
shift. Surrounding vasogenic oedema, and enhancement if post-contrast imaging
exists. Not in scope for these skills.

### Haemorrhage — recognise and refer
Signal varies with age of blood and is genuinely confusing on T1/T2 alone.
Blooming on SWI or GRE is the reliable sign. Not in scope.

## Reconciling with the probe

Where vision and measurement disagree, say which you trusted and why.

Vision should generally win on morphology, mass effect, focal defects, and any
case where visible anatomy explains an odd number. Measurement should generally
win on burden, laterality and anything requiring counting — impressions of
symmetry are unreliable, and quantities are exactly what the eye estimates
badly.

Record the disagreement either way. A documented conflict is a useful QC result;
a silently overridden one destroys the audit trail.

## Still confirm with the user

Vision does not substitute for clinical context. Age, symptom onset time, stroke
history and the referral question frequently settle what the images leave
ambiguous — most sharply for WMH versus MS, where the imaging can be genuinely
identical and the patient's age is decisive.
