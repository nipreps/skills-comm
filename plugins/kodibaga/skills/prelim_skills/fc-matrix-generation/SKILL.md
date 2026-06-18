---
name: fc-matrix-generation
description: >
  Find resting-state fMRI data in a directory, extract ROI time series using a
  brain atlas/parcellation, compute functional connectivity matrices (Pearson
  or partial correlation), and save them as ready-to-harmonize feature matrices.
  Invoke when the user asks for "functional connectivity", "FC matrices",
  "connectome generation", "resting state correlation", "parcellate fMRI",
  "extract time series", "atlas-based connectivity", or "generate connectomes".
  Also invoke when the user mentions rs-fMRI combined with any atlas name
  (Schaefer, Harvard-Oxford, AAL, DiFuMo, etc.) or when they need to
  preprocess raw BOLD for connectivity analysis without a full pipeline.
---

# FC Matrix Generation

Generate functional connectivity matrices from resting-state fMRI data using
nilearn. Detect raw vs. preprocessed data, apply appropriate denoising, extract
atlas-based time series, compute correlation matrices, and save in a format
ready for harmonization.

## Workflow

### 1. Discover the data

**Scope constraint:** Only search within the directories explicitly provided by
the user (e.g., the user's working directory or named BIDS folders). Do not
traverse outside those roots. Report the exact paths being searched and the
count of files found per directory.

Search for resting-state fMRI files. Use a single glob pattern to avoid
duplicate matches:

```
sub-*/func/*task-rest*_bold.nii.gz
```

If this pattern is too restrictive and misses data, fall back to:
```
sub-*/func/*_bold.nii.gz
```

**Deduplicate by absolute path** — two different glob patterns can match the
same file on disk. Track resolved paths in a set and skip duplicates.

**Report what was found by dataset immediately**, showing counts and which files
have JSON sidecars vs which don't.

For each file found, extract NIfTI dimensions directly and parse BIDS JSON
for site metadata. **Never skip a file just because its JSON sidecar is
missing** — use sensible defaults (TR=2.0, site='unknown') and flag it in the
catalog instead.

### 2. Assess preprocessing state

Check whether the data is raw or preprocessed:

- **Raw data**: no `_desc-` entities in filename, no derivatives/ directory, may have varying voxel sizes across subjects, no brain mask in same directory
- **Preprocessed**: filenames contain `_desc-preproc_`, `_space-`, etc., or found under `derivatives/`

If raw: nilearn will apply Signal.clean() with:
- High-pass filter (0.01 Hz)
- Low-pass filter (0.10 Hz unless user specifies otherwise)
- Detrending
- Standardization (z-score)

Also extract confounds from the CompCor method or basic motion parameters.

### 3. Select atlas

Present the user with available atlases and their trade-offs. Available via nilearn:

| Atlas | N ROIs | Coverage | Best for |
|-------|--------|----------|----------|
| Schaefer 2018 (100/200/400/600/1000 parcels) | configurable | Cortex only, 7 or 17 networks | RSFC, network science |
| Harvard-Oxford (cortical + subcortical) | ~110 | Cortical + subcortical | Whole-brain FC |
| AAL / AAL3 | 116-170 | Whole brain | Clinical/legacy studies |
| DiFuMo (64/128/256/512/1024) | configurable | Whole brain, data-driven | High-dim FC, fine parcellation |
| MSDL (probabilistic) | 39 | Whole brain | Sparse/ICA-based FC |
| BASC (multiscale) | 64/122/197 | Whole brain | Multi-resolution |

**Default recommendation**: Schaefer 2018 with 400 parcels + subcortical from Harvard-Oxford, unless the user has a specific preference. Schaefer is the most commonly used in modern resting-state FC literature.

### 4. Write the extraction script

Write `analysis_<N>_fc_extraction.py` containing:

```python
#!/usr/bin/env python3
"""Extract FC matrices from resting-state fMRI using nilearn."""

import json, argparse, sys
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
from nilearn.datasets import fetch_atlas_*
from nilearn.image import clean_img, load_img
from nilearn.connectome import ConnectivityMeasure
from nilearn.signal import clean

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bids-root', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--atlas', default=<user choice>)
    parser.add_argument('--n-rois', type=int, default=<user choice>)
    parser.add_argument('--tr', type=float, help='TR in seconds')
    args = parser.parse_args()
    
    # ... implementation in reference file
```

## Output structure

Organize outputs per dataset so failures in one dataset never block another:

```
output_dir/
  <dataset_name>/
    fc_mats/           - {subject}_fc.npy  (N_rois x N_rois full matrices)
    fc_edges/          - {subject}_edges.npy (1D upper triangle vector)
    success.csv        - subjects that completed
    failures.csv       - subjects that failed + error messages
    failure_details.txt - full tracebacks for debugging
    summary.csv        - all subjects with status column
```

Write each subject's files immediately after extraction — do not batch at the
end. That way partial runs are salvageable.

For each subject, record in the summary:
- `status`: `success` or `failure`
- `error`: the exception message if failed (usable by the Next step)
- `n_rois`, `n_edges`, `edge_mean`, `edge_std` if succeeded

### 5. Run or submit

If a scheduler is available (SLURM, PBS, etc.), write a companion `.sh` wrapper with appropriate resource requests. Otherwise run the Python script directly.

See `references/nilearn-extraction.md` for detailed implementation patterns.

## Constraints

- Never assume a specific runtime — detect what's available
- Always save both full matrices and edge vectors (for ComBat)
- Always include site/scanner metadata in the output catalog
- Set random seeds for reproducibility
- **Save per-subject immediately** — do not batch writes at the end; a crash on
  subject N must not lose subjects 1..N-1
- **Record all failures** with full error messages in `failures.csv` and
  `failure_details.txt` so the user knows exactly what went wrong
- **Organize output per dataset** — each dataset gets its own subdirectory so
  FC matrices from one aren't mixed with another
- **Use `resampling_target='labels'`** in NiftiLabelsMasker. This resamples the
  BOLD data to the atlas space, guaranteeing every subject gets exactly the
  same number of ROIs. Default behavior (`resampling_target='data'`) resamples
  the atlas to native BOLD space, which drops ROIs outside the FOV differently
  for each subject — making harmonization impossible.
- **Validate ROI consistency**: After extraction, check that all successful
  subjects have identical ROI counts. Warn loudly if they don't.
