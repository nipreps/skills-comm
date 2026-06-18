# QC PNG Generation Script

Write this script to `qc_brain_extraction.py` in the working directory, then
run it. It requires only `nibabel` and `matplotlib`, which are available in the
base Miniconda environment — no `module load` is needed.

## Script

```python
#!/usr/bin/env python3
"""
Brain extraction QC: generate a 3-plane mosaic with mask overlay, and write an
IQM sidecar TSV (brain volume, voxel count, coverage) for QC Studio's metrics panel.
Usage: python qc_brain_extraction.py <original.nii.gz> <mask.nii.gz> <output.png> [iqm.tsv]
If <iqm.tsv> is omitted it is derived from <output.png> (..._qc.png -> ..._iqm.tsv).
"""
import sys
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

def load_vol(path):
    img = nib.load(path)
    data = np.asanyarray(img.dataobj, dtype=np.float32)
    vox_dims = np.abs(np.diag(img.affine)[:3])
    return data, vox_dims

def percentile_clip(vol, lo=1, hi=99):
    lo_v, hi_v = np.percentile(vol[vol > 0], [lo, hi]) if vol.any() else (0, 1)
    return np.clip((vol - lo_v) / (hi_v - lo_v + 1e-6), 0, 1)

def sample_slices(vol, n=9, axis=2):
    shape = vol.shape[axis]
    indices = np.linspace(int(shape * 0.1), int(shape * 0.9), n, dtype=int)
    slices = []
    for i in indices:
        s = [slice(None)] * 3
        s[axis] = i
        slices.append(vol[tuple(s)])
    return slices

def overlay_mask(ax, anat_slice, mask_slice, cmap="gray", alpha=0.4):
    ax.imshow(np.rot90(anat_slice), cmap=cmap, interpolation="nearest")
    masked = np.ma.masked_where(mask_slice == 0, mask_slice)
    ax.imshow(np.rot90(masked), cmap="Reds", vmin=0, vmax=1,
              alpha=alpha, interpolation="nearest")
    ax.axis("off")

def derive_iqm_path(png_path):
    p = str(png_path)
    if p.endswith("_qc.png"):
        return p[:-len("_qc.png")] + "_iqm.tsv"
    if p.endswith(".png"):
        return p[:-len(".png")] + "_iqm.tsv"
    return p + "_iqm.tsv"

def write_iqm_tsv(path, n_voxels, vox_vol_mm3, brain_vol_cm3, coverage_pct, flag_vol):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ("metric", "value", "reference_range", "flag"),
        ("brain_volume_cm3", f"{brain_vol_cm3:.1f}", "900-1800", flag_vol),
        ("brain_voxels", str(n_voxels), "-", "-"),
        ("voxel_volume_mm3", f"{vox_vol_mm3:.4f}", "-", "-"),
        ("coverage_pct_fov", f"{coverage_pct:.2f}", "40-50 (typical)", "-"),
    ]
    with open(path, "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")

def main():
    if len(sys.argv) not in (4, 5):
        print("Usage: python qc_brain_extraction.py <original> <mask> <output.png> [iqm.tsv]")
        sys.exit(1)

    orig_path, mask_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    iqm_path = sys.argv[4] if len(sys.argv) == 5 else derive_iqm_path(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    orig, vox = load_vol(orig_path)
    mask, _   = load_vol(mask_path)

    mask_bin = (mask > 0.5).astype(np.float32)

    # Quantitative stats
    vox_vol_mm3   = float(np.prod(vox))
    n_voxels      = int(mask_bin.sum())
    brain_vol_cm3 = n_voxels * vox_vol_mm3 / 1000.0
    total_voxels  = orig.size
    coverage_pct  = 100.0 * n_voxels / total_voxels

    print(f"Brain voxels:    {n_voxels:,}")
    print(f"Brain volume:    {brain_vol_cm3:.1f} cm³")
    print(f"Coverage:        {coverage_pct:.2f}% of total FOV")
    flag_vol = "OK"
    if brain_vol_cm3 < 900 or brain_vol_cm3 > 1800:
        flag_vol = "OUT_OF_RANGE"
        print(f"WARNING: brain volume {brain_vol_cm3:.1f} cm³ is outside expected "
              f"adult T1w range (900–1800 cm³)")

    write_iqm_tsv(iqm_path, n_voxels, vox_vol_mm3, brain_vol_cm3, coverage_pct, flag_vol)
    print(f"IQM sidecar saved: {iqm_path}")

    orig_norm = percentile_clip(orig)

    n_slices = 9
    fig = plt.figure(figsize=(n_slices * 1.5, 3 * 1.8))
    fig.patch.set_facecolor("black")
    gs = gridspec.GridSpec(3, n_slices, figure=fig, hspace=0.04, wspace=0.04)

    planes = [
        (2, "Axial"),
        (1, "Coronal"),
        (0, "Sagittal"),
    ]

    for row, (axis, label) in enumerate(planes):
        anat_slices = sample_slices(orig_norm, n=n_slices, axis=axis)
        mask_slices = sample_slices(mask_bin,  n=n_slices, axis=axis)
        for col, (a_sl, m_sl) in enumerate(zip(anat_slices, mask_slices)):
            ax = fig.add_subplot(gs[row, col])
            overlay_mask(ax, a_sl, m_sl)
            if col == 0:
                ax.set_ylabel(label, color="white", fontsize=8)

    # Title with stats
    title = (f"Brain Extraction QC  |  "
             f"Volume: {brain_vol_cm3:.1f} cm³  |  "
             f"Coverage: {coverage_pct:.1f}%")
    fig.suptitle(title, color="white", fontsize=9, y=0.99)

    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="black", pad_inches=0.1)
    plt.close(fig)
    print(f"QC PNG saved: {out_path}")

if __name__ == "__main__":
    main()
```

