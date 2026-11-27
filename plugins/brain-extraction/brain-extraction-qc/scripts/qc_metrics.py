#!/usr/bin/env python3
"""
Numeric brain-extraction QC.

Computes a battery of quantitative metrics that stand in for visual inspection,
so that a model without image-viewing capability can still assess a brain mask
on evidence rather than on filenames or vibes.

Why this exists: a filled-overlay PNG only helps if something can see it. Almost
everything a human looks for in a skull-strip QC image -- is the mask centred,
does it cover both hemispheres evenly, does it swallow scalp, does it cut off
the temporal poles, is it full of holes, is it bloated into CSF -- has a
well-defined numeric signature. This script measures those signatures directly.

The one thing it genuinely cannot do is detect dura and superior sagittal sinus
inclusion. Dura is a thin structure whose T1 intensity overlaps cortex, sitting
exactly where a correct boundary also sits, so no threshold separates them
reliably. That criterion is reported as UNVERIFIED rather than guessed at.

Usage:
    python qc_metrics.py <anat.nii.gz> <mask.nii.gz> [--json out.json]
                         [--vol-range 900 1900] [--label NAME]

Exit codes:
    0  metrics computed (regardless of pass/fail verdict)
    2  input error (missing file, shape mismatch, empty mask)

Requires: numpy, nibabel, scipy.
"""

import argparse
import json
import sys

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi

# ---------------------------------------------------------------------------
# Rating thresholds.
#
# These are deliberately in one place so they can be retuned against a local
# cohort. The defaults were separated empirically on 1mm adult T1w data using a
# known-good mask plus synthetic corruptions (shift, erosion, dilation,
# hemisphere deletion, punched holes). Values between the pass and fail cut are
# rated BORDERLINE.
#
# Direction: "hi_bad" means larger values are worse; "lo_bad" means smaller
# values are worse.
# ---------------------------------------------------------------------------
THRESHOLDS = {
    # C1 residual skull / scalp. brain_to_head_ratio is split into two one-sided
    # views of the same number: too high means the mask has swallowed non-brain,
    # too low means it has eaten into the brain. Keeping them separate lets each
    # criterion cite the direction that actually concerns it.
    "shallow_mask_frac_pct":      dict(pass_=2.0,  fail=8.0,  dir="hi_bad"),
    "bright_rim_frac_pct":        dict(pass_=0.10, fail=0.30, dir="hi_bad"),
    "brain_to_head_ratio_high":   dict(pass_=0.62, fail=0.72, dir="hi_bad"),
    # C2 tissue loss
    "brain_to_head_ratio_low":    dict(pass_=0.44, fail=0.35, dir="lo_bad"),
    "rim_brightness_high":        dict(pass_=0.42, fail=0.55, dir="hi_bad"),
    # C3 symmetry. Mirror Dice is the workhorse: it is the only one of the three
    # that is insensitive to which direction a mask was displaced.
    "lr_mirror_dice":             dict(pass_=0.95, fail=0.90, dir="lo_bad"),
    "lr_volume_asym_pct":         dict(pass_=12.0, fail=25.0, dir="hi_bad"),
    "centroid_offset_lr_mm":      dict(pass_=6.0,  fail=12.0, dir="hi_bad"),
    # C4 topology
    "extra_component_cm3":        dict(pass_=0.5,  fail=3.0,  dir="hi_bad"),
    "hole_volume_cm3":            dict(pass_=0.5,  fail=3.0,  dir="hi_bad"),
    # C5 boundary tightness. Two-sided: a mask bloated into CSF swallows dark
    # voxels, while a mask eroded into white matter has an unusually bright rim.
    "dark_voxel_frac_pct":        dict(lo=2.0, hi=12.0, lo_fail=0.5, hi_fail=20.0,
                                       dir="band"),
    "rim_darkness_low":           dict(pass_=0.18, fail=0.12, dir="lo_bad"),
}

RANK = {"PASS": 0, "BORDERLINE": 1, "FAIL": 2, "UNVERIFIED": 0}


