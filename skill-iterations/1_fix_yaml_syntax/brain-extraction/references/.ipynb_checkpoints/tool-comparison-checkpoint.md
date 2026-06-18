# Brain Extraction Tool Comparison

Present this table to the user when they request brain extraction. Do not
recommend a tool unprompted — let the user choose based on their priorities.

## Side-by-Side Comparison

| Tool | Module | Method | Typical Speed | Template Required | GPU Optional | Best For | Known Failure Modes |
|------|--------|--------|--------------|-------------------|--------------|----------|---------------------|
| **FSL BET** | `fsl/6.0.7.22` | Morphological (surface fitting) | Fast (~2–5 min) | No | No | Standard T1w, quick turnaround, scripted pipelines | Non-standard intensity profiles; very young/old brains; non-brain pathology near boundary |
| **ANTs antsBrainExtraction** | `ants/2.6.5` | Template-based probabilistic atlas | Slow (~30–60 min) | Yes (OASIS-30 or MNI) | No | Maximum accuracy, atypical anatomy, clinical data | Fails if template space differs greatly from input; slow — not suitable for large batches without HPC parallelism |
| **FreeSurfer mri_synthstrip** | `freesurfer/8.2.0` | Deep learning (contrast-agnostic) | Moderate (~5–15 min) | No | Optional (CPU default) | T1w, T2w, FLAIR, DWI — any modality; robust to scanner variability | Occasional over-stripping at inferior temporal/cerebellum boundary; requires FreeSurfer licence |
| **HD-BET** | `hd-bet/2.0.1` | Deep learning (trained on multi-site data) | Fast on GPU (~2–5 min); Moderate on CPU (~15–20 min) | No | Yes (faster with GPU) | Standard T1w, high-throughput datasets, good default accuracy | Can under-strip in very low-contrast images; CPU mode is slow for large batches |
| **AFNI 3dSkullStrip** | `afni/26.0.07` | Morphological (surface expansion) | Moderate (~5–10 min) | No | No | EPI/functional data, T1w within AFNI workflows | Less reliable on non-T1w structural data; may require parameter tuning for paediatric data |
| **SynthStrip standalone** | `synthstrip/7.4.1` | Deep learning (same model as mri_synthstrip) | Moderate (~5–15 min) | No | Optional | Any modality, when FreeSurfer is not otherwise needed — lighter dependency | Same as mri_synthstrip; standalone version avoids full FreeSurfer environment overhead |

## Key Decision Factors

**Use BET if:** you need speed, are processing many subjects, or are within an
FSL pipeline already. Tune `-f` (fractional threshold) if the default crops too
much or too little.

**Use ANTs if:** accuracy is the top priority and you have time. Especially
useful when other tools fail on unusual anatomy.

**Use mri_synthstrip or SynthStrip if:** your data is multi-modal or the
contrast profile is non-standard. Deep learning generalises well across scanners
and field strengths.

**Use HD-BET if:** you have GPU access and want fast, reliable results on
standard T1w without installing FreeSurfer.

**Use 3dSkullStrip if:** you are working within an AFNI pipeline or your
primary data is functional/EPI.

## Modality Support Summary

| Tool | T1w | T2w | FLAIR | DWI (b0) | EPI/fMRI |
|------|:---:|:---:|:-----:|:--------:|:--------:|
| FSL BET | ✓ | Partial | Partial | Partial | ✓ (with `-F`) |
| ANTs | ✓ | ✓ (with T2 template) | — | — | — |
| mri_synthstrip | ✓ | ✓ | ✓ | ✓ | ✓ |
| HD-BET | ✓ | Partial | — | — | — |
| 3dSkullStrip | ✓ | — | — | — | ✓ |
| SynthStrip | ✓ | ✓ | ✓ | ✓ | ✓ |
