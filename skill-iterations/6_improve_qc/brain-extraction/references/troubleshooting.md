# Brain Extraction Troubleshooting

## Tool Not Found

**Symptom:** the selected executable is missing, e.g. `command -v bet` fails.

**Fix:**
```bash
command -v <executable>
<executable> --help 2>&1 | head -40
```

If unavailable, inspect the local environment:
```bash
command -v module >/dev/null && module avail <tool_or_package>
command -v conda >/dev/null && conda env list
command -v apptainer >/dev/null || command -v singularity >/dev/null || command -v docker >/dev/null
```

Use the local install, environment activation, module, or container mechanism
that exists on the system.

## Missing ANTs Template

**Symptom:** `antsBrainExtraction.sh` exits with an error about a missing
template or probability mask.

**Fix:** verify the exact paths:
```bash
ls "<template.nii.gz>" "<template_prob_mask.nii.gz>"
```

If absent, obtain templates from a lab-approved source, ANTs release assets,
shared storage, DataLad/OpenNeuro datasets, or direct download when licensing
allows. Record the acquisition command in a script.

## Out Of Memory Or Job Killed

**Symptom:** process exits abruptly, a scheduler reports OOM, or logs mention
memory allocation failure.

**Fix:** increase memory, reduce thread count if memory scales per thread, use
CPU/GPU mode appropriate for the tool, or submit through the local scheduler if
available. Inspect logs or scheduler accounting with the commands used by the
current system.

## Wrong Input Dimensions

**Symptom:** tool errors on dimensions or produces an empty/nonsensical mask.

**Diagnosis:**
```bash
python3 -c "import nibabel as nib; img = nib.load('<input_path>'); print(img.shape)"
```

If the file is 4D, extract a representative 3D volume or use a tool/mode
intended for functional data. For example, with FSL available:
```bash
fslroi <input_4d.nii.gz> <output_3d.nii.gz> 0 1
```
