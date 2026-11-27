#!/bin/bash
# Render a brain mask as a crisp single-voxel outline over the anatomical image
# using AFNI @chauffeur_afni, and concatenate the three planes into one PNG.
#
# An outline beats a filled overlay for QC because a filled mask hides the very
# thing you are checking: where exactly the boundary sits. A translucent red
# blob looks fine whether the edge is on the pial surface or 4mm out in the
# dura. An outline makes that difference obvious.
#
# This script is parameterised so it can be run as-is -- no editing required.
#
# Usage:
#   analysis_XX_brainmask_outline_qc.sh -a ANAT -m MASK -o OUT.png
#                                       [-x MONTX] [-y MONTY]
#
# Discover versions first with: module spider afni

set -euo pipefail

MONTX=5                    # slices across, per plane
MONTY=3                    # rows, per plane -> MONTX*MONTY slices per plane
ANAT=""; MASK=""; OUTLINE_PNG=""

usage() { sed -n '2,20p' "$0"; exit 1; }

while getopts "a:m:o:x:y:h" opt; do
  case "$opt" in
    a) ANAT="$OPTARG" ;;
    m) MASK="$OPTARG" ;;
    o) OUTLINE_PNG="$OPTARG" ;;
    x) MONTX="$OPTARG" ;;
    y) MONTY="$OPTARG" ;;
    h|*) usage ;;
  esac
done

[[ -z "$ANAT" || -z "$MASK" || -z "$OUTLINE_PNG" ]] && usage
[[ -f "$ANAT" ]] || { echo "ERROR: anat not found: $ANAT" >&2; exit 2; }
[[ -f "$MASK" ]] || { echo "ERROR: mask not found: $MASK" >&2; exit 2; }

command -v @chauffeur_afni >/dev/null || {
  echo "ERROR: load afni/26.0.07 in the parent Slurm script before calling this helper" >&2
  exit 2
}

OUTDIR="$(dirname "${OUTLINE_PNG}")"
mkdir -p "${OUTDIR}"
[[ ! -e "${OUTLINE_PNG}" ]] || {
  echo "ERROR: refusing to overwrite existing outline: ${OUTLINE_PNG}" >&2
  exit 2
}

WORKDIR="$(mktemp -d "${OUTDIR}/afni_outline_work_XXXXXX")"
trap 'rm -rf "$WORKDIR"' EXIT
EDGE_MASK="${WORKDIR}/mask_edge.nii.gz"

MASK_BIN="${WORKDIR}/mask_binary.nii.gz"
MASK_ERO="${WORKDIR}/mask_eroded.nii.gz"
CHAUFFEUR_PREFIX="${WORKDIR}/outline_chauffeur"

echo "Anatomical : ${ANAT}"
echo "Brain mask : ${MASK}"
echo "Edge mask  : ${EDGE_MASK}"
echo "Outline PNG: ${OUTLINE_PNG}"
echo "Montage    : ${MONTX} x ${MONTY} slices per plane"

# Binarise so the edge depends on mask geometry only, not on mask datatype or
# on any soft/probabilistic values a tool may have written.
3dcalc -overwrite -a "${MASK}" -expr 'step(a-0.5)' -datum byte -prefix "${MASK_BIN}"

# Build the outline as (mask - eroded mask). This yields an exactly one-voxel
# binary shell. 3dedge3 is an alternative but returns a continuous gradient
# whose threshold is arbitrary, which makes the rendered line thickness vary
# with intensity -- harder to read and harder to compare between subjects.
3dmask_tool -overwrite -input "${MASK_BIN}" -dilate_input -1 -prefix "${MASK_ERO}"
3dcalc -overwrite -a "${MASK_BIN}" -b "${MASK_ERO}" -expr 'step(a-b)' \
       -datum byte -prefix "${EDGE_MASK}"

NEDGE=$(3dBrickStat -count -non-zero "${EDGE_MASK}" 2>/dev/null || echo 0)
echo "Edge voxels: ${NEDGE}"
if [[ "${NEDGE}" -lt 100 ]]; then
  echo "ERROR: edge mask has only ${NEDGE} voxels; mask is empty or degenerate" >&2
  exit 3
fi

