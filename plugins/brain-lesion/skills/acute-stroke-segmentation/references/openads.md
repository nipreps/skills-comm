# OpenADS

OpenADS is an acute-stroke pipeline that performs preprocessing, brain masking,
segmentation, normalization, and reporting. It accepts a subject directory
rather than individual file arguments. This sheet describes both installed
hardware variants without ranking them.

## Availability and resources

- GPU module: `openads/1.0.0`
- CPU module: `openadscpu/1.0.0`
- Executable: `ads`
- Conservative Slurm starting request: 4 CPUs, 16 GB RAM, 2 hours; request a
  GPU only for the GPU module and only when Slurm advertises it.

```bash
set -o pipefail
module -t avail openads/1.0.0 openadscpu/1.0.0 2>&1
# Load exactly one compatible module, then:
command -v ads
ads version
```

## Inputs and invocation

OpenADS takes a subject directory, not file arguments. Stage this layout, which
is the one the pipeline documents and the one always observed to resolve. For
`SUBJECT_ID=$(basename "${SUBJECT_DIR}")`:

```text
<SUBJECT_DIR>/<SUBJECT_ID>_DWI.nii.gz
<SUBJECT_DIR>/<SUBJECT_ID>_ADC.nii.gz
```

Discovery is in practice more forgiving than that — a mismatched prefix such as
`sub-CASEA/CASEA_DWI.nii.gz`, and bare `DWI.nii.gz`/`ADC.nii.gz`, have both been
observed to resolve. Do not rely on it: the matching layout above is the only one
to stage deliberately, and a `FileNotFoundError` during preprocessing means
discovery failed whatever the names looked like.

Stage copies or links in the attempt directory; do not rename or overwrite
canonical inputs. Always give OpenADS a writable output root.

```bash
module load openadscpu/1.0.0  # or openads/1.0.0 on an eligible GPU node
mkdir -p "${ATTEMPT_DIR}/openads"
ads dwi --subject-path "${SUBJECT_DIR}" --all \
  --output-root "${ATTEMPT_DIR}/openads"
```

## Outputs

The verified lesion file is:

```text
<output-root>/<SUBJECT_ID>/DWI/segment/<SUBJECT_ID>_stroke-mask.nii.gz
```

| Output | Meaning | Use |
|---|---|---|
| `DWI/segment/<id>_stroke-mask.nii.gz` | Binary stroke mask on OpenADS' reoriented preprocessing DWI grid | Map to requested raw DWI grid, then publish |
| `DWI/segment/<id>_stroke-mask_space-MNI152.nii.gz` | Normalized mask, **affine only** | Not a native-grid substitute |
| `DWI/segment/<id>_stroke-mask_space-MNI152_affsyn.nii.gz` | Normalized mask, affine + SyN | Not a native-grid substitute |
| `DWI/segment/<id>_metrics.json` | Populated **only** when a reference label `<id>_stroke.nii.gz` is staged with the inputs | Every field, `pred_volume` included, is `null` without one |
| `<id>_DWIbrain-mask.nii.gz` | Pipeline brain mask | Not the lesion mask |
| report/normalization products | Pipeline context | Supplementary outputs |

OpenADS' “native” mask is native to
`DWI/preprocess/<id>_DWI.nii.gz`, whose voxel orientation may differ from the
original raw DWI even when shape and physical coverage are preserved. Do not
copy its array under the raw header and do not invert the MNI transforms for
this orientation-only handoff. Map it deterministically with:

```bash
python3 "${SKILL_DIR}/scripts/resample_mask.py" \
  --candidate "<output-root>/<id>/DWI/segment/<id>_stroke-mask.nii.gz" \
  --reference "${RAW_DWI}" \
  --output "${ATTEMPT_DIR}/<id>_stroke-mask_raw-DWI.nii.gz"
```

Confirm that voxel-count/volume change is within the helper's limit, then give
the mapped result to the publisher. Do not guess a root-level
`<id>_stroke.nii.gz` filename and do not select an MNI-space mask when the
request requires raw DWI space.

## The pipeline's own report quotes a different volume

`<output-root>/<id>/DWI/reporting/<id>_automatic_radiological_report.txt` is a
useful source of pipeline context, but **the lesion volume it states is measured
on the affine-MNI mask, not the native one**, and the two differ by tens of
percent because the atlas warp rescales. Quote a volume only from the mask you
published on the requested grid. If you cite the tool's report for anything else,
say which space its number is in rather than repeating it as the result.

## Bundled atlases and the reporting stage

The `--all` run includes a reporting stage whose outputs land under
`<output-root>/<id>/DWI/reporting/`. Beyond the text report it computes
**per-arterial-territory lesion load**, because the image ships atlases at
`/opt/openads/assets/atlases/JHU_ICBM/` inside the container:

| Asset | What it is |
|---|---|
| `ArterialAtlas_MNI182.nii.gz` + `ArterialAtlasLables.txt` | JHU Digital 3D Brain MRI Arterial Territories Atlas, 32 labels (© 2021 Johns Hopkins University, CC BY-SA 4.0) |
| `AspectsAtlas_MNI182.nii.gz`, `AspectsPcaAtlas_MNI182.nii.gz` + lookups | ASPECTS and PC-ASPECTS scoring regions |

This matters when the request asks for a **vascular territory**: it is a direct
atlas measurement available from this tool, not something to infer from a
structural atlas. Harvard-Oxford and the other FSL atlases carry no vascular
territories at all, and no arterial-territory module is installed on a stock
Neurodesk node — so `module avail`/`keyword` searches for one come back empty and
this bundled atlas is easy to miss.

The territories are measured in the pipeline's MNI space. That is legitimate for
a *share* of the lesion; it remains illegitimate for a volume. Report territory as
a percentage and keep the volume on the requested grid.

Treat the pipeline's own ASPECTS/PC-ASPECTS numbers with care: verify how that
implementation handles left/right before quoting a score.

## Known signatures

| Signature | Interpretation |
|---|---|
| `Memory specification can not be satisfied` from `sbatch` | Impossible scheduler request; OpenADS did not run |
| Read-only error under the installation `output` path | Writable `--output-root` was missing or ineffective |
| `DWI Pipeline Finished Successfully` followed by a wrapper missing-file error | Wrapper guessed the wrong output filename; inspect the verified native path |
| DWI/ADC `FileNotFoundError` during preprocessing | Subject-directory layout incompatibility |
| Publisher reports `reference_grid_exact` on the “native” mask | Expected OpenADS reorientation; use the bundled raw-grid helper, not header copying or MNI inversion |
| CUDA/device error with the GPU module | Hardware/module mismatch |

Retain the subject tree, probe, job logs, stage logs, and publisher JSON.
