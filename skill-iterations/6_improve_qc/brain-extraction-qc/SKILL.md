---
name: brain-extraction-qc
description: >
  Validate brain extraction / skull stripping results. Generate a QC PNG mosaic,
  perform AI visual evaluation against a structured rubric, and produce a matching
  human verification form for reliability comparison. Invoke after brain extraction
  completes, or standalone on any existing brain mask with "check brain extraction",
  "QC the mask", "validate skull strip", "review brain extraction", "evaluate
  the mask", or "brain-extraction-qc". Also invoke when the user references a
  file ending in `_brain.nii.gz`, `_mask.nii.gz`, or `_brain_mask.nii.gz`
  and asks to check, review, or validate it.
---

# Skill: brain-extraction-qc

Validate brain extraction results by generating two visual QC products: a Python
PNG mosaic with mask overlay and an AFNI `@chauffeur_afni` PNG with an edge-only
outline of the brain mask over the anatomical image. Visually evaluate both PNGs
using AI vision, then save a paired human verification form so that AI-human
agreement can be measured over time.

## Steps

1. **Identify inputs**

   Read the invocation arguments or current user request for: (1) original
   NIfTI path, (2) brain mask NIfTI path, (3) optional output prefix (used for
   naming QC files). If arguments are missing, ask the user to provide them.

   Verify both files exist:
   ```bash
   ls "<original_path>" "<mask_path>"
   ```
   Stop and report any missing file. Do not proceed.

   Infer the tool name from context or the mask filename if possible (used for
   output file naming). Default to `unknown-tool` if not determinable.

2. **Generate the Python QC PNG**

   Load `references/qc-generation.md` from this skill directory for the full
   Python script. Write it to a temporary file `qc_brain_extraction.py` in the
   current directory (overwrite if it exists already).

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
   fraction, and mask symmetry diagnostics) to stdout — capture and retain these
   for the evaluation report.

   Verify the PNG was produced:
   ```bash
   ls "<qc_png_path>"
   ```
   If the file is absent or empty, stop and report that the Python QC script
   failed to produce output. Do not proceed to Step 3.

3. **Generate AFNI outline QC PNG**

   First confirm AFNI availability if this has not already been done in the
   current session:
   ```bash
   module spider afni
   ```
   Use the newest available pinned version unless a project requires a different
   version. In the current Neurodesk environment, `afni/26.0.07` is available.

   Load `references/afni-outline-qc.md` from this skill directory for the full
   bash script template. Write it to:
   ```
   analysis_01_brainmask_outline_qc.sh
   ```

   Construct these output paths using the same `$TIMESTAMP` from Step 2:
   ```
   qc/<output_prefix>_<tool>_${TIMESTAMP}_mask_edge.nii.gz
   qc/<output_prefix>_<tool>_${TIMESTAMP}_afni_outline_qc.png
   ```

   Edit the script variables at the top so they point to:
   - original anatomical image
   - brain mask
   - edge mask output
   - AFNI outline PNG prefix/path
   - pinned AFNI module version

   Run the script according to the active project/environment instructions.

   Verify the AFNI outline PNG exists and is non-empty:
   ```bash
   ls -lh "<afni_outline_qc_png>"
   ```
   If the file is absent or empty, stop and report that AFNI outline QC failed.
   Do not proceed to Step 4.

