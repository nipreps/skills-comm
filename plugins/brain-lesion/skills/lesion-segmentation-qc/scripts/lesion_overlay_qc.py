#!/usr/bin/env python3
"""
Lesion QC overlay: 3-plane mosaic, slices chosen where the lesion actually is.

Sampling slices across the whole volume is how a small lesion passes review --
most panels show lesion-free brain and the eye reads the montage as clean. This
picks the slices carrying the most lesion in each plane instead, so every panel
is informative, and it draws both a translucent fill and a bright contour so
that both extent and boundary placement are visible at once.

Usage: lesion_overlay_qc.py <anat.nii.gz> <lesion.nii.gz> <out.png> [--slices 9]

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


def load_ras(p):
    img = nib.as_closest_canonical(nib.load(p))
    return np.asanyarray(img.dataobj, dtype=np.float32), np.asarray(img.header.get_zooms()[:3])


def clip(v, lo=1, hi=99):
    if not v.any():
        return v
    a, b = np.percentile(v[v > 0], [lo, hi])
    return np.clip((v - a) / (b - a + 1e-6), 0, 1)


def take(vol, axis, i):
    s = [slice(None)] * 3
    s[axis] = i
    return vol[tuple(s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("anat"); ap.add_argument("lesion"); ap.add_argument("out")
    ap.add_argument("--slices", type=int, default=9)
    args = ap.parse_args()

    anat, zooms = load_ras(args.anat)
    les, _ = load_ras(args.lesion)
    if anat.shape != les.shape:
        raise SystemExit(f"ERROR: anat {anat.shape} != lesion {les.shape}")

    m = (les > 0.5).astype(np.float32)
    vol = float(m.sum()) * float(np.prod(zooms)) / 1000.0
    if m.sum() == 0:
        raise SystemExit("ERROR: lesion mask is empty -- nothing to display")

    a = clip(anat)
    n = args.slices
    fig = plt.figure(figsize=(n * 1.6, 3 * 1.9))
    fig.patch.set_facecolor("black")
    gs = gridspec.GridSpec(3, n, figure=fig, hspace=0.04, wspace=0.04)

    for row, (axis, label) in enumerate([(2, "Axial"), (1, "Coronal"), (0, "Sagittal")]):
        # rank slices by how much lesion they carry, then show them in
        # anatomical order so the montage still reads as a sweep
        per = m.sum(axis=tuple(i for i in range(3) if i != axis))
        idx = np.sort(np.argsort(per)[::-1][:n])
        for col, i in enumerate(idx):
            ax = fig.add_subplot(gs[row, col])
            a_sl, m_sl = np.rot90(take(a, axis, int(i))), np.rot90(take(m, axis, int(i)))
            ax.imshow(a_sl, cmap="gray", interpolation="nearest")
            ax.imshow(np.ma.masked_where(m_sl == 0, m_sl), cmap="autumn",
                      vmin=0, vmax=1, alpha=0.45, interpolation="nearest")
            if m_sl.any():
                ax.contour(m_sl, levels=[0.5], colors=["#00ffff"], linewidths=0.6)
            ax.axis("off")
            ax.set_title(f"{int(i)}", color="white", fontsize=5, pad=1)
            if col == 0:
                ax.text(-0.08, 0.5, label, color="white", fontsize=8, rotation=90,
                        va="center", ha="center", transform=ax.transAxes)

    fig.suptitle(f"Lesion QC  |  {Path(args.lesion).name}  |  {vol:.2f} cm3  |  "
                 "slices with greatest lesion burden",
                 color="white", fontsize=9, y=0.99)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"ERROR: refusing to overwrite existing QC overlay: {output}")
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
    print(f"Lesion QC overlay saved: {output}  ({vol:.2f} cm3)")


if __name__ == "__main__":
    main()
