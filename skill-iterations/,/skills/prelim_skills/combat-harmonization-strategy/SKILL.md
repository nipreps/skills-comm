---
name: combat-harmonization-strategy
description: >
  Analyze multi-site neuroimaging feature data and recommend the optimal
  ComBat-family harmonization method. Covers standard ComBat, ComBat-GAM,
  ComBat-Harmonize (longitudinal), CovBat, and RELIEF. Invoke when the user
  asks about "harmonizing features", "site correction", "batch effect removal",
  "ComBat", "harmonization method", "scanner effect", "multi-site harmonization",
  or "which harmonization to use". Also invoke when the user has a feature
  matrix (edges, thickness, volumes, connectivity) from multiple sites and
  needs to decide how to harmonize.
---

# ComBat-Family Harmonization Strategy

Analyze the dataset characteristics and recommend which ComBat-family method
to use, then produce a Python or R script implementing that method.

## The ComBat Family

| Method | Key Feature | When to Use | Input Requirements |
|--------|------------|-------------|-------------------|
| **Standard ComBat** | Linear batch correction with EB priors | Most cases, especially when biological covariates are linear. Fortin/Johnson papers. | Feature matrix (subjects × features), batch labels, optional linear covariates |
| **ComBat-GAM** | ComBat with Generalized Additive Models | When biological covariates may have nonlinear relationships with features (e.g., age effects on FC). Horien et al. 2021. | Same as standard + smooth_terms specification |
| **Longitudinal ComBat** | Handles repeated measures / within-subject designs | Each subject has multiple scans across time or conditions | Feature matrix, batch labels, subject IDs for repeated measures |
| **CovBat** | Removes site effects in mean AND covariance | When you suspect site affects not just the mean but also the covariance structure between features (common in FC edge data). Chen et al. 2022. | Standard inputs + PCA on residuals |
| **RELIEF** | Harmonization focused on reliability | When you have test-retest data and care about reliability of features | Feature matrix, batch labels, subject IDs for pairs |

### Decision Tree

Ask the user (or inspect the data) for these characteristics:

1. **Do subjects have repeated measures (same subject scanned multiple times)?**
   - Yes → Longitudinal ComBat (neuroHarmonize with subject IDs)
   - No → Continue

2. **Do you have biological covariates (age, sex, group) that must be preserved?**
   - Yes → Include them as `covars`
   - No → Harmonize with batch only

3. **Are any covariate effects potentially nonlinear?**
   - Yes (e.g., age has U-shaped or nonlinear relationship with connectivity) → ComBat-GAM
   - No → Standard ComBat

4. **Are you harmonizing functional connectivity edges specifically?**
   - FC edges are known to have site effects in the covariance structure → **CovBat** is recommended. Site differences often manifest in the pattern of correlations (not just means), so CovBat adjusts mean + covariance.
   - If CovBat is not available/too slow, fall back to ComBat-GAM

5. **Do you have more sites than subjects per site?**
   - If some sites have n < 10, standard ComBat without EB may be safer (parametric=False)

### Default recommendation for FC edge harmonization

For harmonizing resting-state functional connectivity across 2+ sites:
- **Primary**: CovBat (accounts for covariance structure changes, most appropriate for edge/connectivity features)
- **Fallback**: ComBat-GAM (if CovBat unavailable or too computationally heavy)
- **Minimal**: Standard ComBat (if neither available, still provides meaningful correction)

## Implementation Options

Once a method is selected, implement it. Check what tools are available:

### Option A: Python (neuroHarmonize)
```bash
pip install neuroharmonize  # wraps neuroCombat + GAM + longitudinal
```
- Standard ComBat: `harmonizationLearn(data, covars, eb=True)`
- ComBat-GAM: `harmonizationLearn(data, covars, smooth_terms=['age'])`
- Longitudinal: `harmonizationLearn(data, covars)`

### Option B: Python (neuroCombat directly)
```bash
pip install neurocombat
```
- `neuroCombat(dat, covars, batch_col, categorical_cols, continuous_cols, eb=True, parametric=True)`
- No GAM support, no longitudinal support

### Option C: Python (pyCombat)
```bash
pip install pycombat
```
- Minimal, scikit-learn-style API: `Combat().fit_transform(Y, b, X)`
- Use for quick/test implementations

### Option D: R (sva package)
```r
install.packages("sva")
library(sva)
combat(dat, batch, mod, ...)
```
- The original reference implementation
- No GAM support (needs separate mgcv code)
- Use if Python tools unavailable

### Option E: R with CovBat
```r
# CovBat R package from GitHub
remotes::install_github("andy1764/CovBat_Harmonization/R")
```

**Always prefer the Python implementations first** since they work in the same environment as the preprocessing scripts and don't require separate R/Julia runtimes. Fall back to R only if no Python implementation exists for the chosen method.

## Output

The skill produces a Python script (`analysis_<N>_combat_harmonize.py`) that:
1. Loads the feature matrix (edges) and site metadata
2. Implements the selected ComBat method
3. Saves harmonized features: `{output_dir}/harmonized_edges.npy`
4. Saves the original edges for comparison: `{output_dir}/input_edges.csv`
5. Saves site metadata with harmonized flag

## Constraints

- Always check what's installed before assuming availability
- If the preferred method isn't available, suggest the next-best fallback
- Always save both input and output for QC comparison
- Explain to the user WHY the recommended method fits their data
