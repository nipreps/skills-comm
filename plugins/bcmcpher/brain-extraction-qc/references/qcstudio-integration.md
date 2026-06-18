# QC Studio integration for brain extraction

[QC Studio](https://github.com/nipoppy/qc-studio) is a Streamlit app for **interactive
human QC** of neuroimaging outputs inside a Nipoppy dataset. This skill uses it as the
human-rating front end that *augments* the automated AI evaluation — it does not replace
the AI eval or the montage. Load this reference when the brain mask lives in (or can be
copied into) a Nipoppy `derivatives/` tree and the user wants to review it in QC Studio.

The QC view is generated from the tokenized template `qc-studio/template/qc.json` (with its own
`README.md`): the skill substitutes the rendered pipeline's `{{PIPELINE_NAME}}` /
`{{PIPELINE_VERSION}}` (and `{{INPUT_IMAGE_ENTITIES}}`) and writes the result into the user's
project (e.g. `<dataset>/qc-studio/<name>/qc.json`). This file explains how to produce the
inputs it points at and how to launch the viewer.

## `qc.json` schema (`QCTask`)

QC Studio reads a `qc.json` whose root is a dict mapping `<task_name>` → `QCTask`. Fields:

| Field | Type | Required | Feeds panel |
|-------|------|----------|-------------|
| `base_mri_image_path` | str | yes | Niivue 3D base layer |
| `overlay_mri_image_path` | str | no | Niivue 3D overlay |
| `svg_montage_path` | list[str] | no | Montage panel (accepts PNG) |
| `iqm_path` | str | no | QC metrics panel |

All paths are **relative to `--dataset_dir`** and may use the same template variables
nipoppy substitutes at runtime: `[[NIPOPPY_BIDS_PARTICIPANT_ID]]`,
`[[NIPOPPY_BIDS_SESSION_ID]]`.

## Brain-extraction task → outputs mapping

For the `brain_extraction_qc` task, map fields to the pipeline + QC outputs:

| `QCTask` field | Points at |
|----------------|-----------|
| `base_mri_image_path` | the **original head T1w** in `bids/` (skull visible, so the rater can confirm it is excluded) |
| `overlay_mri_image_path` | `derivatives/<name>/<version>/output/<sub>/<ses>/anat/<sub>_<ses>_desc-brain_mask.nii.gz` |
| `svg_montage_path` | `…/<sub>_<ses>_desc-brain_qc.png` (the 3×9 mosaic from `qc_brain_extraction.py`) |
| `iqm_path` | `…/<sub>_<ses>_desc-brain_iqm.tsv` (the IQM sidecar from `qc_brain_extraction.py`) |

Tokenized template form (`qc-studio/template/qc.json`); the skill substitutes
`{{PIPELINE_NAME}}` / `{{PIPELINE_VERSION}}` / `{{INPUT_IMAGE_ENTITIES}}` when rendering:

```json
{
    "brain_extraction_qc": {
        "base_mri_image_path": "bids/[[NIPOPPY_BIDS_PARTICIPANT_ID]]/[[NIPOPPY_BIDS_SESSION_ID]]/anat/[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]_{{INPUT_IMAGE_ENTITIES}}.nii.gz",
        "overlay_mri_image_path": "derivatives/{{PIPELINE_NAME}}/{{PIPELINE_VERSION}}/output/[[NIPOPPY_BIDS_PARTICIPANT_ID]]/[[NIPOPPY_BIDS_SESSION_ID]]/anat/[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]_desc-brain_mask.nii.gz",
        "svg_montage_path": [
            "derivatives/{{PIPELINE_NAME}}/{{PIPELINE_VERSION}}/output/[[NIPOPPY_BIDS_PARTICIPANT_ID]]/[[NIPOPPY_BIDS_SESSION_ID]]/anat/[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]_desc-brain_qc.png"
        ],
        "iqm_path": "derivatives/{{PIPELINE_NAME}}/{{PIPELINE_VERSION}}/output/[[NIPOPPY_BIDS_PARTICIPANT_ID]]/[[NIPOPPY_BIDS_SESSION_ID]]/anat/[[NIPOPPY_BIDS_PARTICIPANT_ID]]_[[NIPOPPY_BIDS_SESSION_ID]]_desc-brain_iqm.tsv"
    }
}
```

## Producing the QC inputs in the derivatives tree

QC Studio resolves template paths with **no timestamp**, so the montage and IQM must sit at
deterministic, BIDS-style paths next to the mask. Generate them by pointing
`qc_brain_extraction.py` at the derivatives `anat/` dir:

```bash
DERIV="derivatives/<name>/<version>/output/sub-001/ses-01/anat"
python3 qc_brain_extraction.py \
  "bids/sub-001/ses-01/anat/sub-001_ses-01_run-1_T1w.nii.gz" \
  "${DERIV}/sub-001_ses-01_desc-brain_mask.nii.gz" \
  "${DERIV}/sub-001_ses-01_desc-brain_qc.png" \
  "${DERIV}/sub-001_ses-01_desc-brain_iqm.tsv"
```

This is in addition to (not instead of) the timestamped `qc/<…>_qc.png` the skill already
writes for the AI eval — the timestamped copy preserves the AI/human agreement record; the
deterministic copy feeds QC Studio.

## How the QC view should look

QC Studio composes three panels (`ui/constants.py PANEL_CONFIG`: `niivue` and `svg` on by
default, `iqm` off):

- **Panel A — Niivue 3D viewer (primary judgment surface).** Original T1w with the brain
  mask as a semi-transparent red overlay across three synced ortho planes; scroll slices and
  toggle overlay opacity. Best for boundary tightness, residual skull/scalp, pole coverage.
- **Panel B — Montage.** The static 3×9 axial/coronal/sagittal mosaic with red mask overlay
  and a volume/coverage title bar — identical imagery to what the AI eval reads.
- **Panel C — QC metrics.** The IQM TSV: brain volume (cm³), voxel count, coverage %, each
  with reference range and out-of-range flag.

## Rating criteria (keep aligned with the AI eval)

Raters should score the **same five criteria** the AI eval and human form use, so AI/human
agreement stays computable:

1. No residual skull or scalp signal
2. No excessive tissue loss at poles (frontal, temporal, occipital)
3. Symmetric left-right and anterior-posterior coverage
4. No internal holes or disconnected mask regions
5. Boundary tightness (not over-dilated into dura/CSF)

…plus an overall verdict (Pass / Borderline / Fail) and confidence (High / Medium / Low).
These mirror `ai-evaluation-criteria.md` and `human-verification-form.md`.

**Rating capture:** if QC Studio's installed version exposes a configurable rating form,
map these five criteria onto it. If it does not, keep the markdown human form
(`human-verification-form.md`) as the authoritative rating capture and use QC Studio purely
for visualization — the criterion labels match either way.

## Launch

```bash
# In a clone of qc-studio (https://github.com/nipoppy/qc-studio):
python ui/main.py \
  --dataset_dir   /path/to/nipoppy-dataset \
  --participant_list /path/to/qc_participants.tsv \
  --qc_pipeline   <name> \
  --qc_task       brain_extraction_qc \
  --qc_json       /path/to/nipoppy-dataset/qc-studio/<name>/qc.json \
  --output_dir    /path/to/qc-output \
  --session_list  ses-01
streamlit run ui/app.py
```

`--participant_list` is a TSV with a `participant_id` column (`sub-001`, `sub-002`, …).
