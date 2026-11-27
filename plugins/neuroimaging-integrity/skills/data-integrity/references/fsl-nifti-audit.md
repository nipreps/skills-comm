# FSL NIfTI integrity audit

Use this reference when FSL is the selected NIfTI parser. It is an audit aid,
not a repair recipe. Follow the parent skill's read-only and batch-only rules:
on Neurodesk, run every command that opens or computes from an input image
inside a retained Slurm script with the exact selected module version.

## Select and verify FSL

Discover only the selected module and version before writing the script, for
example `module spider fsl/6.0.7.23`. In the script, load that exact version
and record `fslversion` plus the availability of the commands the script uses.
Do not inspect wrapper scripts, container catalogs, or unrelated FSL installs
to debug a normal module load. If the module loads but a required command fails,
retain the module/runtime error in the Slurm log and report the affected check
as NOT CHECKED or WARNING.

## Header and geometry commands

Run these from the Slurm script, retaining stdout and stderr separately:

```bash
fslhd "$image" > "$header_out" 2> "$header_err"
fslinfo "$image" > "$info_out" 2> "$info_err"
```

`fslhd` reports the full header; `fslinfo` reports a basic subset. `fslval`
can retrieve one named header value when needed. Use the command's actual
output format: FSL headers contain keys such as `qto_xyz:1` and `sto_xyz:1`,
and `fslinfo` presents named fields. Do not assume every key is a simple
colon-delimited token or parse tabular header output using a fixed character
offset. Preserve the raw header output with the audit artifacts.

Compare complete qform and sform transforms when both codes are set. A
comparison of only dimensions, voxel sizes, or origins does not establish that
the affines agree. A missing form code, a genuine transform disagreement, and
a parser failure are different outcomes; report each with the evidence rather
than silently preferring one transform.

## Voxel summaries with `fslstats`

The commonly useful options are:

| Option | Meaning |
|---|---|
| `-R` | Absolute minimum and maximum |
| `-r` | Robust minimum and maximum |
| `-v` | Total voxel count and total volume in mm³ |
| `-V` | Non-zero voxel count and non-zero volume in mm³ |
| `-m` / `-s` | Mean / standard deviation over all voxels |
| `-M` / `-S` | Mean / standard deviation over non-zero voxels |
| `-p N` | The requested percentile, where supported by the selected FSL build |

For example, the following summary requests absolute range, total and non-zero
counts/volumes, and all-voxel and non-zero statistics:

```bash
fslstats "$image" -R -v -V -m -s -M -S > "$stats_out" 2> "$stats_err"
```

In FSL 6.0.7.23, that combined request emitted one whitespace-delimited line
with fields in option order: min, max, total voxel count, total volume,
non-zero voxel count, non-zero volume, mean, standard deviation, non-zero
mean, non-zero standard deviation. Parse the expected number of fields and
check the command exit status. Do not read one statistic per line. Keep the raw
output, and if the field count or format differs, mark dependent checks
NOT CHECKED or WARNING instead of reporting the image as empty or corrupt.
Reconfirm the format when changing FSL versions.

`-V` can support an all-zero check when its output parses correctly. It does
not prove that all voxel values are finite. Do not use statistics calculated
after replacing NaN or infinity with zero as evidence that the original image
contained no such values. Use a separately verified finite-value check; if the
chosen method cannot distinguish non-finite values reliably, report that check
as NOT CHECKED.

For percentiles, request them explicitly and save the raw output. Do not infer
ADC units or modality identity from raw quantiles alone; use the source
metadata and the unit guidance in the parent skill.

## Interpreting the audit

- Compare ADC and DWI grids when they are expected to describe the same
  acquisition. A structural image may legitimately have a different voxel
  resolution or grid; report the difference and assess registration/provenance
  rather than treating every mismatch as corruption.
- Header plausibility and successful decompression cannot prove that the
  original DICOM series or a required scan was complete before conversion.
- A locally generated SHA-256 manifest proves only that the recorded bytes can
  be identified and checked for later change. Compare it with a trusted source
  manifest before calling it provenance evidence.
- Keep file/header integrity, acquisition metadata, and source completeness as
  separate statuses. Missing independent inventory normally leaves overall
  dataset completeness at WARNING, even when supplied files pass internal
  checks.

## References

- FSL, [FSL utilities](https://fsl.fmrib.ox.ac.uk/fsl/docs/utilities/fslutils.html): descriptions of `fslhd`, `fslinfo`, `fslval`, and `fslstats`.
- FSL, [FSLUTILS practical](https://fsl.fmrib.ox.ac.uk/fslcourse/graduate/lectures/practicals/intro3/): examples for `-R`, `-r`, `-V`, `-k`, `-M`, and checking command usage.
