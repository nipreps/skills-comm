---
name: brain-extraction
description: >
  Perform brain extraction (skull stripping) on an MRI image in the Neurodesk
  environment. Invoke on "skull strip", "brain extraction", "remove skull",
  "strip the brain", "BET", "antsBrainExtraction", "mri_synthstrip", "HD-BET",
  "3dSkullStrip", "synthstrip", "brain mask", "create brain mask",
  "whole brain mask", "mask the brain", "strip the skull",
  or "brain-extraction". Also invoke when the user says they want to isolate
  brain tissue, remove non-brain voxels, or prepare a brain mask for
  downstream registration or segmentation.
---

# Skill: brain-extraction

Guide the user through brain extraction (skull stripping) in the Neurodesk
environment: identify the input, present tool options without bias, write a
SLURM-compliant bash script, submit it, and hand off to QC on completion.

## Nipoppy datasets

If the input lives in a Nipoppy dataset (a `config.json` and `manifest.tsv` are present at the
dataset root), prefer **scaffolding a tool-specific `brainextraction` Nipoppy pipeline** into
the user's project instead of running a standalone SLURM script. The user then owns a
Nipoppy-tracked pipeline they can version and share, and outputs land in the standard
derivatives layout where `track-processing` and QC Studio find them.

Run this as a sub-flow of the steps below — still present the tool menu (Step 3) and let the
user choose; the choice selects the recipe rather than a `module load`:

1. **Confirm naming.** Ask for the pipeline **name** (default `brainextraction-<tool>`) and
   **version** (default `1.0.0`) so the user can version and share it.
2. **Render the bundle.** Read `../nipoppy-pipelines/template/` and the chosen tool's section in
   `../nipoppy-pipelines/tool-recipes.md`, substitute every `{{TOKEN}}`, and write the five files
   (`config`, `descriptor`, `invocation`, `tracker`, `hpc`) into the user's project, e.g.
   `<dataset>/pipelines/<name>/`. The rendered files MUST be valid JSON (no trailing commas, no
   leftover `{{...}}`). Keep the standardized output names — never tool-specific names.
3. **Validate & install.**
   ```bash
   nipoppy pipeline validate <dataset>/pipelines/<name>
   nipoppy pipeline install  <dataset>/pipelines/<name>
   ```
4. **Run & track.**
   ```bash
   nipoppy process          --pipeline <name> --pipeline-version <version>
   nipoppy track-processing --pipeline <name> --pipeline-version <version>
   ```
5. **Hand off to QC.** Outputs land at
   `derivatives/<name>/<version>/output/<sub>/<ses>/anat/<sub>_<ses>_desc-brain_mask.nii.gz`
   (and `_desc-brain_T1w.nii.gz`). Invoke `brain-extraction-qc` with those paths; it renders the
   matching QC Studio view from `../qc-studio/template/qc.json`.

See `../nipoppy-pipelines/README.md` for the template, tokens, and the package/version/share
path. The standalone SLURM workflow below remains the fallback for data that is not in a Nipoppy
dataset.

## Steps

1. **Identify the input image**

   Read the invocation arguments or current user request for a NIfTI path. If
   none is given, ask the user:
   > "Please provide the path to your input NIfTI image (e.g., `sub-01/anat/sub-01_T1w.nii.gz`)."

   Once a path is provided, verify it exists:
   ```bash
   ls "<input_path>"
   ```
   If missing, stop and report the exact path that was not found. Do not proceed.

   Check the file extension ends in `.nii` or `.nii.gz`. If not, warn the user
   that the file may not be a valid NIfTI and ask them to confirm.

   Check that the input is a 3D volume, not a 4D timeseries:
   ```bash
   python3 -c "import nibabel as nib; img = nib.load('<input_path>'); d4 = img.shape[3] if len(img.shape) > 3 else 1; print('dim4=' + str(d4))"
   ```
   If `dim4 > 1`, warn the user:
   > "This appears to be a 4D volume (dim4 = N). Brain extraction expects a 3D
   > anatomical image. Please confirm you intended this file, or select a
   > single-volume NIfTI before proceeding."
   Do not proceed past Step 1 until the user confirms the correct input.

2. **Identify the output location**

   If an output prefix was given as the second argument, use it. Otherwise,
   default to the same directory as the input with `_brain` appended before the
   extension (e.g., `sub-01/anat/sub-01_T1w_brain`). Confirm with the user or
   infer silently if the context is clear.

   Determine the output directory and set `OUT_DIR` for use in the script.

3. **Present tool options**

   Load `references/tool-comparison.md` from this skill directory and present
   the comparison table to the user. Include columns: Tool, Method, Speed,
   Template Required, GPU Optional, Best For.

   After presenting the table, ask:
   > "Which tool would you like to use? If you'd like a recommendation based on
   > your data type or constraints, let me know."

   Do not express a preference unprompted. If the user asks for a recommendation:
   - Default anatomy T1w, no special constraints → FSL BET (fast, universal)
   - Difficult anatomy, low contrast, or high accuracy required → FreeSurfer mri_synthstrip or HD-BET
   - Multi-modal (T2, FLAIR, DWI) → mri_synthstrip or SynthStrip
   - Need maximum accuracy and have time → ANTs antsBrainExtraction
   - Functional / EPI data → AFNI 3dSkullStrip

   Wait for the user to confirm a tool before proceeding.

   After the user selects a tool, verify it is available on this cluster and
   capture the exact installed version:
   ```bash
   module spider <tool_name>
   ```
   Parse the output for the version string matching the tool reference. If a
   newer version is available, note it to the user. If the reference version is
   absent, ask the user which available version to use. Update the `module load`
   line in the script to match the confirmed version before proceeding.

