#!/usr/bin/env python3
"""
Numeric QC for a lesion segmentation, aware of what kind of lesion it should be.

A lesion mask cannot be judged like a brain mask. There is no expected volume, no
expected shape, and no symmetry requirement -- in fact the correct answer differs
by lesion type in ways that invert each other. One large unilateral component is
exactly right for a stroke and exactly wrong for small-vessel WMH. So the type
must be supplied, and the plausibility checks are chosen from it.

Two checks do most of the work and neither needs vision:

  containment   Does the mask stay inside the brain? Lesion voxels in skull,
                scalp or air are unambiguous segmenter failures.
  signature     Do the labelled voxels actually have the intensity the lesion
                type implies -- FLAIR-bright for WMH, CSF-dark on T1 for a
                chronic cavity? A segmenter that labels normal-appearing tissue
                has failed regardless of how plausible its mask looks.

Usage:
  lesion_qc_metrics.py --lesion MASK --type {acute_stroke,chronic_stroke,wmh}
                       [--brain-mask M] [--flair F] [--t1 T] [--dwi D] [--adc A]
                       [--json out.json]

Exit codes: 0 measured, 2 input error.
Requires: numpy, nibabel, scipy.
"""

import argparse
import json
import sys

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi

# Plausible total lesion volumes. Wide on purpose -- these catch order-of-
# magnitude failures (an empty mask, a whole-hemisphere mask), not clinical
# abnormality. A volume outside the range is a prompt to look, not a verdict.
VOLUME_RANGE_CM3 = {
    "acute_stroke":   (0.5, 300.0),
    "chronic_stroke": (1.0, 400.0),
    "wmh":            (0.5, 200.0),
}

# What the mask should look like, per type.
EXPECT = {
    "acute_stroke": dict(
        focal=True, bilateral=False,
        note="one dominant unilateral cluster in a vascular territory"),
    "chronic_stroke": dict(
        focal=True, bilateral=False,
        note="one dominant unilateral cavity"),
    "wmh": dict(
        focal=False, bilateral=True,
        note="many bilateral periventricular and deep white matter foci"),
}

RANK = {"PASS": 0, "BORDERLINE": 1, "FAIL": 2, "UNVERIFIED": 0}


def load_ras(p):
    img = nib.as_closest_canonical(nib.load(p))
    return (np.asanyarray(img.dataobj, dtype=np.float32),
            np.asarray(img.header.get_zooms()[:3], dtype=np.float64),
            img.shape, np.asarray(img.affine, dtype=np.float64))


def same_grid(shape_a, affine_a, shape_b, affine_b):
    return shape_a == shape_b and np.allclose(
        affine_a, affine_b, rtol=0.0, atol=1e-3
    )


def mirror_about(vol, idx):
    shift = vol.shape[0] - 1 - 2 * idx
    out = np.roll(vol[::-1], shift, axis=0)
    if shift > 0:
        out[:shift] = False
    elif shift < 0:
        out[shift:] = False
    return out


def find_midsagittal(mask, zooms, search_mm=20.0):
    cen = float(ndi.center_of_mass(mask)[0])
    rng = max(1, int(round(search_mm / zooms[0])))
    base, best, best_d = int(round(cen)), int(round(cen)), -1.0
    denom = float(mask.sum())
    for d in range(-rng, rng + 1):
        i = base + d
        if i <= 0 or i >= mask.shape[0] - 1:
            continue
        mir = mirror_about(mask, i)
        dice = 2.0 * float((mask & mir).sum()) / (denom + float(mir.sum()))
        if dice > best_d:
            best, best_d = i, dice
    return best, best_d


