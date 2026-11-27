#!/usr/bin/env python3
"""
Brain extraction QC mosaic: 3 planes x N slices, mask filled plus edge contour.

This is the human-facing companion to qc_metrics.py. It answers "show me" where
the metrics answer "how much". Slices are sampled across the mask bounding box
rather than the whole field of view, so panels are not wasted on empty air.

Usage:
    python qc_mosaic.py <anat.nii.gz> <mask.nii.gz> <out.png> [--slices 13]

Requires: numpy, nibabel, matplotlib.
"""
import argparse
import os
from pathlib import Path
import tempfile

import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def load_ras(path):
    img = nib.as_closest_canonical(nib.load(path))
    return np.asanyarray(img.dataobj, dtype=np.float32), np.asarray(img.header.get_zooms()[:3])


def percentile_clip(vol, lo=1, hi=99):
    if not vol.any():
        return vol
    lo_v, hi_v = np.percentile(vol[vol > 0], [lo, hi])
    return np.clip((vol - lo_v) / (hi_v - lo_v + 1e-6), 0, 1)


def slice_indices(mask_bin, axis, n):
    """Sample n slices spanning the mask extent along `axis`, plus a margin."""
    shape = mask_bin.shape[axis]
    if np.any(mask_bin):
        coords = np.argwhere(mask_bin)
        lo, hi = int(coords[:, axis].min()), int(coords[:, axis].max())
        pad = max(2, int(round((hi - lo + 1) * 0.08)))
        start, stop = max(0, lo - pad), min(shape - 1, hi + pad)
    else:
        start, stop = int(shape * 0.05), int(shape * 0.95)
    return np.unique(np.linspace(start, stop, n, dtype=int))


def take(vol, axis, i):
    sl = [slice(None)] * 3
    sl[axis] = i
    return vol[tuple(sl)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("anat"); ap.add_argument("mask"); ap.add_argument("out")
    ap.add_argument("--slices", type=int, default=13)
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    anat, zooms = load_ras(args.anat)
    mask, _ = load_ras(args.mask)
    if anat.shape != mask.shape:
        raise SystemExit(f"ERROR: anat shape {anat.shape} != mask shape {mask.shape}")

    mask_bin = (mask > 0.5).astype(np.float32)
    anat_n = percentile_clip(anat)
    n = args.slices
    vol_cm3 = float(mask_bin.sum()) * float(np.prod(zooms)) / 1000.0

    fig = plt.figure(figsize=(n * 1.5, 3 * 1.8))
    fig.patch.set_facecolor("black")
    gs = gridspec.GridSpec(3, n, figure=fig, hspace=0.04, wspace=0.04)

    # RAS axes: 0 = L->R (sagittal), 1 = P->A (coronal), 2 = I->S (axial)
    for row, (axis, label) in enumerate([(2, "Axial"), (1, "Coronal"), (0, "Sagittal")]):
        idx = slice_indices(mask_bin, axis, n)
        for col, i in enumerate(idx):
            ax = fig.add_subplot(gs[row, col])
            a_sl, m_sl = np.rot90(take(anat_n, axis, i)), np.rot90(take(mask_bin, axis, i))
            ax.imshow(a_sl, cmap="gray", interpolation="nearest")
            ax.imshow(np.ma.masked_where(m_sl == 0, m_sl), cmap="Reds",
                      vmin=0, vmax=1, alpha=0.30, interpolation="nearest")
            if m_sl.any():
                ax.contour(m_sl, levels=[0.5], colors=["#00ffff"], linewidths=0.45)
            ax.axis("off")
            ax.set_title(str(int(i)), color="white", fontsize=5, pad=1)
            if col == 0:
                ax.text(-0.08, 0.5, label, color="white", fontsize=8, rotation=90,
                        va="center", ha="center", transform=ax.transAxes)

    fig.suptitle(f"Brain Extraction QC  |  {Path(args.mask).name}  |  "
                 f"Volume: {vol_cm3:.1f} cm3", color="white", fontsize=9, y=0.99)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"ERROR: refusing to overwrite existing QC mosaic: {output}")
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{output.stem}.", suffix=".png", dir=output.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        plt.savefig(temporary, dpi=150, bbox_inches="tight", facecolor="black", pad_inches=0.1)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    plt.close(fig)
    print(f"QC mosaic saved: {output}  (mask volume {vol_cm3:.1f} cm3)")


if __name__ == "__main__":
    main()
