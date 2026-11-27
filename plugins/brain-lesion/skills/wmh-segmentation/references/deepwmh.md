# DeepWMH

DeepWMH is an annotation-free, FLAIR-only WMH segmentation pipeline built around
a customized nnU-Net. Its pretrained inference path applies N4 bias-field
correction, removes components below its internal 3 mm rule, masks the result
with an internally generated ROBEX brain mask, and writes a binary WMH mask.

Primary sources: [official repository](https://github.com/lchdl/DeepWMH) and
[2024 publication](https://pubmed.ncbi.nlm.nih.gov/38320896/).

## Neurodesk integration status

**Module: `deepwmh/1.0.1`.** In the tested Neurodesk image, the tool banner
self-reports "Version 1.0.0 (2023.10)"; the module version identifies the
container build, not the upstream release. Confirm the exact module with
`module spider deepwmh/1.0.1` on the target cluster.

The container bundles the pretrained model, the DeepWMH nnU-Net fork, ROBEX and
ANTs, so inference works offline. Consequently `N4BiasFieldCorrection` and
`ROBEX_DIR` are **not** exposed on the host, and the host-visible
`DEEPWMH_MODEL_DIR` points *inside* the `.simg`
(`.../deepwmh_1.0.1_<build-id>.simg/opt/deepwmh-model`), so it is not a readable
host directory. Do not gate on either; both are internal implementation detail.
The exact image path is set by the Neurodesk module and varies by image build.

```bash
set -o pipefail
module -t avail deepwmh/1.0.1 2>&1 | grep -F 'deepwmh/1.0.1'
module load deepwmh/1.0.1
command -v deepwmh
command -v DeepWMH_predict
command -v nnUNet_predict
deepwmh --help >logs/tool-probes/deepwmh_help.log 2>&1
```

`deepwmh` is a thin wrapper that execs
`DeepWMH_predict -m "${DEEPWMH_MODEL_DIR:-/opt/deepwmh-model}"`. Because the host
wrappers use `--cleanenv`, the in-container fallback `/opt/deepwmh-model` is what
actually applies. The model root contains a single task,
`nnUNet/3d_fullres/Task002_FinalModel/...`, so `--custom-task-name` is not needed.

## Required workaround: writable model root

**The module cannot run as shipped.** The bundled nnU-Net fork writes a
`training_log_<timestamp>.txt` into the *model* folder during `restore_model`,
and the absolute path `/opt/deepwmh-model/...` is baked into the re-packaged
`model_best.model.pkl`. The squashfs image is read-only, so inference aborts
after N4 preprocessing with:

```text
OSError: [Errno 30] Read-only file system:
'/opt/deepwmh-model/nnUNet/3d_fullres/Task002_FinalModel/nnUNetTrainerV2__nnUNetPlansv2.1/all/training_log_....txt'
```

Passing `--trained-model <writable copy>` does **not** fix this: the log path
comes from the pickle, not from the supplied model root. The working fix is to
stage a writable copy of the model (237 MB) and bind it *over* the image path.
The Neurodesk command wrappers expand `$neurodesk_singularity_opts` into their
`singularity exec` line, which is how the extra bind is delivered:

```bash
DEEPWMH_BIN="$(command -v deepwmh)"
DEEPWMH_DIR="$(dirname "${DEEPWMH_BIN}")"
shopt -s nullglob
IMAGES=("${DEEPWMH_DIR}"/deepwmh_1.0.1_*.simg)
if [ "${#IMAGES[@]}" -ne 1 ]; then
  echo "Expected one DeepWMH 1.0.1 image beside its module wrapper" >&2
  exit 1
fi
SIMG="${IMAGES[0]}"
MODEL_RW="${ATTEMPT_DIR}/deepwmh_model_rw"
mkdir -p "${MODEL_RW}"
singularity --silent exec "${SIMG}" cp -r /opt/deepwmh-model/. "${MODEL_RW}/"
export neurodesk_singularity_opts="--bind ${MODEL_RW}:/opt/deepwmh-model"
```

Unset `neurodesk_singularity_opts` afterwards; the bind is specific to this
image and later QC steps run in other containers. Report this defect upstream to
the Neurodesk container recipe rather than treating it as a user error.

## Resources (measured, not estimated)

Measured on one case (256 x 232 x 48, 1 x 1 x 3 mm FLAIR), `deepwmh/1.0.1`,
CPU-only, 8 CPUs, 24 GB request, Slurm job COMPLETED `0:0`:

| Quantity | Value |
|---|---|
| DeepWMH wall time | 994 s (~16.6 min) |
| Full job elapsed | 17:05 |
| Peak memory | not recorded — this cluster's `sacct` returns empty `MaxRSS` |

A 24 GB / 8 CPU request completed within a 6 h allocation in the tested
environment. Peak memory remains unmeasured, so keep a generous `--mem` rather
than tightening it on a guess.

**GPU is optional, not required.** The reference sheet previously claimed the CLI
documents no CPU path; that is wrong. `-g -1` / `--gpu -1` is the documented
CPU-only mode, and it is the *only* eligible mode on a cluster without GPUs
(`sinfo` GRES `(null)`; `torch.cuda.is_available()` False inside the container).
Allow for a long CPU run; measured elapsed time depends on image size and
cluster. Harmless
`torch.cuda.amp` deprecation and "CUDA is not available. Disabling" warnings are
emitted on the CPU path.

## Input and invocation

- Input: one unmasked 3D T2-FLAIR NIfTI (`.nii` or `.nii.gz`).
- T1w is not used.
- Do not pre-skull-strip: final field-of-view masking is part of the documented
  pipeline.
- Retain N4 correction. Use `--skip-bfc` only if the supplied FLAIR is already
  demonstrably bias-corrected and the task requires that deviation; the module
  help warns it noticeably degrades accuracy under strong inhomogeneity.

```bash
module load deepwmh/1.0.1
CASE_NAME="${CASE_NAME:?set a filesystem-safe case name}"
mkdir -p "${ATTEMPT_DIR}/deepwmh"
export neurodesk_singularity_opts="--bind ${MODEL_RW}:/opt/deepwmh-model"
deepwmh \
  --input-images "${FLAIR}" \
  --case-names "${CASE_NAME}" \
  --output-folder "${ATTEMPT_DIR}/deepwmh" \
  --gpu -1
unset neurodesk_singularity_opts
CANDIDATE_MASK="${ATTEMPT_DIR}/deepwmh/002_Segmentations/003_postproc_fov/${CASE_NAME}.nii.gz"
```

Use full option names to make the retained script self-explanatory. Note that
`--gpu` takes an index, and `-1` selects CPU. Resolve the helper interpreter
before loading the module, and retain the module probe, the invocation, SLURM
accounting, logs, and expected output paths.

## Outputs and validation

| Path under the output folder | Meaning | Use |
|---|---|---|
| `001_Preprocessed_Images/<case>_0000.nii.gz` | N4-corrected FLAIR | Diagnostic context, good QC underlay |
| `002_Segmentations/001_raw/<case>.nii.gz` | Raw nnU-Net mask | Diagnostic only |
| `002_Segmentations/002_postproc_3mm/<case>.nii.gz` | Mask after internal small-component removal | Diagnostic only |
| `002_Segmentations/003_postproc_fov/<case>.nii.gz` | Mask after ROBEX field-of-view restriction | Publication candidate |
| `003_Previews/<case>.gif` | Tool-generated preview | Supplementary QC only |

All three mask stages are written on the exact input FLAIR grid — verified by
comparing `dim1-3` and `pixdim1-3` against the input. Verify that the final
candidate is binary, non-empty, and on that grid. Note that the two
post-processed stages carry float round-off: their nonzero value is
`1.0000000591`, not exactly `1.0`. A strict `== 1` equality test will wrongly
call them non-binary; threshold at `> 0.5` instead.

Independently run lesion QC: the internal ROBEX step and GIF do not replace the
output-grid brain-containment check or the standard PNG overlay.

The fixed removal of small components can suppress genuine punctate WMH. Record
raw-versus-final volume and component counts so a good-looking final mask does
not hide that loss. Do not restore components with handwritten morphology.

**Count components with `scipy.ndimage.label`, not `fsl-cluster`.** Validate
component counts with a documented connected-component implementation. Do not
use a system command named `cluster` without confirming that it is the FSL
binary; other packages install a command with that name.

## Known signatures

| Signature | Interpretation |
|---|---|
| `OSError: [Errno 30] Read-only file system` under `/opt/deepwmh-model` | Expected without the writable-model bind above; not a data problem |
| Missing `nnUNet/` below the model root | Weights were not installed using the expected layout |
| Stock nnU-Net import or planner errors | Wrong nnU-Net distribution; the DeepWMH fork is required |
| `torch.cuda.amp` warnings / "CUDA is not available. Disabling" | Normal on the `-g -1` CPU path |
| Strong-bias FLAIR run with `--skip-bfc` | Method deviation with increased domain-shift risk |
| Many raw punctate components disappear in `002_postproc_3mm` | Internal small-lesion filtering, not proof they were false positives |

Retain the module/help probe, model provenance, command, Slurm accounting,
stdout/stderr, all three mask stages, preview, publisher JSON, and lesion-QC
artifacts.
