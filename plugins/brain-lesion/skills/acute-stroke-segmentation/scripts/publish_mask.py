#!/usr/bin/env python3
"""Validate and atomically publish an exact uint8 NIfTI mask."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

import nibabel as nib
import numpy as np
from scipy import ndimage


VOLUME_LIMITS_ML = {
    "brain": (900.0, 1900.0),
    "lesion": (0.5, 500.0),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--kind", required=True, choices=sorted(VOLUME_LIMITS_ML))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    candidate_img = nib.load(str(args.candidate))
    reference_img = nib.load(str(args.reference))
    data = np.asanyarray(candidate_img.dataobj)
    values = np.unique(data)
    failures: list[str] = []
    warnings: list[str] = []

    if candidate_img.shape != reference_img.shape or not np.array_equal(
        candidate_img.affine, reference_img.affine
    ):
        failures.append("reference_grid_exact")
    near_zero = np.isclose(data, 0.0, rtol=0.0, atol=1e-6)
    near_one = np.isclose(data, 1.0, rtol=0.0, atol=1e-6)
    binary_with_scaling_tolerance = bool(
        np.all(np.isfinite(data)) and np.all(near_zero | near_one)
    )
    if not binary_with_scaling_tolerance:
        failures.append("binary_exact_0_1")

    # Normalize only the known NIfTI integer-scaling artifact; this does not
    # accept probability maps or arbitrary thresholds.
    mask = near_one
    if not mask.any():
        failures.append("nonempty")

    # True voxel volume from the affine, matching resample_mask.py. get_zooms()
    # returns stored pixdim, which understates an oblique voxel's volume.
    voxel_volume_ml = abs(float(np.linalg.det(reference_img.affine[:3, :3]))) / 1000.0
    volume_ml = float(mask.sum() * voxel_volume_ml)
    low, high = VOLUME_LIMITS_ML[args.kind]
    if not (low <= volume_ml <= high):
        failures.append(f"volume_{low:g}_{high:g}_ml")

    structure = ndimage.generate_binary_structure(3, 1)
    _, component_count = ndimage.label(mask, structure=structure)
    if args.kind == "brain" and component_count != 1:
        failures.append("single_connected_component")

    filled = ndimage.binary_fill_holes(mask, structure=structure)
    internal_hole_voxels = int(np.count_nonzero(filled & ~mask))
    if internal_hole_voxels and args.kind == "brain":
        failures.append("no_internal_holes")
    elif internal_hole_voxels:
        warnings.append(f"internal_holes_present:{internal_hole_voxels}")

    if args.output.exists() and not args.replace:
        failures.append("output_exists")

    report = {
        "candidate": str(args.candidate),
        "reference": str(args.reference),
        "output": str(args.output),
        "kind": args.kind,
        "shape": list(candidate_img.shape),
        "values": [float(value) for value in values[:16]],
        "normalized_near_binary_scaling": bool(
            binary_with_scaling_tolerance and not set(values.tolist()) <= {0, 1}
        ),
        "component_count": int(component_count),
        "internal_hole_voxels": internal_hole_voxels,
        "volume_ml": round(volume_ml, 6),
        "plausible_volume_ml": [low, high],
        "warnings": warnings,
        "failures": failures,
    }
    if failures:
        print(json.dumps(report, indent=2))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    header = reference_img.header.copy()
    header.set_data_dtype(np.uint8)
    header["scl_slope"] = np.nan
    header["scl_inter"] = np.nan
    published = nib.Nifti1Image(mask.astype(np.uint8), reference_img.affine, header)
    published.header.set_data_dtype(np.uint8)
    published.header["scl_slope"] = np.nan
    published.header["scl_inter"] = np.nan

    handle = tempfile.NamedTemporaryFile(
        prefix=f".{args.output.name}.", suffix=".nii.gz", dir=args.output.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        nib.save(published, str(temporary))
        check = nib.load(str(temporary))
        check_data = np.asanyarray(check.dataobj)
        if check.get_data_dtype() != np.dtype(np.uint8):
            raise RuntimeError(f"published dtype is {check.get_data_dtype()}, expected uint8")
        if not set(np.unique(check_data).tolist()) <= {0, 1}:
            raise RuntimeError("published file is not exact {0,1}")
        if check.shape != reference_img.shape or not np.array_equal(
            check.affine, reference_img.affine
        ):
            raise RuntimeError("published file no longer matches the reference grid")
        if not np.isnan(check.header["scl_slope"]) or not np.isnan(check.header["scl_inter"]):
            raise RuntimeError("published NIfTI scaling fields were not cleared")
        os.replace(temporary, args.output)
    finally:
        if temporary.exists():
            temporary.unlink()

    report["published_dtype"] = "uint8"
    report["published_values"] = [0, 1] if (~mask).any() else [1]
    report["scl_slope_inter_cleared"] = True
    report["published"] = True
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