# Crop both volumes to the mask bounding box plus a margin before rendering.
# @chauffeur_afni spreads its slices across the whole field of view, so on a
# typical T1 with neck coverage a third of the montage panels come back empty
# or show only scalp. Cropping first means every panel carries brain, which is
# what makes a fixed-size montage worth reading.
BOX_REF="${WORKDIR}/box_ref.nii.gz"
ANAT_CROP="${WORKDIR}/anat_crop.nii.gz"
EDGE_CROP="${WORKDIR}/edge_crop.nii.gz"

3dAutobox -overwrite -input "${MASK_BIN}" -npad 12 -prefix "${BOX_REF}"
3dresample -overwrite -master "${BOX_REF}" -rmode Li \
           -input "${ANAT}" -prefix "${ANAT_CROP}"
3dresample -overwrite -master "${BOX_REF}" -rmode NN \
           -input "${EDGE_MASK}" -prefix "${EDGE_CROP}"

# Render the three planes. -save_ftype PNG matters: without it @chauffeur_afni
# can emit .ppm, which most image viewers and vision models will not open.
@chauffeur_afni                       \
  -ulay        "${ANAT_CROP}"         \
  -olay        "${EDGE_CROP}"         \
  -prefix      "${CHAUFFEUR_PREFIX}"  \
  -save_ftype  PNG                    \
  -set_subbricks 0 0 0                \
  -montx "${MONTX}" -monty "${MONTY}" \
  -set_xhairs  OFF                    \
  -label_mode  1                      \
  -label_size  3                      \
  -opacity     9                      \
  -blowup      2                      \
  -pbar_posonly                       \
  -func_range  1                      \
  -thr_olay    0.5                    \
  -cbar        Reds_and_Blues_Inv

# Concatenate axial + coronal + sagittal into a single image, so a reviewer
# cannot accidentally inspect only one plane and call the job done.
mapfile -t ORIENT_PNGS < <(
  find "${WORKDIR}" -maxdepth 1 -type f \
    \( -name 'outline_chauffeur*axi*.png' -o \
       -name 'outline_chauffeur*cor*.png' -o \
       -name 'outline_chauffeur*sag*.png' \) | sort
)

if [[ "${#ORIENT_PNGS[@]}" -lt 3 ]]; then
  echo "ERROR: expected axial, coronal and sagittal PNGs from @chauffeur_afni" >&2
  find "${WORKDIR}" -maxdepth 1 -type f -print >&2
  exit 4
fi

# 2dcat infers its output format from the prefix extension, but not every AFNI
# build can write PNG -- where it cannot, it silently emits <prefix>.ppm instead
# and returns success. Left unhandled that produces a stray .ppm and no PNG,
# which is how QC images end up unreadable by viewers and vision models. So
# concatenate to PPM deliberately, then convert.
CAT_PPM="${WORKDIR}/outline_cat.ppm"
2dcat -gap 5 -gap_col 150 180 150 -nx 1 -ny 3 \
      -prefix "${CAT_PPM}" "${ORIENT_PNGS[@]}"

# 2dcat may append its own extension; take whatever actually landed.
CAT_OUT="$(find "${WORKDIR}" -maxdepth 1 -name 'outline_cat*' -type f | head -1)"
if [[ -z "${CAT_OUT}" || ! -s "${CAT_OUT}" ]]; then
  echo "ERROR: 2dcat produced no output" >&2
  exit 5
fi

PNG_TMP="${WORKDIR}/outline.png"
CONVERT_PYTHON="${HELPER_PYTHON:?set HELPER_PYTHON in the parent Slurm script before loading AFNI}"
"${CONVERT_PYTHON}" - "${CAT_OUT}" "${PNG_TMP}" <<'PY'
from pathlib import Path
import sys
from PIL import Image

source, destination = map(Path, sys.argv[1:3])
with Image.open(source) as image:
    image.load()
    image.convert("RGB").save(destination, format="PNG")
with Image.open(destination) as image:
    if image.format != "PNG" or image.width == 0 or image.height == 0:
        raise SystemExit("ERROR: converted outline is not a valid PNG")
PY

if [[ ! -s "${PNG_TMP}" ]]; then
  echo "ERROR: outline PNG missing or empty: ${PNG_TMP}" >&2
  exit 5
fi

mv -- "${PNG_TMP}" "${OUTLINE_PNG}"
echo "AFNI outline QC PNG saved: ${OUTLINE_PNG}"
