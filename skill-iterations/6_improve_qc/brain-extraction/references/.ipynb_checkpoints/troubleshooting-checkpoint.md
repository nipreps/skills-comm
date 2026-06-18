# Brain Extraction Troubleshooting

## Module not found

**Symptom:** `module load fsl/6.0.7.22` fails with "module not found" or similar.

**Cause:** The pinned version in the reference file may be stale — the cluster may have upgraded or removed it.

**Fix:**
```bash
module spider fsl
```
Identify the available version(s), select the closest one, and update the `module load` line in your script before resubmitting.

---

## Missing ANTs template (OASIS-30)

**Symptom:** `antsBrainExtraction.sh` exits immediately with an error about a missing template directory.

**Cause:** The OASIS-30 MNI152 template required by ANTs is not present at the expected path.

**Fix — download via DataLad:**
```bash
datalad install https://github.com/stnava/ANTs/releases/download/v2.3.4/ANTs_template_OASIS30.tar.gz
```

**Fix — download via wget:**
```bash
wget -q https://github.com/stnava/ANTs/releases/download/v2.3.4/ANTs_template_OASIS30.tar.gz
tar -xzf ANTs_template_OASIS30.tar.gz
```

Update `TEMPLATE_DIR` in your script to point to the extracted directory.

---

## Job killed / Out of Memory (OOM)

**Symptom:** `sacct` shows `State=OUT_OF_MEMORY` or `State=FAILED` with a non-zero exit code.

**Diagnosis:**
```bash
sacct -j <jobid> --format=JobID,State,ExitCode,MaxRSS --noheader
```
A `MaxRSS` close to the requested `--mem` confirms OOM.

**Fix:** Increase `--mem` in the SLURM header and resubmit:
- FSL BET: 8–16 GB is typically sufficient for T1w
- ANTs: 32–64 GB for whole-brain registration
- HD-BET: 8–16 GB (CPU mode); GPU mode needs a GPU partition

---

## Wrong input dimensions (4D volume)

**Symptom:** Tool exits with an error about unexpected image dimensions, or produces an empty / nonsensical mask.

**Diagnosis:**
```bash
python3 -c "import nibabel as nib; img = nib.load('<input_path>'); print(img.shape)"
```
If the shape has 4 elements and the 4th is > 1, the input is a 4D timeseries.

**Fix:** Extract a single volume before running brain extraction:
```bash
module load fsl/<version>
fslroi <input_4d.nii.gz> <output_3d.nii.gz> 0 1
```
Then re-run brain extraction on `<output_3d.nii.gz>`.
