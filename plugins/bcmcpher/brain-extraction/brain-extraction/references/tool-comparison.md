# Brain Extraction Tool Comparison

Present this table when the user requests brain extraction. Do not recommend a
tool unprompted; let the user choose based on priorities unless they ask.

## Side-by-Side Comparison

| Tool | Executable / package hint | Method | Typical Speed | Template Required | GPU Optional | Best For | Known Failure Modes |
|------|---------------------------|--------|---------------|-------------------|--------------|----------|---------------------|
| **FSL BET** | `bet` / FSL | Morphological surface fitting | Fast | No | No | Standard T1w, quick turnaround, FSL workflows | Non-standard intensity profiles, pathology near boundary |
| **ANTs antsBrainExtraction** | `antsBrainExtraction.sh` / ANTs | Template-based probabilistic atlas | Slow | Yes | No | Maximum accuracy, atypical anatomy, clinical data | Fails if template is inappropriate; slow for batches |
| **mri_synthstrip** | `mri_synthstrip` / FreeSurfer or SynthStrip | Deep learning, contrast-agnostic | Moderate | No | Sometimes | T1w, T2w, FLAIR, DWI, unusual contrast | Occasional inferior temporal/cerebellum boundary issues; licence may be needed |
| **HD-BET** | `hd-bet` / `hdbet` | Deep learning | Fast on GPU, moderate on CPU | No | Yes | Standard T1w, high-throughput datasets | Can under-strip low-contrast images; CPU mode can be slow |
| **AFNI 3dSkullStrip** | `3dSkullStrip` / AFNI | Morphological surface expansion | Moderate | No | No | EPI/functional data, AFNI workflows | Less reliable on non-T1w structural data |

## Key Decision Factors

**Use BET if:** speed matters and the data are standard T1w.

**Use ANTs if:** accuracy is the top priority and a suitable template/mask is
available.

**Use mri_synthstrip if:** the modality or contrast is non-standard.

**Use HD-BET if:** standard T1w data and GPU or acceptable CPU runtime are
available.

**Use 3dSkullStrip if:** working in AFNI or with EPI/functional reference data.

## Modality Support Summary

| Tool | T1w | T2w | FLAIR | DWI b0 | EPI/fMRI |
|------|:---:|:---:|:-----:|:------:|:--------:|
| FSL BET | yes | partial | partial | partial | yes, with `-F` |
| ANTs | yes | with template | with template | uncommon | uncommon |
| mri_synthstrip | yes | yes | yes | yes | yes |
| HD-BET | yes | partial | uncommon | uncommon | uncommon |
| 3dSkullStrip | yes | uncommon | uncommon | uncommon | yes |