def rate(name, value):
    """Rate one metric against its threshold. Returns PASS/BORDERLINE/FAIL."""
    t = THRESHOLDS[name]
    if value is None or not np.isfinite(value):
        return "UNVERIFIED"
    if t["dir"] == "hi_bad":
        if value <= t["pass_"]:
            return "PASS"
        return "FAIL" if value >= t["fail"] else "BORDERLINE"
    if t["dir"] == "lo_bad":
        if value >= t["pass_"]:
            return "PASS"
        return "FAIL" if value <= t["fail"] else "BORDERLINE"
    # band: healthy inside [lo, hi], failing outside [lo_fail, hi_fail]
    if t["lo"] <= value <= t["hi"]:
        return "PASS"
    if value <= t["lo_fail"] or value >= t["hi_fail"]:
        return "FAIL"
    return "BORDERLINE"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def otsu_threshold(vals, nbins=256):
    """Otsu's threshold from a 1-D sample. Avoids a scikit-image dependency."""
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0.0
    hist, edges = np.histogram(vals, bins=nbins)
    centers = 0.5 * (edges[:-1] + edges[1:])
    w = hist.astype(np.float64)
    total = w.sum()
    if total == 0:
        return float(centers[0])
    omega = np.cumsum(w) / total
    mu = np.cumsum(w * centers) / total
    mu_t = mu[-1]
    denom = omega * (1.0 - omega)
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma_b = (mu_t * omega - mu) ** 2 / denom
    if not np.any(np.isfinite(sigma_b)):
        return float(centers[0])
    return float(centers[int(np.nanargmax(sigma_b))])


def largest_component(binary):
    """Keep only the largest 26-connected component."""
    lab, n = ndi.label(binary, structure=np.ones((3, 3, 3)))
    if n <= 1:
        return binary
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == int(sizes.argmax())


def load_ras(path):
    """Load a NIfTI reoriented to canonical RAS.

    Reorienting matters: symmetry only means something along the true left-right
    anatomical axis. Working in raw voxel axes silently compares the wrong
    directions on any non-RAS acquisition.
    """
    img = nib.as_closest_canonical(nib.load(path))
    data = np.asanyarray(img.dataobj, dtype=np.float32)
    zooms = np.asarray(img.header.get_zooms()[:3], dtype=np.float64)
    return data, zooms, img


def build_head_mask(anat, zooms):
    """Segment the whole head (brain + skull + scalp) from background.

    Used as an anatomical reference frame: the head is bilaterally symmetric and
    its surface tells us how deep any voxel sits, which is what makes
    'is this mask shallow enough to be scalp' and 'where is the true midline'
    answerable without eyes.

    This is done by flood-filling the background inward from the volume faces
    and calling everything unreachable "head", rather than by thresholding.
    Thresholding fails here in a way that quietly poisons every depth-based
    metric: cortical bone is a signal void in T1, so a threshold carves the
    skull out of the head and leaves the head surface sitting directly on the
    brain. Depth then reads as ~0 for cortex and real scalp inclusion becomes
    undetectable. Flood filling keeps the dark skull, because it is enclosed by
    the scalp and therefore never reachable from outside.
    """
    nz = anat[anat > 0]
    thr = otsu_threshold(nz) if nz.size else 0.0
    tissue = anat > (0.20 * thr)       # generous: keep dim scalp and marrow
    # Close small gaps so background noise cannot tunnel through the scalp.
    tissue = ndi.binary_closing(tissue, structure=np.ones((3, 3, 3)), iterations=2)

    lab, _ = ndi.label(~tissue)
    faces = np.concatenate([
        lab[0].ravel(), lab[-1].ravel(),
        lab[:, 0].ravel(), lab[:, -1].ravel(),
        lab[:, :, 0].ravel(), lab[:, :, -1].ravel(),
    ])
    border_labels = np.unique(faces)
    border_labels = border_labels[border_labels != 0]
    outside = np.isin(lab, border_labels)

    head = ~outside
    head = largest_component(head)
    head = ndi.binary_fill_holes(head)
    return head


