# Brain Extraction Troubleshooting

## Module not found

**Symptom:** the documented pinned module fails to load.

**Cause:** The pinned version in the reference file may be stale — the cluster may have upgraded or removed it.

**Action:**
```bash
module spider fsl/6.0.7.22
```
Record that the pinned dependency is unavailable. Do not silently substitute a
different version; use an alternative only when its reference documents a
compatible invocation.

---

## Missing ANTs template (OASIS-30)

**Symptom:** `antsBrainExtraction.sh` exits immediately with an error about a missing template directory.

**Cause:** The OASIS-30 MNI152 template required by ANTs is not present at the expected path.

**Action:** report that the required template is unavailable. Do not fetch data
or substitute a different template unless the task explicitly requests it and
the source and version are documented.

---

## Job killed / Out of Memory (OOM)

**Symptom:** `sacct` shows `State=OUT_OF_MEMORY` or `State=FAILED` with a non-zero exit code.

**Diagnosis:**
```bash
sacct -j <jobid> --format=JobID,State,ExitCode,MaxRSS --noheader
```
A `MaxRSS` close to the requested `--mem` confirms OOM.

**Action:** record the failure and accounting. For an explicitly authorized
retry, adjust `--mem` using the measured `MaxRSS`; do not resubmit repeatedly:
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

**Action:** report the dimension mismatch and stop. Create a single-volume
derivative only when the task explicitly calls for it, in a separate retained
SLURM job:
```bash
module load fsl/<version>
fslroi <input_4d.nii.gz> <output_3d.nii.gz> 0 1
```
Then use the derived 3D image only when that matches the requested analysis.
