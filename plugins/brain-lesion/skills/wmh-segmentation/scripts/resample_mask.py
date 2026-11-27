#!/usr/bin/env python3
"""Map a binary mask to a declared reference grid with nearest-neighbour sampling."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

import nibabel as nib
from nibabel.processing import resample_from_to
import numpy as np


def binary_data(img: nib.spatialimages.SpatialImage) -> np.ndarray:
    data = np.asarray(img.dataobj)
    if data.ndim != 3 or not np.isfinite(data).all():
        raise ValueError("candidate must be a finite 3D image")
    near_zero = np.isclose(data, 0.0, atol=1e-6)
    near_one = np.isclose(data, 1.0, atol=1e-6)
    if not np.all(near_zero | near_one):
        raise ValueError("candidate must contain only binary 0/1 values")
    return near_one.astype(np.uint8)


def volume_ml(mask: np.ndarray, affine: np.ndarray) -> float:
    voxel_ml = abs(float(np.linalg.det(affine[:3, :3]))) / 1000.0
    return float(mask.sum()) * voxel_ml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-volume-change-pct", type=float, default=5.0)
    args = parser.parse_args()

    candidate_img = nib.load(args.candidate)
    reference_img = nib.load(args.reference)
    if len(reference_img.shape) != 3:
        raise ValueError("reference must be 3D")

    source_mask = binary_data(candidate_img)
    if not source_mask.any():
        raise ValueError("candidate mask is empty")
    source_binary = nib.Nifti1Image(source_mask, candidate_img.affine)
    mapped_img = resample_from_to(
        source_binary,
        (reference_img.shape, reference_img.affine),
        order=0,
        mode="constant",
        cval=0,
    )
    mapped_mask = (np.asarray(mapped_img.dataobj) > 0.5).astype(np.uint8)
    if not mapped_mask.any():
        raise ValueError("mapped mask is empty; grids may not share physical space")

    before_ml = volume_ml(source_mask, candidate_img.affine)
    after_ml = volume_ml(mapped_mask, reference_img.affine)
    change_pct = abs(after_ml - before_ml) / before_ml * 100.0
    if change_pct > args.max_volume_change_pct:
        raise ValueError(
            f"mask volume changed by {change_pct:.3f}% "
            f"(limit {args.max_volume_change_pct:.3f}%); verify spatial relationship"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    header = reference_img.header.copy()
    header.set_data_dtype(np.uint8)
    header.set_slope_inter(None, None)
    output_img = nib.Nifti1Image(mapped_mask, reference_img.affine, header)
    with tempfile.NamedTemporaryFile(
        prefix=f".{args.output.name}.", suffix=".nii.gz",
        dir=args.output.parent, delete=False,
    ) as handle:
        temporary = Path(handle.name)
    try:
        nib.save(output_img, temporary)
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)

    stored = nib.load(args.output)
    if stored.shape != reference_img.shape or not np.array_equal(
        stored.affine, reference_img.affine
    ):
        raise RuntimeError("stored output does not exactly match reference grid")
    print(json.dumps({
        "candidate": str(args.candidate),
        "reference": str(args.reference),
        "output": str(args.output),
        "source_orientation": nib.aff2axcodes(candidate_img.affine),
        "reference_orientation": nib.aff2axcodes(reference_img.affine),
        "volume_before_ml": round(before_ml, 6),
        "volume_after_ml": round(after_ml, 6),
        "volume_change_pct": round(change_pct, 6),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