def mirror_about(vol, idx, axis=0):
    """Reflect a boolean volume about integer index `idx` along `axis`."""
    shift = vol.shape[axis] - 1 - 2 * idx
    out = np.roll(vol[::-1] if axis == 0 else np.flip(vol, axis), shift, axis=axis)
    if shift > 0:
        sl = [slice(None)] * 3; sl[axis] = slice(0, shift)
        out[tuple(sl)] = False
    elif shift < 0:
        sl = [slice(None)] * 3; sl[axis] = slice(shift, None)
        out[tuple(sl)] = False
    return out


def find_midsagittal(head, zooms, search_mm=20.0):
    """Locate the mid-sagittal plane by maximising the head's mirror overlap.

    The head centroid alone is a poor midline: whatever the field of view
    happens to include of the neck, jaw and shoulders drags it sideways by
    several millimetres, which is the same order as the mask displacement we
    are trying to detect. Searching for the plane of best bilateral symmetry
    pins the midline to actual anatomy instead.
    """
    cen = float(ndi.center_of_mass(head)[0])
    rng = max(1, int(round(search_mm / zooms[0])))
    base = int(round(cen))
    best_idx, best_dice = base, -1.0
    denom = float(head.sum())
    for d in range(-rng, rng + 1):
        idx = base + d
        if idx <= 0 or idx >= head.shape[0] - 1:
            continue
        mir = mirror_about(head, idx)
        dice = 2.0 * float((head & mir).sum()) / (denom + float(mir.sum()))
        if dice > best_dice:
            best_idx, best_dice = idx, dice
    return best_idx, best_dice


