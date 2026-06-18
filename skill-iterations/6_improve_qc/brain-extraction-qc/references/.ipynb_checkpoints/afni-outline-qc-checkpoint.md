# AFNI Brain Mask Outline QC Script

Use this template to create `analysis_01_brainmask_outline_qc.sh`. Keep the
AFNI commands in this script with an explicit pinned module load. Run the script
according to the active project/environment instructions.

The script creates an edge-only outline from the brain mask, then overlays that
outline on the anatomical image with AFNI `@chauffeur_afni`. The outline is
more sensitive than a filled transparent mask for detecting shifted masks,
asymmetric coverage, clipped cortex, and skull/scalp inclusion.

## Script

```bash
#!/bin/bash

set -euo pipefail

# Pin the AFNI version discovered with: module spider afni
module load afni/26.0.07

# Edit these variables before running.
ANAT="<original_path>"
MASK="<mask_path>"
EDGE_MASK="qc/<output_prefix>_<tool>_<timestamp>_mask_edge.nii.gz"
OUTLINE_PNG="qc/<output_prefix>_<tool>_<timestamp>_afni_outline_qc.png"

mkdir -p qc

WORKDIR="$(mktemp -d qc/afni_outline_work_XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

MASK_BIN="${WORKDIR}/mask_binary.nii.gz"
MASK_ERODED="${WORKDIR}/mask_eroded.nii.gz"
CHAUFFEUR_PREFIX="${WORKDIR}/outline_chauffeur"

echo "Anatomical image: ${ANAT}"
echo "Brain mask:       ${MASK}"
echo "Edge mask:        ${EDGE_MASK}"
echo "Outline PNG:      ${OUTLINE_PNG}"

# Binarize the mask so edge detection is based on mask geometry only.
3dcalc \
  -overwrite \
  -a "${MASK}" \
  -expr 'step(a)' \
  -datum byte \
  -prefix "${MASK_BIN}"

# Edge detection on the mask: erode one voxel, then subtract eroded interior
# from the original binary mask. The result is a one-voxel shell/outline.
3dmask_tool \
  -overwrite \
  -input "${MASK_BIN}" \
  -dilate_inputs -1 \
  -prefix "${MASK_ERODED}"

3dcalc \
  -overwrite \
  -a "${MASK_BIN}" \
  -b "${MASK_ERODED}" \
  -expr 'step(a)-step(b)' \
  -datum byte \
  -prefix "${EDGE_MASK}"

# Render the edge-only mask over the anatomical image. The outline should track
# the brain boundary closely without entering skull/scalp or cutting cortex.
@chauffeur_afni \
  -ulay "${ANAT}" \
  -olay "${EDGE_MASK}" \
  -prefix "${CHAUFFEUR_PREFIX}" \
  -montx 6 \
  -monty 4 \
  -set_xhairs OFF \
  -label_mode 1 \
  -label_size 3 \
  -opacity 9 \
  -pbar_posonly \
  -func_range 1 \
  -thr_olay 0.5 \
  -cbar ROI_i256 \
  -do_clean

# @chauffeur_afni may append a view suffix to the requested prefix. Preserve a
# stable filename for the skill workflow.
FIRST_PNG="$(find "${WORKDIR}" -maxdepth 1 -name 'outline_chauffeur*.png' | sort | head -n 1)"
if [[ -z "${FIRST_PNG}" ]]; then
  echo "ERROR: @chauffeur_afni did not create a PNG" >&2
  exit 2
fi

cp "${FIRST_PNG}" "${OUTLINE_PNG}"

if [[ ! -s "${OUTLINE_PNG}" ]]; then
  echo "ERROR: outline PNG is missing or empty: ${OUTLINE_PNG}" >&2
  exit 3
fi

echo "AFNI outline QC PNG saved: ${OUTLINE_PNG}"
```

## What To Inspect

Open the AFNI outline PNG alongside the Python filled-mask PNG. The edge-only
outline should:

- follow the cortical and cerebellar boundary closely
- remain centered and symmetric across left/right and anterior/posterior views
- avoid skull, scalp, eyes, dura, and large CSF regions
- avoid cutting through visible grey or white matter
- show a single coherent boundary without disconnected islands

The outline view should be treated as authoritative for boundary placement. If
the filled red overlay looks acceptable but the outline is shifted, asymmetric,
or cuts through cortex, downgrade the relevant visual criteria.