4. **AI visual evaluation**

   Load `references/ai-evaluation-criteria.md` from this skill directory to
   review the rubric definitions before evaluating.

   The Python QC PNG was verified to exist at the end of Step 2, and the AFNI
   outline QC PNG was verified to exist at the end of Step 3. Open and visually
   inspect both images using the image-viewing capability available in the
   current agent/runtime.

   Examine the image carefully: check each plane (axial, coronal, sagittal),
   inspect the filled mask overlay in the Python PNG, inspect the edge-only
   mask outline in the AFNI PNG, and assess each criterion below. Do not infer
   from metadata alone — the visual read is required.

   Produce the following structured report, filling in all fields:

   ```markdown
   ## AI Brain Extraction QC

   **Subject:** <output_prefix>
   **Tool:** <tool>
   **Timestamp:** <YYYYMMDD-HHMMSS>
   **Original image:** <original_path>
   **Brain mask:** <mask_path>
   **Python QC PNG:** <qc_png_path>
   **AFNI outline QC PNG:** <afni_outline_qc_png>

   ### Quantitative
   | Metric | Value | Reference range |
   |--------|-------|-----------------|
   | Brain volume | X cm³ | 900–1800 cm³ (adult T1w) |
   | Voxel count | N | — |
   | Coverage fraction | X% | 95–105% of expected |
   | Max half-mask imbalance | X% on <axis> | <10% expected; >15% concerning |
   | Max centroid offset | X% of FOV on <axis> | <5% expected; >8% concerning |
   | Max bbox margin imbalance | X% on <axis> | <8% expected; >12% concerning |

   ### Visual Criteria
   | Criterion | Rating | Notes |
   |-----------|--------|-------|
   | No residual skull or scalp signal | Pass / Borderline / Fail | <observation from filled overlay and AFNI outline> |
   | No excessive tissue loss at poles (frontal, temporal, occipital) | Pass / Borderline / Fail | <observation from filled overlay and AFNI outline> |
   | Symmetric left-right and anterior-posterior coverage | Pass / Borderline / Fail | <observation; explicitly mention L/R and A/P balance, any half-mask imbalance warnings, whether midline slices look centered, and whether the AFNI outline tracks both hemispheres evenly> |
   | No internal holes or disconnected mask regions | Pass / Borderline / Fail | <observation from filled overlay and AFNI outline> |
   | Boundary tightness (not over-dilated into dura/CSF) | Pass / Borderline / Fail | <observation from filled overlay and AFNI outline; outline should hug the brain edge without including skull/scalp or cutting through cortex> |

   ### Overall Verdict
   **<Pass / Borderline / Fail>** — Confidence: <High / Medium / Low>

   ### Notes
   <Free-text observations about image quality, unusual features, or artefacts>

   ### Recommended action
   <none | re-run with adjusted parameters: <suggest specific flag changes> | manual mask editing recommended>
   ```

5. **Save AI evaluation**

   Write the completed report to:
   ```
   qc/<output_prefix>_<tool>_<timestamp>_ai_eval.md
   ```

6. **Write human verification form**

   Load `references/human-verification-form.md` from this skill directory for
   the template. Write a blank (unfilled) instance to:
   ```
   qc/<output_prefix>_<tool>_<timestamp>_human_eval.md
   ```
   The criterion labels must be identical to those in the AI evaluation table
   so that agreement can be computed later.

   Tell the user:
   > "Please open `qc/<...>_qc.png` and `qc/<...>_afni_outline_qc.png` to
   > review the extraction visually, then fill in `qc/<...>_human_eval.md` with
   > your assessment. The AI evaluation is at `qc/<...>_ai_eval.md` for
   > comparison. Use identical ratings (Pass / Borderline / Fail) so agreement
   > can be scored."

7. **Summarise**

   Report:
   - Overall AI verdict and confidence
   - Path to the Python QC PNG and AFNI outline QC PNG
   - Any criteria rated Borderline or Fail, with the specific recommendation
   - Reminder that the human form needs to be filled in

## Constraints

- ALWAYS visually inspect both the Python QC PNG and the AFNI outline QC PNG
  before writing the evaluation — never fill in criteria from metadata or
  quantitative stats alone.
- Keep AFNI commands in `analysis_01_brainmask_outline_qc.sh` with a pinned
  `module load afni/<version>` line. Follow the active project/environment
  instructions for how that script is run.
- Treat symmetry conservatively. A mask with clear consistent left-right or
  anterior-posterior imbalance must not receive an overall Pass, even if other
  criteria look acceptable.
- ALWAYS save both `_ai_eval.md` and `_human_eval.md` before reporting complete.
- The criterion labels in the AI eval and the human form MUST be identical word-
  for-word — this is required for downstream agreement scoring.
- If brain volume is outside 900–1800 cm³ for an adult T1w scan, flag it
  explicitly in the Quantitative section notes even if the visual rating is Pass.
- If the QC script reports `WARNING: symmetry`, the symmetry criterion must be
  Borderline or Fail unless the visual review gives a concrete anatomy,
  acquisition, or field-of-view reason why the warning is expected.
- Confidence should reflect actual uncertainty: use Low when image quality,
  contrast, or unusual anatomy makes visual criteria hard to assess.
- Do not delete `qc_brain_extraction.py` after running — it serves as a
  reproducible record of exactly which QC script was used.