def surface_shell(mask, inner=True):
    """One-voxel shell just inside (or outside) the mask boundary."""
    if inner:
        return mask & ~ndi.binary_erosion(mask, np.ones((3, 3, 3)))
    return ndi.binary_dilation(mask, np.ones((3, 3, 3))) & ~mask


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def compute(anat, mask, zooms, vol_range):
    vox_mm3 = float(np.prod(zooms))
    cc = vox_mm3 / 1000.0                      # voxels -> cm^3
    m = mask > 0.5
    n_vox = int(m.sum())
    if n_vox == 0:
        raise SystemExit("ERROR: mask is empty (no voxels > 0.5)")

    out = {}
    notes = []

    # --- volume ------------------------------------------------------------
    brain_cm3 = n_vox * cc
    out["brain_volume_cm3"] = round(brain_cm3, 1)
    out["voxel_count"] = n_vox
    out["voxel_size_mm"] = [round(float(z), 3) for z in zooms]
    lo, hi = vol_range
    out["volume_in_reference_range"] = bool(lo <= brain_cm3 <= hi)
    out["volume_reference_range_cm3"] = [lo, hi]

    head = build_head_mask(anat, zooms)
    head_cm3 = float(head.sum()) * cc
    out["head_volume_cm3"] = round(head_cm3, 1)
    out["brain_to_head_ratio"] = round(brain_cm3 / head_cm3, 4) if head_cm3 else None

    # depth of every voxel below the head surface, in mm
    depth_mm = ndi.distance_transform_edt(head, sampling=zooms)

    # --- C1 residual skull / scalp -----------------------------------------
    # Brain never touches the outside of the head; scalp and skull do. A mask
    # with a meaningful share of its voxels sitting within a few mm of the head
    # surface has eaten non-brain tissue.
    shallow = m & (depth_mm < 4.0)
    out["shallow_mask_frac_pct"] = round(100.0 * float(shallow.sum()) / n_vox, 3)
    out["shallow_mask_cm3"] = round(float(shallow.sum()) * cc, 2)

    # Scalp fat is the brightest thing in a T1. Bright voxels in the outer shell
    # of the mask are the signature of an under-strip that kept the fat ring.
    core = m & (depth_mm > 12.0)
    if core.sum() > 100:
        core_p98 = float(np.percentile(anat[core], 98))
    else:
        core_p98 = float(np.percentile(anat[m], 98))
    rim = surface_shell(m, inner=True)
    rim_n = int(rim.sum())
    if rim_n:
        bright_rim = rim & (anat > 1.15 * core_p98)
        out["bright_rim_frac_pct"] = round(100.0 * float(bright_rim.sum()) / rim_n, 3)
    else:
        out["bright_rim_frac_pct"] = None

    # --- C2 tissue loss at poles -------------------------------------------
    # Look just outside the mask for tissue that is (a) brain-bright and
    # (b) deep inside the head. Restricting to a 10mm collar keeps neck, face
    # and orbital fat out of it while still catching clipped poles.
    collar = ndi.binary_dilation(m, np.ones((3, 3, 3)), iterations=int(round(10.0 / zooms.min()))) & ~m
    brain_vals = anat[m]
    # Require the missed voxels to look like actual grey/white matter. A looser
    # band (say the 20th percentile) sweeps in perilesional CSF, dura and
    # diploe, which sit just outside every correct mask and would give a
    # perfect extraction a large false "missed tissue" score.
    brain_lo = float(np.percentile(brain_vals, 45))
    brain_hi = float(np.percentile(brain_vals, 99.5))
    missed = collar & (depth_mm > 8.0) & (anat > brain_lo) & (anat < brain_hi)

    # Drop speckle by discarding small components rather than by morphological
    # opening. Opening with a 3-voxel structuring element annihilates a thin
    # shell -- which is exactly the shape an over-eroded mask leaves behind,
    # the single most important thing this metric has to catch.
    lab_ms, n_ms = ndi.label(missed, structure=np.ones((3, 3, 3)))
    if n_ms:
        sizes = np.bincount(lab_ms.ravel())
        sizes[0] = 0
        keep = np.where(sizes * cc >= 0.5)[0]
        missed = np.isin(lab_ms, keep)

    # Ignore anything below the mask's own inferior extent. Every extraction
    # tool cuts the brainstem at some arbitrary axial level, so cord and neck
    # tissue immediately below the mask is a convention, not an error -- and
    # left in, it dominates this metric and masks real pole clipping above.
    zc_all = np.argwhere(m)[:, 2]
    z_floor = int(zc_all.min()) + int(round(5.0 / zooms[2]))
    below = np.zeros_like(missed)
    below[:, :, :z_floor] = True
    out["missed_tissue_below_mask_cm3"] = round(float((missed & below).sum()) * cc, 2)
    missed = missed & ~below

    missed_cm3 = float(missed.sum()) * cc
    # Reported for localisation, deliberately NOT rated. Validation on synthetic
    # corruptions showed it does not separate a good mask from an over-eroded
    # one: temporalis muscle and dura sit just outside every correct mask at
    # brain-like intensity and depth, and they dominate the total. Use it to
    # answer "where is tissue missing" once another metric has established that
    # some is, not to decide whether any is.
    out["missed_tissue_cm3"] = round(missed_cm3, 2)

    # Localise the miss so the report can name a pole instead of saying "somewhere".
    out["missed_tissue_by_region"] = {}
    if missed.sum() > 0:
        cen = np.array(ndi.center_of_mass(m))
        coords = np.argwhere(missed).astype(np.float64)
        rel = (coords - cen) * zooms          # mm, RAS: +x right, +y anterior, +z superior
        regions = {
            "right":     rel[:, 0] > 0, "left":     rel[:, 0] < 0,
            "anterior":  rel[:, 1] > 0, "posterior": rel[:, 1] < 0,
            "superior":  rel[:, 2] > 0, "inferior":  rel[:, 2] < 0,
        }
        for k, sel in regions.items():
            v = float(sel.sum()) * cc
            if v >= 0.5:
                out["missed_tissue_by_region"][k] = round(v, 2)

    # --- C3 symmetry -------------------------------------------------------
    # Mirror about the HEAD midline, not the mask's own centroid. Mirroring a
    # mask about itself would score a one-hemisphere mask as perfectly
    # symmetric -- exactly the failure we most need to catch.
    mid_idx, head_sym_dice = find_midsagittal(head, zooms)
    mid_lr = float(mid_idx)
    out["midsagittal_voxel_index"] = int(mid_idx)
    out["head_symmetry_dice"] = round(head_sym_dice, 4)

    mirrored = mirror_about(m, mid_idx)
    inter = float((m & mirrored).sum())
    dice = 2.0 * inter / (float(m.sum()) + float(mirrored.sum()))
    out["lr_mirror_dice"] = round(dice, 4)

    left_vol = float(m[:mid_idx].sum()) * cc          # RAS: low x = Left
    right_vol = float(m[mid_idx + 1:].sum()) * cc
    tot = left_vol + right_vol
    out["left_volume_cm3"] = round(left_vol, 1)
    out["right_volume_cm3"] = round(right_vol, 1)
    out["lr_volume_asym_pct"] = round(100.0 * abs(right_vol - left_vol) / tot, 2) if tot else None

    mask_cen = np.array(ndi.center_of_mass(m))
    head_cen = np.array(ndi.center_of_mass(head))
    out["centroid_offset_lr_mm"] = round(abs(mask_cen[0] - mid_lr) * zooms[0], 2)
    out["centroid_offset_vs_head_mm"] = [
        round(float(abs(mask_cen[i] - head_cen[i]) * zooms[i]), 2) for i in range(3)
    ]

    # Where along the I->S axis is any asymmetry concentrated? Lets a text-only
    # report say "inferior slices" instead of just "asymmetric".
    zc = np.argwhere(m)[:, 2]
    z0, z1 = int(zc.min()), int(zc.max())
    bands = []
    for b in range(8):
        a = z0 + (z1 - z0) * b // 8
        bb = z0 + (z1 - z0) * (b + 1) // 8
        sl = m[:, :, a:bb + 1]
        lv = float(sl[:mid_idx].sum())
        rv = float(sl[mid_idx + 1:].sum())
        t = lv + rv
        bands.append(round(100.0 * abs(rv - lv) / t, 1) if t > 0 else None)
    out["lr_asym_pct_by_axial_band_inf_to_sup"] = bands

    # --- C4 topology -------------------------------------------------------
    lab, n_comp = ndi.label(m, structure=np.ones((3, 3, 3)))
    out["n_connected_components"] = int(n_comp)
    if n_comp > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        out["extra_component_cm3"] = round(float(sizes.sum() - sizes.max()) * cc, 3)
    else:
        out["extra_component_cm3"] = 0.0

    filled = ndi.binary_fill_holes(m)
    out["hole_volume_cm3"] = round(float((filled & ~m).sum()) * cc, 3)

    # --- C5 boundary tightness ---------------------------------------------
    # A correct brain boundary sits on the bright-to-dark cortex/CSF edge, so
    # the image gradient there is high. A mask bloated into homogeneous CSF, or
    # one cutting arbitrarily through white matter, sits on a flat gradient.
    a_norm = anat / (np.percentile(anat[m], 99) + 1e-6)
    gx, gy, gz = np.gradient(a_norm, *zooms)
    gmag = np.sqrt(gx * gx + gy * gy + gz * gz)
    interior = m & (depth_mm > 12.0)
    if rim_n and interior.sum() > 100:
        # Reported as context only, deliberately not rated. It looks like it
        # should measure boundary quality, but the sharpest edge in a T1 is
        # skin-to-air: a mask that swallows the whole head scores *higher* here
        # than a correct brain mask, so rating on it would invert the verdict.
        g_rim = float(np.mean(gmag[rim]))
        g_int = float(np.mean(gmag[interior]))
        out["boundary_gradient_ratio"] = round(g_rim / g_int, 3) if g_int > 0 else None

        core_med = float(np.median(anat[interior]))
        # Rim intensity relative to the mask core, two-sided: a mask dilated
        # into CSF has a dark rim, one eroded into white matter a bright one.
        out["boundary_darkness_ratio"] = round(
            float(np.median(anat[rim])) / (core_med + 1e-6), 3)
        # How much of the mask is frank CSF, skull or air. A tight brain mask
        # carries a little sulcal and ventricular CSF; a bloated one carries a
        # lot, and a whole-head mask carries the skull's signal void too.
        out["dark_voxel_frac_pct"] = round(
            100.0 * float((anat[m] < 0.25 * core_med).sum()) / n_vox, 2)
    else:
        out["boundary_gradient_ratio"] = None
        out["boundary_darkness_ratio"] = None
        out["dark_voxel_frac_pct"] = None

    # One-sided views of two-sided quantities, so each criterion can cite the
    # direction it cares about (see THRESHOLDS).
    out["brain_to_head_ratio_high"] = out["brain_to_head_ratio"]
    out["brain_to_head_ratio_low"] = out["brain_to_head_ratio"]
    out["rim_brightness_high"] = out["boundary_darkness_ratio"]
    out["rim_darkness_low"] = out["boundary_darkness_ratio"]

    # --- field of view truncation ------------------------------------------
    touching = []
    for ax, (loname, hiname) in enumerate(
            [("left", "right"), ("posterior", "anterior"), ("inferior", "superior")]):
        idx = np.argwhere(m)[:, ax]
        if idx.min() <= 0:
            touching.append(loname)
        if idx.max() >= m.shape[ax] - 1:
            touching.append(hiname)
    out["mask_touches_fov_edge"] = touching
    if touching:
        notes.append(
            f"Mask reaches the field-of-view edge ({', '.join(touching)}); "
            "apparent clipping there may be an acquisition limit, not an extraction error.")

    if not out["volume_in_reference_range"]:
        notes.append(
            f"Brain volume {brain_cm3:.1f} cm3 is outside the {lo}-{hi} cm3 reference "
            "range; confirm the expected range for this population before treating "
            "it as an error.")

    return out, notes