def robust_z(vol, mask):
    v = vol[mask]
    med = float(np.median(v))
    q1, q3 = np.percentile(v, [25, 75])
    return (vol - med) / (float(q3 - q1) or 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesion", required=True)
    ap.add_argument("--type", required=True,
                    choices=["acute_stroke", "chronic_stroke", "wmh"])
    ap.add_argument("--brain-mask", dest="brain_mask", default=None)
    for m in ("t1", "flair", "dwi", "adc"):
        ap.add_argument(f"--{m}", default=None)
    ap.add_argument("--json", dest="json_path", default=None)
    args = ap.parse_args()

    les, zooms, shape, lesion_affine = load_ras(args.lesion)
    m = les > 0.5
    cc = float(np.prod(zooms)) / 1000.0
    if m.sum() == 0:
        print("FAIL: lesion mask is empty (no voxels > 0.5)")
        if args.json_path:
            json.dump(dict(lesion_type=args.type, numeric_verdict="FAIL",
                           metrics=dict(lesion_volume_cm3=0.0),
                           criteria=[dict(criterion="Non-empty mask",
                                          rating="FAIL")]),
                      open(args.json_path, "w"), indent=2)
        sys.exit(0)

    mets, crit, notes = {}, [], []

    # ---- volume and clusters ---------------------------------------------
    lab, n = ndi.label(m, structure=np.ones((3, 3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:] * cc)[::-1]
    vol = float(m.sum()) * cc
    mets["lesion_volume_cm3"] = round(vol, 2)
    mets["n_clusters"] = int(n)
    mets["largest_cluster_cm3"] = round(float(sizes[0]), 2)
    mets["largest_cluster_fraction"] = round(float(sizes[0]) / vol, 3)
    mets["median_cluster_cm3"] = round(float(np.median(sizes)), 4)

    lo, hi = VOLUME_RANGE_CM3[args.type]
    mets["volume_reference_range_cm3"] = [lo, hi]
    in_range = lo <= vol <= hi
    mets["volume_in_reference_range"] = bool(in_range)
    crit.append(dict(criterion="Lesion volume is plausible for the stated type",
                     rating="PASS" if in_range else "FAIL",
                     evidence=f"{vol:.2f} cm3 vs expected {lo}-{hi} cm3"))

    # ---- containment within the brain -------------------------------------
    if args.brain_mask:
        bm, _, bs, brain_affine = load_ras(args.brain_mask)
        if not same_grid(bs, brain_affine, shape, lesion_affine):
            print(
                "ERROR: brain mask grid differs from lesion grid "
                "(shape and affine must both match)",
                file=sys.stderr,
            )
            sys.exit(2)
        brain = bm > 0.5
        outside = float((m & ~brain).sum()) * cc
        pct = 100.0 * outside / vol
        mets["lesion_outside_brain_cm3"] = round(outside, 3)
        mets["lesion_outside_brain_pct"] = round(pct, 2)
        r = "PASS" if pct <= 1.0 else ("BORDERLINE" if pct <= 5.0 else "FAIL")
        crit.append(dict(criterion="Lesion is contained within the brain mask",
                         rating=r,
                         evidence=f"{pct:.2f}% of lesion volume ({outside:.2f} cm3) "
                                  "lies outside the brain mask"))
        mid_idx, head_dice = find_midsagittal(brain, zooms)
        mets["head_symmetry_dice"] = round(head_dice, 4)
    else:
        brain = None
        mid_idx, _ = find_midsagittal(m, zooms)
        notes.append("No brain mask supplied: containment could not be checked, "
                     "and the midline was estimated from the lesion itself, which "
                     "makes laterality unreliable. Supply --brain-mask.")
        crit.append(dict(criterion="Lesion is contained within the brain mask",
                         rating="UNVERIFIED", evidence="no brain mask supplied"))

    # ---- laterality --------------------------------------------------------
    left = float(m[:mid_idx].sum()) * cc
    right = float(m[mid_idx + 1:].sum()) * cc
    lat = 100.0 * abs(right - left) / (left + right) if (left + right) else 0.0
    mets["left_cm3"], mets["right_cm3"] = round(left, 2), round(right, 2)
    mets["laterality_pct"] = round(lat, 1)

    # ---- pattern matches the stated type ----------------------------------
    exp = EXPECT[args.type]
    frac = mets["largest_cluster_fraction"]
    if exp["focal"]:
        ok = frac >= 0.5 and lat >= 25.0
        ev = (f"largest cluster is {frac:.0%} of the load, laterality {lat:.0f}% "
              f"-- expected {exp['note']}")
        r = "PASS" if ok else ("BORDERLINE" if (frac >= 0.5 or lat >= 25.0) else "FAIL")
    else:
        ok = frac <= 0.7 and lat <= 40.0
        ev = (f"largest cluster is {frac:.0%} of the load across {n} clusters, "
              f"laterality {lat:.0f}% -- expected {exp['note']}")
        r = "PASS" if ok else ("BORDERLINE" if (frac <= 0.7 or lat <= 40.0) else "FAIL")
    crit.append(dict(criterion="Spatial pattern matches the stated lesion type",
                     rating=r, evidence=ev))

    # ---- intensity signature ----------------------------------------------
    # The check that catches a segmenter labelling normal tissue. Compared
    # against non-lesion brain so it is self-calibrating per scan.
    sig_rating, sig_ev = "UNVERIFIED", "no suitable modality supplied"
    sig_note = None
    ref = brain if brain is not None else np.ones_like(m)
    ref_nonles = ref & ~ndi.binary_dilation(
        m, np.ones((3, 3, 3)), iterations=max(1, int(round(5.0 / zooms.min()))))

    if args.type == "wmh" and args.flair:
        fl, _, fs, flair_affine = load_ras(args.flair)
        if not same_grid(fs, flair_affine, shape, lesion_affine):
            sig_ev = "FLAIR supplied but its grid differs from the lesion grid"
            sig_note = sig_ev + "; use a registered copy or leave UNVERIFIED."
        elif ref_nonles.sum() > 100:
            z = robust_z(fl, ref_nonles)
            med_z = float(np.median(z[m]))
            mets["lesion_flair_robust_z"] = round(med_z, 2)
            sig_rating = "PASS" if med_z >= 1.5 else (
                "BORDERLINE" if med_z >= 0.8 else "FAIL")
            sig_ev = (f"median FLAIR robust-z inside the mask is {med_z:.2f} "
                      "vs normal-appearing brain; WMH should be clearly bright")
    elif args.type == "chronic_stroke" and args.t1:
        t1, _, ts, t1_affine = load_ras(args.t1)
        if not same_grid(ts, t1_affine, shape, lesion_affine):
            sig_ev = "T1 supplied but its grid differs from the lesion grid"
            sig_note = sig_ev + "; use a registered copy or leave UNVERIFIED."
        elif ref_nonles.sum() > 100:
            ratio = float(np.median(t1[m])) / (float(np.median(t1[ref_nonles])) + 1e-6)
            mets["lesion_t1_to_brain_ratio"] = round(ratio, 3)
            sig_rating = "PASS" if ratio <= 0.7 else (
                "BORDERLINE" if ratio <= 0.85 else "FAIL")
            sig_ev = (f"median T1 inside the mask is {ratio:.2f}x normal-appearing "
                      "brain; a chronic cavity should be markedly darker")
    elif args.type == "acute_stroke" and args.dwi and args.adc:
        dw, _, ds, dwi_affine = load_ras(args.dwi)
        ad, _, as_, adc_affine = load_ras(args.adc)
        dwi_matches = same_grid(ds, dwi_affine, shape, lesion_affine)
        adc_matches = same_grid(as_, adc_affine, shape, lesion_affine)
        if not (dwi_matches and adc_matches):
            sig_ev = "DWI or ADC supplied but its grid differs from the lesion grid"
            sig_note = sig_ev + "; use registered copies or leave UNVERIFIED."
        elif ref_nonles.sum() > 100:
            dz = float(np.median(robust_z(dw, ref_nonles)[m]))
            ar = float(np.median(ad[m])) / (float(np.median(ad[ref_nonles])) + 1e-6)
            mets["lesion_dwi_robust_z"] = round(dz, 2)
            mets["lesion_adc_ratio"] = round(ar, 3)
            good = dz >= 1.0 and ar <= 0.85
            sig_rating = "PASS" if good else (
                "BORDERLINE" if (dz >= 1.0 or ar <= 0.85) else "FAIL")
            sig_ev = (f"DWI robust-z {dz:.2f} (want high) and ADC ratio {ar:.2f} "
                      "(want low) -- restricted diffusion should be present")
    crit.append(dict(criterion="Labelled voxels carry the expected intensity signature",
                     rating=sig_rating, evidence=sig_ev))
    if sig_rating == "UNVERIFIED":
        notes.append(sig_note or
                     "Intensity signature unchecked. Supply the modality the "
                     "lesion type is defined on (FLAIR for WMH, T1 for chronic "
                     "stroke, DWI+ADC for acute stroke) -- without it, a mask over "
                     "normal-appearing tissue cannot be distinguished from a "
                     "correct one.")

    # ---- fragmentation -----------------------------------------------------
    tiny = int((sizes < 0.02).sum())
    mets["n_clusters_under_0.02_cm3"] = tiny
    if n > 0 and tiny / n > 0.5 and n > 20:
        crit.append(dict(criterion="Mask is not dominated by noise specks",
                         rating="BORDERLINE",
                         evidence=f"{tiny} of {n} clusters are under 0.02 cm3; "
                                  "consider a minimum-cluster-size filter"))
    else:
        crit.append(dict(criterion="Mask is not dominated by noise specks",
                         rating="PASS",
                         evidence=f"{tiny} of {n} clusters under 0.02 cm3"))

    worst = max((c["rating"] for c in crit), key=lambda r: RANK[r])
    verdict = "FAIL" if worst == "FAIL" else ("BORDERLINE" if worst == "BORDERLINE"
                                              else "PASS")

    # ---- report ------------------------------------------------------------
    print("=== Lesion segmentation QC ===")
    print(f"Lesion type : {args.type}")
    print(f"Mask        : {args.lesion}")
    print()
    for k, v in mets.items():
        print(f"  {k:<34} {v}")
    print()
    print(f"{'Criterion':<58} {'Rating'}")
    print("-" * 74)
    for c in crit:
        print(f"{c['criterion']:<58} {c['rating']}")
        print(f"    {c['evidence']}")
    print("-" * 74)
    print(f"NUMERIC VERDICT: {verdict}")
    for nte in notes:
        print(f"NOTE: {nte}")
    print("\nNot assessed numerically: whether the lesion boundary is "
          "anatomically correct, and whether the lesion is what it is labelled "
          "as. Both need visual or clinical review.")

    if args.json_path:
        json.dump(dict(lesion_type=args.type, lesion=args.lesion, metrics=mets,
                       criteria=crit, numeric_verdict=verdict, notes=notes),
                  open(args.json_path, "w"), indent=2)
        print(f"\nJSON written: {args.json_path}")


if __name__ == "__main__":
    main()
