# Brain-mask QC script and output contract

The bundled scripts are the source of truth for implementation details. Run
image reads inside a retained SLURM script, not in an interactive shell.

## Scripts

- `scripts/qc_metrics.py` reads the anatomical image and binary mask, computes
  the numeric QC battery, and writes a JSON report. Inputs are positional:
  anatomical image, then mask. `--vol-range LO HI` overrides the adult T1w
  default of 900–1900 cm³.
- `scripts/afni_outline_qc.sh` checks that the caller loaded the pinned AFNI
  module, renders an outline in a job-specific temporary directory, validates
  the converted PNG, and publishes it without overwriting an existing file.
- `scripts/qc_mosaic.py` renders an optional filled-mask and contour mosaic.

Resolve the host `python3` path before loading AFNI. Check `numpy`, `nibabel`,
`scipy`, `matplotlib`, and Pillow (`PIL`) in that interpreter in the
submitted job. Export `HELPER_PYTHON` for the outline script. If a dependency
is missing, report the limitation; do not install packages during the QC run.

## Output set

For one run, save the metrics JSON, outline PNG, optional mosaic PNG, AI report,
and blank human verification form under the requested QC output directory. Set
the timestamp inside the Slurm job, save it with the job ID, and reuse it in
every filename. The metrics JSON records numeric values and verdict; it does
not claim visual review. Record dura and superior sagittal sinus inclusion as
UNVERIFIED unless the outline was actually inspected.