4. **Write the SLURM script**

   **ANTs special case (check first, before writing anything):** If the user
   selected ANTs, immediately verify the template exists at the path specified
   in `references/ants-brain-extraction.md`:
   ```bash
   ls "<template_path>"
   ```
   If it does not exist, pause and offer to add a DataLad or wget download step
   for the OASIS-30 template. Do not proceed to write the ANTs script until the
   template is confirmed present.

   Load the reference file for the chosen tool:
   - FSL BET → `references/fsl-bet.md`
   - ANTs → `references/ants-brain-extraction.md`
   - FreeSurfer mri_synthstrip or SynthStrip → `references/synthstrip.md`
   - HD-BET → `references/hd-bet.md`
   - AFNI 3dSkullStrip → `references/afni-3dskullstrip.md`

   Determine the next available script number with zero-padded two-digit numbering:
   ```bash
   LAST=$(ls analysis_[0-9][0-9]_*.sh 2>/dev/null | sort | tail -1)
   N=$([ -z "$LAST" ] && echo "01" || printf "%02d" $(( ${LAST:9:2} + 1 )))
   ```
   Use `$N` as the script number (e.g., `01`, `02`, `03`).

   Ask the user:
   > "Does your cluster require `--partition` or `--account` in the SLURM header?
   > If so, please provide the values; otherwise I'll omit them."

   Write a script named `analysis_<N>_brain_extraction.sh` containing:
   - Full SLURM header with resource values from the tool reference (add
     `--partition` / `--account` if provided by the user)
   - `mkdir -p logs/` and `mkdir -p "$OUT_DIR"/`
   - `module load <tool>/<pinned-version>` (exact version confirmed in Step 3)
   - The extraction command with recommended default parameters
   - A clear comment above each command block explaining what it does

   Show the complete script to the user and ask:
   > "Does this script look correct? Reply 'yes' to submit or request changes."

5. **Submit the job**

   After the user confirms the script is correct, ask:
   > "Would you like to record this analysis with DataLad for provenance? If
   > so, I can add the appropriate DataLad provenance step. Reply 'yes' to use
   > DataLad, or 'no' to submit directly."

   If yes, use the local DataLad workflow available in the current environment
   before proceeding. If no, submit directly:
   ```bash
   sbatch analysis_<N>_brain_extraction.sh
   ```
   Capture and report the job ID. Tell the user:
   > "Job submitted — ID: <jobid>
   > Monitor: `squeue -j <jobid>`
   > Logs: `tail -f logs/brain_extraction_<jobid>.out`"

6. **Wait for completion and hand off to QC**

   Tell the user to notify you when the job finishes. Once they confirm,
   first verify the job exited cleanly:
   ```bash
   sacct -j <jobid> --format=JobID,State,ExitCode --noheader
   ```
   If State is not `COMPLETED` or ExitCode is not `0:0`, do not proceed to QC.
   Instead show the last 30 lines of the error log:
   ```bash
   tail -30 logs/brain_extraction_<jobid>.err
   ```
   Report the failure to the user and stop.

   If the job completed successfully, verify the expected output file exists:
   ```bash
   ls "<expected_mask_path>"
   ```
   If the output is absent, stop and instruct the user to check the SLURM log
   for errors before proceeding.

   Once both checks pass:
   - Identify the brain mask output path from the tool reference (it varies by tool)
   - Invoke the brain-extraction-qc workflow with the original image and brain mask:
     > Run `brain-extraction-qc <original_input> <brain_mask> <output_prefix>`

## Constraints

- NEVER run extraction commands directly in the shell. Always write a `.sh`
  script and submit it via `sbatch`.
- ALWAYS show the full script to the user before running `sbatch`.
- ALWAYS name scripts `analysis_<N>_brain_extraction.sh`.
- ALWAYS zero-pad script numbers to two digits (e.g., `01`, `02`, `03`).
- ALWAYS use explicitly versioned `module load` (e.g., `fsl/6.0.7.22`, not `fsl`).
- ALWAYS create `logs/` before submitting so the SLURM output path resolves.
- Do not express tool preference unless explicitly asked.
- If the input is inside a Nipoppy dataset, prefer scaffolding a tool-specific Nipoppy pipeline
  (render from `../nipoppy-pipelines/template/`) over a standalone SLURM script — see the Nipoppy
  datasets section. Always keep the standardized `_desc-brain_mask.nii.gz` /
  `_desc-brain_T1w.nii.gz` output names so the tracker and QC view stay tool-agnostic.
- Do not proceed past Step 1 if the input file does not exist.
- ANTs: never write a script with a template path that has not been verified to exist.
