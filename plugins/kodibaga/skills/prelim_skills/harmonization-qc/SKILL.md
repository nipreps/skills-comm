---
name: harmonization-qc
description: >
  Visual quality control for ComBat-family harmonization results. Generate
  PCA/UMAP plots colored by site before and after harmonization, heatmap
  comparisons, variance explained by site, and a summary report. Invoke when
  the user asks for "harmonization QC", "check harmonization", "visualize
  ComBat results", "PCA before after harmonization", "evaluate site correction",
  "does harmonization work", or "validate batch correction". Also invoke
  after any harmonization completes to verify the results are meaningful.
---

# Harmonization Quality Control

Generate visual and quantitative assessments of how well harmonization
removed site effects while preserving biological signal.

## Workflow

### 1. Load data

Read the pre- and post-harmonization feature matrices and metadata:

```python
import numpy as np
import pandas as pd

orig = np.load('harmonization/input_edges.npy')
harm = np.load('harmonization/harmonized_edges.npy')
meta = pd.read_csv('harmonization/subject_metadata.csv')
sites = meta['site'].values
```

### 2. Quantitative metrics

Compute these metrics for both pre- and post-harmonization:

**Site variance explained** (lower = better):
```python
from sklearn.decomposition import PCA
from scipy.stats import f_oneway

# For each PC, compute variance explained by site
pca = PCA(n_components=min(10, n_subjects-1))
pca.fit(features)
for i in range(pca.n_components_):
    f_stat, p_val = f_oneway(*[pca.transform(features)[sites==s, i] for s in np.unique(sites)])
    print(f"PC{i+1}: F={f_stat:.2f}, p={p_val:.4f}")
```

**Silhouette score by site** (lower = better, sites should intermingle):
```python
from sklearn.metrics import silhouette_score
score = silhouette_score(features, sites)
```

**Correlation of site with each edge** (count edges with |r| > 0.3 as "site-biased"):
```python
site_encoded = pd.get_dummies(sites)
site_corrs = np.array([np.abs(np.corrcoef(site_encoded[s], features[:, i])[0,1]) 
                        for i in range(features.shape[1])])
n_biased = np.sum(site_corrs > 0.3)
```

### 3. Generate figures

Create a multi-panel QC figure (`harmonization_qc.png`):

**Panel 1: PCA scatter (top row)**
- Left: Pre-harmonization PC1 vs PC2, colored by site
- Right: Post-harmonization PC1 vs PC2, colored by site
- Sites should visually intermingle after harmonization

**Panel 2: UMAP embedding (optional, middle row)**
- Same layout as PCA but using UMAP for nonlinear structure

**Panel 3: Edge-wise variance comparison (bottom left)**
- Scatter plot: pre-harmonization SD per edge vs post-harmonization SD per edge
- Diagonal line for reference
- Points below the line = variance reduced

**Panel 4: Bar chart of site variance explained by PC (bottom right)**
- Grouped bars: pre vs post for top 5 PCs
- Y-axis: proportion of variance explained by site (from ANOVA F)

### 4. Generate report

Produce a text summary:

```
QC Report: ComBat Harmonization
================================
Method: ComBat-GAM
Date: YYYY-MM-DD
N subjects: XX
N sites: XX
N features: XX

Site variance explained:
  Before: PC1=F=XX.X (p<.001), PC2=F=XX.X (p<.001)
  After:  PC1=F=X.X (p>.05), PC2=F=X.X (p>.05)

Site-biased edges:
  Before: XX edges (XX%)
  After:  XX edges (XX%)

Silhouette by site:
  Before: X.XXX
  After:  X.XXX (lower is better)

Assessment: PASS/FLAG
```

### 5. Writing the QC script

Write `analysis_<N>_harmonization_qc.py` with:
- All imports (numpy, pandas, matplotlib, sklearn, scipy)
- Figure generation (mpl.figure with subplots)
- Text report output to stdout and to `harmonization_qc_report.txt`
- Save figure to `harmonization_qc.png` at 300 DPI

### 6. Assessment criteria

**PASS** (harmonization likely succeeded):
- PCA site separation visibly reduced
- Silhouette score decreased
- Site-biased edge count decreased
- No NaN/Inf values in harmonized data

**FLAG** (needs investigation):
- PCA shows new/unexpected clusters after harmonization
- Many edges show increased variance
- Site-biased edges increased
- NaN values present

## Constraints

- Always use both quantitative and visual assessment
- Never pass/fail based on visualization alone — compute metrics
- If UMAP is not installed (`pip install umap-learn`), skip that panel rather than failing
- Set matplotlib style for publication-quality figures
