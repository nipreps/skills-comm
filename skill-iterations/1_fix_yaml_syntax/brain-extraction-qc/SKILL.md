---
name: brain-extraction-qc
description: >
  Validate brain extraction / skull stripping results. Generate a QC PNG mosaic,
  perform AI visual evaluation against a structured rubric, and produce a matching
  human verification form for reliability comparison. Invoke after brain extraction
  completes, or standalone on any existing brain mask with "check brain extraction",
  "QC the mask", "validate skull strip", "review brain extraction", "evaluate
  the mask", or /brain-extraction-qc. Also invoke when the user references a
  file ending in `_brain.nii.gz`, `_mask.nii.gz`, or `_brain_mask.nii.gz`
  and asks to check, review, or validate it.
allowed-tools: Read, Bash, Glob, Write
---

# Skill: brain-extraction-qc

Validate brain extraction results through three steps: generate a PNG mosaic
with mask overlay, visually evaluate the PNG using AI vision, and save a paired
human verification form so that AI-human agreement can be measured over time.

## Steps

1. **Identify inputs**

   Read `$ARGUMENTS` for: (1) original NIfTI path, (2) brain mask NIfTI path,
   (3) optional output prefix (used for naming QC files). If arguments are
   missing, ask the user to provide them.

   Verify both files exist:
   ```bash
   ls "<original_path>" "<mask_path>"
   ```
   Stop and report any missing file. Do not proceed.

   Infer the tool name from context or the mask filename if possible (used for
   output file naming). Default to `unknown-tool` if not determinable.

2. **Generate the QC PNG**

   Load `${CLAUDE_PLUGIN_ROOT}/references/qc-generation.md` for the full Python
   script. Write it to a temporary file `qc_brain_extraction.py` in the current
   directory (overwrite if it exists already).

   Create the output directory:
   ```bash
   mkdir -p qc/
   ```

   Before running the script, verify required Python dependencies are available:
   ```bash
   python3 -c "import nibabel, matplotlib"
   ```
   If this fails, tell the user to run `pip install nibabel matplotlib` and
   verify the import succeeds before proceeding.

   Capture the timestamp once and store it — this exact value must be reused
   verbatim in Steps 4 and 5 to ensure all three output files share the same
   timestamp:
   ```bash
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   echo "$TIMESTAMP"
   ```

   Construct the output filename using `$TIMESTAMP`:
   ```
   qc/<output_prefix>_<tool>_${TIMESTAMP}_qc.png
   ```

   Run the script:
   ```bash
   python3 qc_brain_extraction.py "<original_path>" "<mask_path>" "<qc_png_path>"
   ```

   The script prints quantitative stats (brain volume cm³, voxel count, coverage
   fraction) to stdout — capture and retain these for the evaluation report.

   Verify the PNG was produced:
   ```bash
   ls "<qc_png_path>"
   ```
   If the file is absent or empty, stop and report that the QC script failed to
   produce output. Do not proceed to Step 3.

3. **AI visual evaluation**

   Load `${CLAUDE_PLUGIN_ROOT}/references/ai-evaluation-criteria.md` to review
   the rubric definitions before evaluating.

   The PNG was verified to exist at the end of Step 2. Read it using the Read tool:
   ```
   Read("<qc_png_path>")
   ```

   Examine the image carefully: check each plane (axial, coronal, sagittal),
   inspect the mask boundary (red overlay), and assess each criterion below.
   Do not infer from metadata alone — the visual read is required.

   Produce the following structured report, filling in all fields:

   ```markdown
   ## AI Brain Extraction QC

   **Subject:** <output_prefix>
   **Tool:** <tool>
   **Timestamp:** <YYYYMMDD-HHMMSS>
   **Original image:** <original_path>
   **Brain mask:** <mask_path>

   ### Quantitative
   | Metric | Value | Reference range |
   |--------|-------|-----------------|
   | Brain volume | X cm³ | 900–1800 cm³ (adult T1w) |
   | Voxel count | N | — |
   | Coverage fraction | X% | 95–105% of expected |

   ### Visual Criteria
   | Criterion | Rating | Notes |
   |-----------|--------|-------|
   | No residual skull or scalp signal | Pass / Borderline / Fail | <observation> |
   | No excessive tissue loss at poles (frontal, temporal, occipital) | Pass / Borderline / Fail | <observation> |
   | Symmetric left-right and anterior-posterior coverage | Pass / Borderline / Fail | <observation> |
   | No internal holes or disconnected mask regions | Pass / Borderline / Fail | <observation> |
   | Boundary tightness (not over-dilated into dura/CSF) | Pass / Borderline / Fail | <observation> |

   ### Overall Verdict
   **<Pass / Borderline / Fail>** — Confidence: <High / Medium / Low>

   ### Notes
   <Free-text observations about image quality, unusual features, or artefacts>

   ### Recommended action
   <none | re-run with adjusted parameters: <suggest specific flag changes> | manual mask editing recommended>
   ```

4. **Save AI evaluation**

   Write the completed report to:
   ```
   qc/<output_prefix>_<tool>_<timestamp>_ai_eval.md
   ```

5. **Write human verification form**

   Load `${CLAUDE_PLUGIN_ROOT}/references/human-verification-form.md` for the
   template. Write a blank (unfilled) instance to:
   ```
   qc/<output_prefix>_<tool>_<timestamp>_human_eval.md
   ```
   The criterion labels must be identical to those in the AI evaluation table
   so that agreement can be computed later.

   Tell the user:
   > "Please open `qc/<...>_qc.png` to review the extraction visually, then
   > fill in `qc/<...>_human_eval.md` with your assessment. The AI evaluation
   > is at `qc/<...>_ai_eval.md` for comparison. Use identical ratings
   > (Pass / Borderline / Fail) so agreement can be scored."

6. **Summarise**

   Report:
   - Overall AI verdict and confidence
   - Path to the QC PNG
   - Any criteria rated Borderline or Fail, with the specific recommendation
   - Reminder that the human form needs to be filled in

## Constraints

- ALWAYS use the Read tool to visually inspect the PNG before writing the
  evaluation — never fill in criteria from metadata or quantitative stats alone.
- ALWAYS save both `_ai_eval.md` and `_human_eval.md` before reporting complete.
- The criterion labels in the AI eval and the human form MUST be identical word-
  for-word — this is required for downstream agreement scoring.
- If brain volume is outside 900–1800 cm³ for an adult T1w scan, flag it
  explicitly in the Quantitative section notes even if the visual rating is Pass.
- Confidence should reflect actual uncertainty: use Low when image quality,
  contrast, or unusual anatomy makes visual criteria hard to assess.
- Do not delete `qc_brain_extraction.py` after running — it serves as a
  reproducible record of exactly which QC script was used.
