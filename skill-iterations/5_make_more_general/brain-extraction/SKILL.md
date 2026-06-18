---
name: brain-extraction
description: >
  Perform brain extraction (skull stripping) on an MRI image in a portable
  neuroimaging workflow. Invoke on "skull strip", "brain extraction",
  "remove skull", "strip the brain", "BET", "antsBrainExtraction",
  "mri_synthstrip", "HD-BET", "3dSkullStrip", "synthstrip", "brain mask",
  "create brain mask", "whole brain mask", "mask the brain", "strip the skull",
  or "brain-extraction". Also invoke when the user wants to isolate brain
  tissue, remove non-brain voxels, or prepare a brain mask for downstream
  registration or segmentation.
---

# Skill: brain-extraction

Guide brain extraction in whatever runtime is available: local shell, Conda
environment, container, module-based cluster, or scheduler-backed HPC system.
Do not assume Neurodesk, SLURM, Lmod modules, or any specific install path.

## Steps

1. **Identify the input image**

   Read the request for a NIfTI path. If none is given, ask for one.

   Verify it exists:
   ```bash
   ls "<input_path>"
   ```

   Check that it ends in `.nii` or `.nii.gz`. If not, warn that it may not be a
   NIfTI and ask for confirmation.

   Check that the input is suitable for brain extraction:
   ```bash
   python3 -c "import nibabel as nib; img = nib.load('<input_path>'); print(img.shape)"
   ```
   If it is a 4D timeseries, ask the user whether to extract a single reference
   volume or use a tool appropriate for functional data.

2. **Identify outputs**

   If an output prefix was provided, use it. Otherwise default to the input
   directory with `_brain` appended before the extension. Set `OUT_DIR`,
   `OUTPUT`, and `MASK` or tool-specific equivalents.

3. **Present tool options**

   Load `references/tool-comparison.md` and present the comparison table. Ask
   which tool the user wants. If they ask for a recommendation:
   - Default anatomy T1w, no special constraints -> FSL BET
   - Difficult anatomy, low contrast, or high accuracy needed -> mri_synthstrip or HD-BET
   - Multi-modal T2, FLAIR, DWI, or unusual contrast -> mri_synthstrip
   - Maximum accuracy and a suitable template is available -> ANTs
   - Functional/EPI reference data -> AFNI 3dSkullStrip or 3dAutomask

4. **Discover the runtime**

   After tool selection, verify availability without assuming a platform:
   ```bash
   command -v <executable>
   <executable> --help 2>&1 | head -40
   ```

   If the executable is unavailable, check likely environment mechanisms:
   ```bash
   command -v module >/dev/null && module avail <tool_or_module_name>
   command -v conda >/dev/null && conda env list
   command -v apptainer >/dev/null || command -v singularity >/dev/null || command -v docker >/dev/null
   ```

   Use the reference file for tool-specific executable names and install hints.
   For HD-BET, the executable is usually `hd-bet`; the module/package name may
   be `hdbet`.

5. **Write a reproducible script when appropriate**

   Load the selected reference:
   - FSL BET -> `references/fsl-bet.md`
   - ANTs -> `references/ants-brain-extraction.md`
   - mri_synthstrip / SynthStrip -> `references/synthstrip.md`
   - HD-BET -> `references/hd-bet.md`
   - AFNI 3dSkullStrip -> `references/afni-3dskullstrip.md`

   Determine the next script name:
   ```bash
   LAST=$(ls analysis_[0-9][0-9]_*.sh 2>/dev/null | sort | tail -1)
   N=$([ -z "$LAST" ] && echo "01" || printf "%02d" $(( ${LAST:9:2} + 1 )))
   ```

   Write `analysis_<N>_brain_extraction.sh` with:
   - `#!/usr/bin/env bash` and `set -euo pipefail`
   - input/output variables and `mkdir -p` for output/log directories
   - only the environment setup needed on the current system
   - the selected extraction command
   - output existence checks

   If a scheduler is available and useful for the job, include or create the
   appropriate submission wrapper. Otherwise make the script runnable directly.

6. **Run or submit**

   For short/local jobs, run the script directly after confirming with the user
   when the command is potentially long-running. For scheduler-backed systems,
   submit with the local scheduler command (`sbatch`, `qsub`, `bsub`, etc.) and
   report how to monitor logs/status.

7. **Validate and hand off to QC**

   Verify the expected brain image and mask exist and are non-empty:
   ```bash
   test -s "<expected_output>"
   test -s "<expected_mask>"
   ```

   Then invoke the brain-extraction-qc workflow with:
   `brain-extraction-qc <original_input> <brain_mask> <output_prefix>`.

## Constraints

- Do not assume Neurodesk, SLURM, Lmod modules, DataLad, GPU access, or a fixed
  install path.
- Prefer reproducible scripts for substantive processing, but use the execution
  model that matches the current system.
- Always verify the selected executable or environment before writing final run
  commands.
- Always validate output files before declaring success.
- Do not express a tool preference unless asked or unless context makes a
  recommendation necessary.
- ANTs: never run with a template path that has not been verified to exist.
