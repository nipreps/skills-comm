# QC PNG Generation Script

Write this script to `qc_brain_extraction.py` in the working directory, then
run it. It requires `nibabel` and `matplotlib`; verify they are available in
the active Python environment before running.

## Script

```python
#!/usr/bin/env python3
"""
Brain extraction QC: generate a 3-plane mosaic with mask overlay.
Usage: python qc_brain_extraction.py <original.nii.gz> <mask.nii.gz> <output.png>
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
    axis_codes = nib.aff2axcodes(img.affine)
    return data, vox_dims, axis_codes

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

def half_mask_imbalance(mask_bin, axis):
    """Return percent imbalance between low/high halves along one voxel axis."""
    size = mask_bin.shape[axis]
    mid = size // 2
    low_sel = [slice(None)] * 3
    high_sel = [slice(None)] * 3
    low_sel[axis] = slice(0, mid)
    high_sel[axis] = slice(mid + (size % 2), size)
    low = float(mask_bin[tuple(low_sel)].sum())
    high = float(mask_bin[tuple(high_sel)].sum())
    total = low + high
    if total == 0:
        return 0.0, low, high
    return 100.0 * abs(high - low) / total, low, high

def centroid_offsets(mask_bin):
    """Return centroid offset from FOV centre as percent of axis size."""
    coords = np.argwhere(mask_bin > 0)
    if coords.size == 0:
        return [0.0, 0.0, 0.0]
    centroid = coords.mean(axis=0)
    centre = (np.array(mask_bin.shape, dtype=np.float32) - 1.0) / 2.0
    return (100.0 * np.abs(centroid - centre) / np.array(mask_bin.shape)).tolist()

def bbox_margin_imbalance(mask_bin, axis):
    """Return percent FOV difference between low/high margins of mask bbox."""
    coords = np.argwhere(mask_bin > 0)
    if coords.size == 0:
        return 0.0, 0, 0
    lo = int(coords[:, axis].min())
    hi = int(coords[:, axis].max())
    low_margin = lo
    high_margin = mask_bin.shape[axis] - 1 - hi
    return 100.0 * abs(high_margin - low_margin) / mask_bin.shape[axis], low_margin, high_margin

def overlay_mask(ax, anat_slice, mask_slice, cmap="gray", alpha=0.4):
    ax.imshow(np.rot90(anat_slice), cmap=cmap, interpolation="nearest")
    masked = np.ma.masked_where(mask_slice == 0, mask_slice)
    ax.imshow(np.rot90(masked), cmap="Reds", vmin=0, vmax=1,
              alpha=alpha, interpolation="nearest")
    ax.axis("off")

def main():
    if len(sys.argv) != 4:
        print("Usage: python qc_brain_extraction.py <original> <mask> <output.png>")
        sys.exit(1)

    orig_path, mask_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    orig, vox, axis_codes = load_vol(orig_path)
    mask, _, mask_axis_codes = load_vol(mask_path)

    if orig.shape != mask.shape:
        print(f"ERROR: original shape {orig.shape} differs from mask shape {mask.shape}")
        sys.exit(2)
    if axis_codes != mask_axis_codes:
        print(f"WARNING: original orientation {axis_codes} differs from mask orientation {mask_axis_codes}")

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
    if brain_vol_cm3 < 900 or brain_vol_cm3 > 1800:
        print(f"WARNING: brain volume {brain_vol_cm3:.1f} cm³ is outside expected "
              f"adult T1w range (900–1800 cm³)")

    print("Symmetry diagnostics:")
    max_half = (0.0, "axis-0")
    max_centroid = (0.0, "axis-0")
    max_margin = (0.0, "axis-0")
    offsets = centroid_offsets(mask_bin)
    for axis in range(3):
        axis_name = f"axis-{axis} ({axis_codes[axis]})"
        half_pct, low, high = half_mask_imbalance(mask_bin, axis)
        margin_pct, low_margin, high_margin = bbox_margin_imbalance(mask_bin, axis)
        centroid_pct = offsets[axis]
        max_half = max(max_half, (half_pct, axis_name), key=lambda x: x[0])
        max_centroid = max(max_centroid, (centroid_pct, axis_name), key=lambda x: x[0])
        max_margin = max(max_margin, (margin_pct, axis_name), key=lambda x: x[0])
        print(f"  {axis_name}: half imbalance {half_pct:.1f}% "
              f"(low={low:.0f}, high={high:.0f}); "
              f"centroid offset {centroid_pct:.1f}% FOV; "
              f"bbox margin imbalance {margin_pct:.1f}% "
              f"(low margin={low_margin}, high margin={high_margin})")
    print(f"Max half-mask imbalance: {max_half[0]:.1f}% on {max_half[1]}")
    print(f"Max centroid offset:     {max_centroid[0]:.1f}% of FOV on {max_centroid[1]}")
    print(f"Max bbox margin imbalance: {max_margin[0]:.1f}% on {max_margin[1]}")
    if max_half[0] > 15.0 or max_centroid[0] > 8.0 or max_margin[0] > 12.0:
        print("WARNING: symmetry diagnostics exceed conservative thresholds; "
              "visually inspect for L/R or A/P mask failure")

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
             f"Coverage: {coverage_pct:.1f}%  |  "
             f"Max asym: {max_half[0]:.1f}%")
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
  "qc/<subject>_<tool>_<timestamp>_qc.png"
```

Expected stdout:
```
Brain voxels:    1,234,567
Brain volume:    1243.2 cm³
Coverage:        42.30% of total FOV
Symmetry diagnostics:
  axis-0 (R): half imbalance 4.8% (low=587321, high=647246); centroid offset 2.1% FOV; bbox margin imbalance 3.5% (low margin=18, high margin=25)
  axis-1 (A): half imbalance 6.2% (low=579004, high=655563); centroid offset 2.8% FOV; bbox margin imbalance 4.0% (low margin=20, high margin=28)
  axis-2 (S): half imbalance 9.5% (low=558712, high=675855); centroid offset 4.4% FOV; bbox margin imbalance 6.1% (low margin=12, high margin=24)
Max half-mask imbalance: 9.5% on axis-2 (S)
Max centroid offset:     4.4% of FOV on axis-2 (S)
Max bbox margin imbalance: 6.1% on axis-2 (S)
QC PNG saved: qc/sub-01_fsl-bet_20260611-143022_qc.png
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
- **Title bar:** brain volume, coverage fraction, and maximum half-mask asymmetry

## Interpreting the Output

| Visual cue | Meaning |
|-----------|---------|
| Red extends past brain edge into scalp/skull | Under-stripping |
| Grey brain tissue visible outside red region | Over-stripping |
| Red mask with holes inside | Disconnected mask regions |
| Asymmetric red coverage L vs R | Possible lateralised failure |
| Red missing at superior or inferior slices | Pole clipping |

## Symmetry Diagnostics

The script prints three mask-balance checks for each voxel axis:

| Metric | Meaning | Concerning value |
|--------|---------|------------------|
| Half imbalance | Difference in mask voxel count between low/high halves of the field of view | >15% |
| Centroid offset | Distance between the mask centroid and field-of-view centre | >8% of FOV |
| Bbox margin imbalance | Difference between low/high margins around the mask bounding box | >12% |

These numbers are not a substitute for visual QC. They are intended to prevent
obvious asymmetric masks from being marked as good. If any symmetry warning is
printed, inspect axial and coronal rows carefully and downgrade the symmetry
criterion unless the asymmetry is explained by anatomy, pathology, or an
intentionally asymmetric acquisition field of view.