# ---------------------------------------------------------------------------
# Criterion roll-up
# ---------------------------------------------------------------------------

CRITERIA = [
    ("No residual skull or scalp signal",
     ["shallow_mask_frac_pct", "bright_rim_frac_pct", "brain_to_head_ratio_high"]),
    ("No excessive tissue loss at poles (frontal, temporal, occipital)",
     ["brain_to_head_ratio_low", "rim_brightness_high"]),
    ("Symmetric left-right and anterior-posterior coverage",
     ["lr_mirror_dice", "lr_volume_asym_pct", "centroid_offset_lr_mm"]),
    ("No internal holes or disconnected mask regions",
     ["extra_component_cm3", "hole_volume_cm3"]),
    ("Boundary tightness (not over-dilated into dura/CSF)",
     ["dark_voxel_frac_pct", "rim_darkness_low"]),
]


def roll_up(metrics):
    per_criterion = []
    for label, keys in CRITERIA:
        ratings = {k: rate(k, metrics.get(k)) for k in keys}
        worst = max(ratings.values(), key=lambda r: RANK[r])
        per_criterion.append(dict(criterion=label, rating=worst, metrics=ratings))
    return per_criterion


def overall(per_criterion, metrics):
    # Any single failing criterion sinks the mask. Each criterion here maps to a
    # defect that would propagate into registration, segmentation or volumetry,
    # so there is no useful sense in which a mask "fails one and is still fine".
    # A reviewer with additional context can override this -- and should say so
    # in writing -- but the default has to be the safe direction.
    n_fail = sum(1 for c in per_criterion if c["rating"] == "FAIL")
    n_bord = sum(1 for c in per_criterion if c["rating"] == "BORDERLINE")

    if n_fail >= 1:
        v = "FAIL"
    elif n_bord >= 1:
        v = "BORDERLINE"
    else:
        v = "PASS"
    if v == "PASS" and not metrics.get("volume_in_reference_range", True):
        v = "BORDERLINE"
    return v


