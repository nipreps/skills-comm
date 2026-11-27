---
name: brain-extraction
description: >
  Perform adult brain extraction or skull stripping and publish a
  publication-gated whole-brain MRI mask. Invoke on "skull strip", "brain extraction", "remove
  skull", "brain mask", "whole brain mask", or a request to isolate brain
  tissue for downstream analysis.
---

# Brain extraction

This skill supplies anatomical task knowledge and the execution/publication
contract. Tool references are neutral capability sheets, not a preferred order.

## 1. Check the anatomical target

A whole-brain extraction mask should include cerebral and cerebellar tissue,
brainstem to a defensible inferior cutoff, and the intracranial CSF boundary
appropriate to the requested downstream use. It should exclude scalp, skull,
orbits, nasal tissue, and neck. Inspect difficult boundaries at frontal poles,
inferior temporal lobes, posterior fossa, superior sagittal sinus, and around
large lesions or postoperative change.

The mask must be a coherent brain-shaped component. A binary file can still be
wrong through scalp inclusion, clipped cortex, an inferior leak, or selection
of an intensity-valued “brain image” instead of the mask output.

## 2. Establish the input and output contract

The bundled publisher accepts adult brain masks of 900–1900 cm3 and has no
override. If the input is paediatric, neonatal, rodent, markedly atrophic, or
post-resection anatomy, do not invoke this publisher; report that this skill's
publication contract does not support the case. QC's adjustable numeric range
does not override the publisher's gate.

Require a readable 3D extraction input, an explicit final mask path, and an
explicit `REFERENCE_GRID`. The reference defaults to the extraction input, but
downstream lesion QC may require a different already-coregistered anatomical
grid (for example FLAIR). Inspect modality, shape, affine, voxel size,
dimensionality, dtype, and finite-value range for both. For a 4D input,
establish the reference volume first. Do not overwrite an existing final result
unless replacement was requested and the old result was preserved.

## 3. Select a documented compatible tool

Start from modality compatibility and the task's compute constraints. Read only
the references for plausible tools; read `references/tool-comparison.md` only
if it changes the choice. Read `references/troubleshooting.md` only when its
failure signature matches. Choose autonomously based on documented fit,
availability, live Slurm capacity, output contract, and validation evidence.
Record the selected method and reason in one line. Do not ask the user to
choose.

Run and retain these probes before writing Slurm directives:

```bash
mkdir -p logs/tool-probes
nvidia-smi >logs/tool-probes/00_nvidia-smi.log 2>&1 || true
{
  sinfo -h -o 'partition=%P state=%a time=%l cpus=%c memory_mb=%m gres=%G'
  sinfo -N -h -o 'node=%N state=%T cpus=%c memory_mb=%m gres=%G'
  scontrol show partition
} >logs/tool-probes/00_slurm_resources.log 2>&1
```

Use only a reference-documented method whose availability probe succeeds.
Record failures and consider another documented compatible tool. Exhausting
the documented tools is reportable failure; intensity thresholding, masks from
nonzero voxels, and handwritten morphology are not substitutes.

Copy the selected reference's validated invocation exactly. Do not add optional
flags from memory, attach numeric values to boolean flags, or tune parameters in
a retry loop. A different invocation is a new scientific choice and must not be
silently substituted for the documented operating point.

## 4. Execute and publish

Put substantive work in a retained `src/analysis_<step>_brain_extraction.sh`,
pin the documented module, use a job-specific attempt directory, and submit
through Slurm with resources fitting the live report. Require captured job ID,
`sacct` `COMPLETED` with `ExitCode 0:0`, inspected logs, and the exact candidate
filename documented for the selected tool.

Submit one job per selected method. Capture `JOB_ID=$(sbatch --parsable
<script>)`, monitor that ID with `squeue -j "${JOB_ID}"`, and inspect it with
`sacct -j "${JOB_ID}"`. Never run `sbatch --wait "${JOB_ID}"` (sbatch treats
the ID as a script path). If a job fails, inspect its logs and resubmit only
after correcting a demonstrated cause, using a new attempt directory.

Resolve the installed skill directory before writing the retained Slurm script
and store its absolute path in `SKILL_DIR`; it is not automatically defined:

```bash
SKILL_DIR="/absolute/path/to/brain-extraction" # Replace with the installed path before submission.
: "${SKILL_DIR:?Set SKILL_DIR to this skill's installed directory before submission}"
test -f "${SKILL_DIR}/scripts/publish_mask.py"
HELPER_PYTHON="${HELPER_PYTHON:-$(command -v python3)}"
test -x "${HELPER_PYTHON}"
```

Capture `HELPER_PYTHON` before loading the imaging module so a container wrapper
cannot replace the host interpreter needed to read bundled helper scripts.
Check the script dependencies against
`${SKILL_DIR}/../python-requirements.txt`; report an environment mismatch
and do not install packages during the analysis job.

If the tool candidate does not exactly match `REFERENCE_GRID`, map it only when
the extraction input and requested reference have a declared valid spatial
relationship. This helper is nearest-neighbour resampling, not registration:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/resample_mask.py" \
  --candidate "${CANDIDATE_MASK}" --reference "${REFERENCE_GRID}" \
  --output "${ATTEMPT_DIR}/brain_mask_on_reference.nii.gz"
CANDIDATE_MASK="${ATTEMPT_DIR}/brain_mask_on_reference.nii.gz"
```

If no valid relationship exists, stop and report the grid handoff as
unavailable. Never copy only the header between meaningfully different grids.
Publish only with:

```bash
"${HELPER_PYTHON}" "${SKILL_DIR}/scripts/publish_mask.py" \
  --kind brain --candidate "${CANDIDATE_MASK}" \
  --reference "${REFERENCE_GRID}" --output "${FINAL_MASK}"
```

The publisher requires binary non-empty data, exact reference grid, one
6-connected component, no internal holes, and adult brain volume 900–1900 cm3.
It writes exact `uint8` `{0,1}`, copies the reference affine/header, clears
NIfTI scaling, verifies the stored file, and renames atomically.
It refuses an existing output by default. Do not pass `--replace` unless the
task explicitly authorized replacement and the previous output was preserved.

After publication invoke `brain-extraction-qc` with an anatomical image on
`REFERENCE_GRID`. Inspect volume, symmetry,
centring, topology, scalp inclusion, boundary tightness, the real PNG encoding,
and the rendered outline before claiming anatomical quality.

If the image is in a Nipoppy dataset and human visualization in QC Studio is
needed, read
`${SKILL_DIR}/../brain-extraction-qc/references/qcstudio-integration.md`.
This optional view supplements the mask QC report. If QC is Fail, Borderline,
or incomplete, retain the report with the mask and do not hand the mask to
downstream analysis as approved.

## Constraints

- Do not choose by user preference or request an interactive tool selection;
  use the documented compatibility and availability evidence.
- Run image reads and neuroimaging tools inside the retained, version-pinned
  SLURM script. Never infer a mask from nonzero voxels or handwritten
  morphology.
- Preserve existing outputs unless replacement was explicitly authorized.
- Report publication success separately from anatomical QC; a valid NIfTI
  mask is not by itself evidence of a correct extraction.