## Running the Script

```bash
python qc_brain_extraction.py \
  "<original.nii.gz>" \
  "<mask.nii.gz>" \
  "qc/<subject>_<tool>_<timestamp>_qc.png" \
  ["<iqm.tsv>"]      # optional; derived from the PNG name if omitted
```

The optional 4th argument is the IQM sidecar path. For QC Studio integration, pass the
deterministic derivatives path so the metrics panel resolves (see
`qcstudio-integration.md`):
`derivatives/brainextraction/<version>/output/<sub>/<ses>/anat/<sub>_<ses>_desc-brain_iqm.tsv`

Expected stdout:
```
Brain voxels:    1,234,567
Brain volume:    1243.2 cm³
Coverage:        42.30% of total FOV
IQM sidecar saved: qc/sub-01_fsl-bet_20260611-143022_iqm.tsv
QC PNG saved: qc/sub-01_fsl-bet_20260611-143022_qc.png
```

### IQM sidecar (TSV)

A tab-separated file with one row per metric, consumed by QC Studio's metrics panel:

```
metric            value   reference_range   flag
brain_volume_cm3  1243.2  900-1800          OK
brain_voxels      1234567 -                 -
voxel_volume_mm3  1.0000  -                 -
coverage_pct_fov  42.30   40-50 (typical)   -
```

## Dependency Check

Before running, verify dependencies:
```bash
python -c "import nibabel, matplotlib; print('OK')"
```

If this fails:
```bash
pip install nibabel matplotlib
```

## What the PNG Shows

- **3 rows:** Axial (top), Coronal (middle), Sagittal (bottom)
- **9 columns per row:** evenly spaced slices spanning 10%–90% of the FOV
- **Red overlay:** brain mask (semi-transparent, alpha=0.4)
- **Title bar:** brain volume and coverage fraction

## Interpreting the Output

| Visual cue | Meaning |
|-----------|---------|
| Red extends past brain edge into scalp/skull | Under-stripping |
| Grey brain tissue visible outside red region | Over-stripping |
| Red mask with holes inside | Disconnected mask regions |
| Asymmetric red coverage L vs R | Possible lateralised failure |
| Red missing at superior or inferior slices | Pole clipping |