def main():
    ap = argparse.ArgumentParser(description="Numeric brain-extraction QC")
    ap.add_argument("anat")
    ap.add_argument("mask")
    ap.add_argument("--json", dest="json_path", default=None)
    ap.add_argument("--vol-range", nargs=2, type=float, default=[900.0, 1900.0],
                    metavar=("LO", "HI"))
    ap.add_argument("--label", default=None, help="identifier echoed into the output")
    args = ap.parse_args()

    anat, zooms, aimg = load_ras(args.anat)
    mask, mzooms, mimg = load_ras(args.mask)

    if anat.shape != mask.shape:
        print(f"ERROR: anat shape {anat.shape} != mask shape {mask.shape}", file=sys.stderr)
        sys.exit(2)
    if not np.allclose(aimg.affine, mimg.affine, atol=1e-3):
        print("WARNING: anat and mask affines differ; results may be misaligned",
              file=sys.stderr)

    metrics, notes = compute(anat, mask, zooms, args.vol_range)
    per_criterion = roll_up(metrics)
    verdict = overall(per_criterion, metrics)

    result = dict(
        label=args.label,
        anat=args.anat,
        mask=args.mask,
        metrics=metrics,
        criteria=per_criterion,
        numeric_verdict=verdict,
        unverified=["Dura / superior sagittal sinus inclusion"],
        notes=notes,
    )

    # ---- human/model readable report -------------------------------------
    print(f"=== Numeric brain-extraction QC ===")
    if args.label:
        print(f"Label:  {args.label}")
    print(f"Anat:   {args.anat}")
    print(f"Mask:   {args.mask}")
    print()
    print(f"Brain volume        : {metrics['brain_volume_cm3']} cm3 "
          f"({'in' if metrics['volume_in_reference_range'] else 'OUTSIDE'} "
          f"{args.vol_range[0]:.0f}-{args.vol_range[1]:.0f} cm3)")
    print(f"Brain/head ratio    : {metrics['brain_to_head_ratio']}")
    print(f"L / R volume        : {metrics['left_volume_cm3']} / "
          f"{metrics['right_volume_cm3']} cm3  "
          f"(asym {metrics['lr_volume_asym_pct']}%)")
    print(f"L-R mirror Dice     : {metrics['lr_mirror_dice']}")
    print(f"Centroid off midline: {metrics['centroid_offset_lr_mm']} mm")
    print(f"Components / holes  : {metrics['n_connected_components']} comp, "
          f"{metrics['extra_component_cm3']} cm3 extra, "
          f"{metrics['hole_volume_cm3']} cm3 holes")
    print(f"Shallow (<4mm deep) : {metrics['shallow_mask_frac_pct']}% of mask")
    print(f"Bright rim fraction : {metrics['bright_rim_frac_pct']}%")
    print(f"Missed tissue       : {metrics['missed_tissue_cm3']} cm3 "
          f"{metrics['missed_tissue_by_region'] or ''}")
    print(f"  (below mask floor : {metrics['missed_tissue_below_mask_cm3']} cm3, "
          f"not rated -- brainstem cut level is a tool convention)")
    print(f"Dark voxels in mask : {metrics['dark_voxel_frac_pct']}% "
          f"(CSF/skull/air; high means bloated)")
    print(f"Boundary darkness   : {metrics['boundary_darkness_ratio']} "
          f"(rim/core intensity; low = rim in CSF, high = rim cutting tissue)")
    print(f"Boundary gradient   : {metrics['boundary_gradient_ratio']} "
          f"(context only, not rated)")
    print(f"L-R asym by axial band (inf->sup): "
          f"{metrics['lr_asym_pct_by_axial_band_inf_to_sup']}")
    print()
    print(f"{'Criterion':<62} {'Rating'}")
    print("-" * 76)
    for c in per_criterion:
        print(f"{c['criterion']:<62} {c['rating']}")
        for k, r in c["metrics"].items():
            if r != "PASS":
                print(f"    -> {k} = {metrics.get(k)}  [{r}]")
    print(f"{'Dura / superior sagittal sinus inclusion':<62} UNVERIFIED")
    print("-" * 76)
    print(f"NUMERIC VERDICT: {verdict}")
    for n in notes:
        print(f"NOTE: {n}")

    if args.json_path:
        with open(args.json_path, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"\nJSON written: {args.json_path}")


if __name__ == "__main__":
    main()
