#!/usr/bin/env python3
"""
Lesion signature probe: rank lesion-type hypotheses from image measurements.

This exists so that a model with no image-viewing capability can still reach a
defensible lesion-type hypothesis instead of guessing from a filename. Lesion
types differ in ways that are measurable, not just visible:

  acute ischaemic stroke  restricted diffusion (DWI bright, ADC dark), usually
                          one focal unilateral lesion in a vascular territory
  chronic stroke          CSF-like cavity on T1, unilateral, often large, with
                          ex-vacuo ventricular asymmetry
  WMH                     FLAIR-bright, bilateral and roughly symmetric, many
                          small confluent foci hugging the ventricles

The probe measures those signatures and ranks hypotheses. It does NOT diagnose.
Its job is to narrow the field and to say honestly how confident the evidence
allows it to be, so a human or a vision-capable model can confirm.

Usage:
  lesion_signature.py --t1 T1.nii.gz [--flair F.nii.gz] [--dwi D.nii.gz]
                      [--adc A.nii.gz] [--t2 T2.nii.gz] [--swi S.nii.gz]
                      [--mask brain_mask.nii.gz] [--json out.json]

Exit codes: 0 measured, 2 input error.
Requires: numpy, nibabel, scipy.
"""

import argparse
import json
import sys

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi

# --------------------------------------------------------------------------
# Thresholds. In one place so they can be retuned per site and per protocol.
# Hyperintensity cut-offs are in robust z units (median / IQR within brain),
# which travels across scanners far better than raw intensity.
# --------------------------------------------------------------------------
CFG = dict(
    flair_hyper_z=1.8,        # robust-z above brain median to call FLAIR-bright
    adc_restricted_frac=0.75,  # ADC below this fraction of brain median = restricted
    dwi_hyper_z=1.5,
    t1_cavity_frac=0.55,      # T1 below this fraction of brain median = CSF-like
    t1_contralateral_normal_frac=0.80,  # mirror location must look like normal tissue
    cavity_min_depth_mm=6.0,  # sulcal CSF hugs the surface; a cavity sits deeper
    cavity_open_mm=3.0,       # sulcal CSF is sheet-like; a cavity survives opening
    # Set from the measured noise floor, not from what a cavity "should" be.
    # On a healthy adult T1 this detector still returns ~13 cm3 of asymmetric
    # CSF-like tissue after every filter, because head tilt, partial volume and
    # genuinely asymmetric CSF spaces do not cancel under a single reflection.
    # A planted 45 cm3 cavity measured 91 cm3. Sitting the cut-off between them
    # trades away small lesions for not calling chronic stroke on every normal
    # brain -- the right trade for a router whose fallback is to ask.
    cavity_min_cm3=25.0,
    min_cluster_cm3=0.05,     # ignore specks below this
    periventricular_mm=10.0,  # distance from ventricle proxy counted as PV
    symmetric_lat_pct=25.0,   # |L-R|/total below this = bilateral/symmetric
    focal_dominance=0.60,     # largest cluster >= this fraction of load = focal
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def otsu(vals, nbins=256):
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return 0.0
    hist, edges = np.histogram(vals, bins=nbins)
    c = 0.5 * (edges[:-1] + edges[1:])
    w = hist.astype(np.float64)
    tot = w.sum()
    if tot == 0:
        return float(c[0])
    om = np.cumsum(w) / tot
    mu = np.cumsum(w * c) / tot
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mu[-1] * om - mu) ** 2 / (om * (1 - om))
    return float(c[int(np.nanargmax(sb))]) if np.any(np.isfinite(sb)) else float(c[0])


def largest_component(binary):
    lab, n = ndi.label(binary, structure=np.ones((3, 3, 3)))
    if n <= 1:
        return binary
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    return lab == int(sizes.argmax())


def load_ras(path):
    img = nib.as_closest_canonical(nib.load(path))
    return (np.asanyarray(img.dataobj, dtype=np.float32),
            np.asarray(img.header.get_zooms()[:3], dtype=np.float64),
            img.affine, img.shape)


def robust_z(vol, mask):
    """Median/IQR normalisation inside the brain. Scanner- and protocol-robust."""
    v = vol[mask]
    if v.size == 0:
        return np.zeros_like(vol)
    med = float(np.median(v))
    q1, q3 = np.percentile(v, [25, 75])
    iqr = float(q3 - q1) or 1.0
    return (vol - med) / iqr


def crude_brain_mask(vol, zooms):
    """Fallback brain mask. Deliberately crude and reported as such."""
    thr = otsu(vol[vol > 0])
    m = vol > thr
    m = ndi.binary_closing(m, np.ones((3, 3, 3)), iterations=2)
    m = largest_component(m)
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_erosion(m, np.ones((3, 3, 3)),
                           iterations=max(1, int(round(4.0 / zooms.min()))))
    return largest_component(m)


def mirror_about(vol, idx):
    shift = vol.shape[0] - 1 - 2 * idx
    out = np.roll(vol[::-1], shift, axis=0)
    if shift > 0:
        out[:shift] = False
    elif shift < 0:
        out[shift:] = False
    return out


def find_midsagittal(mask, zooms, search_mm=20.0):
    """Plane of best bilateral symmetry. Laterality is meaningless without it."""
    cen = float(ndi.center_of_mass(mask)[0])
    rng = max(1, int(round(search_mm / zooms[0])))
    base = int(round(cen))
    best, best_d = base, -1.0
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


def cluster_stats(binary, cc, min_cm3):
    """Component count and size distribution -- the many-small vs one-big signal."""
    lab, n = ndi.label(binary, structure=np.ones((3, 3, 3)))
    if n == 0:
        return dict(count=0, total_cm3=0.0, largest_cm3=0.0,
                    largest_fraction=0.0, median_cm3=0.0)
    sizes = np.bincount(lab.ravel())[1:] * cc
    sizes = np.sort(sizes[sizes >= min_cm3])[::-1]
    if sizes.size == 0:
        return dict(count=0, total_cm3=0.0, largest_cm3=0.0,
                    largest_fraction=0.0, median_cm3=0.0)
    tot = float(sizes.sum())
    return dict(count=int(sizes.size), total_cm3=round(tot, 2),
                largest_cm3=round(float(sizes[0]), 2),
                largest_fraction=round(float(sizes[0]) / tot, 3),
                median_cm3=round(float(np.median(sizes)), 3))


def laterality_pct(binary, mid_idx, cc):
    left = float(binary[:mid_idx].sum()) * cc
    right = float(binary[mid_idx + 1:].sum()) * cc
    tot = left + right
    if tot <= 0:
        return None, 0.0, 0.0
    return round(100.0 * abs(right - left) / tot, 1), round(left, 2), round(right, 2)


def ventricle_proxy(t1, brain, depth_mm, zooms, mid_idx):
    """Approximate the lateral ventricles: deep, near-midline CSF.

    Two properties separate ventricles from the other CSF in a T1, and neither
    is a bounding box: ventricles sit deep inside the brain where sulcal and
    subarachnoid CSF is shallow, and they straddle the midline where a stroke
    cavity is lateral. Selecting on depth and midline distance keeps the
    temporal horns and atria, which a central box excludes -- and an excluded
    horn reads downstream as an asymmetric CSF-like "cavity", which is how a
    healthy brain acquires a spurious chronic infarct.

    Only a proxy. It feeds a periventricular *fraction*, which is relative, so
    being consistently a little off still separates ventricle-hugging WMH from
    peripheral lesions.
    """
    if t1 is None or brain.sum() == 0:
        return None
    cc = float(np.prod(zooms)) / 1000.0
    dark = brain & (t1 < np.percentile(t1[brain], 10))
    deep = dark & (depth_mm > 12.0)
    if deep.sum() < 50:
        return None

    lab, n = ndi.label(deep, structure=np.ones((3, 3, 3)))
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())
    keep = []
    for l in range(1, n + 1):
        if sizes[l] * cc < 0.5:
            continue
        # near-midline: ventricles straddle it, a cavity does not
        xs = np.argwhere(lab == l)[:, 0]
        if abs(float(xs.mean()) - mid_idx) * zooms[0] <= 30.0:
            keep.append(l)
    if not keep:
        return None
    return np.isin(lab, keep)


# --------------------------------------------------------------------------
# Feature extraction
# --------------------------------------------------------------------------

def analyse(vols, zooms, brain, cc, mid_idx):
    """Compute every feature we can from whatever modalities are present."""
    f = {}
    z = {k: robust_z(v, brain) for k, v in vols.items()}

    # ---- FLAIR / T2 hyperintensity ---------------------------------------
    for key in ("flair", "t2"):
        if key not in vols:
            continue
        hyper = brain & (z[key] > CFG["flair_hyper_z"])
        hyper = ndi.binary_opening(hyper, np.ones((3, 3, 3)))
        st = cluster_stats(hyper, cc, CFG["min_cluster_cm3"])
        lat, lv, rv = laterality_pct(hyper, mid_idx, cc)
        f[f"{key}_hyper"] = dict(**st, laterality_pct=lat,
                                 left_cm3=lv, right_cm3=rv)
        f[f"_{key}_hyper_mask"] = hyper

    # ---- restricted diffusion (acute ischaemia) --------------------------
    if "dwi" in vols and "adc" in vols:
        adc_med = float(np.median(vols["adc"][brain]))
        restricted = (brain
                      & (z["dwi"] > CFG["dwi_hyper_z"])
                      & (vols["adc"] < CFG["adc_restricted_frac"] * adc_med))
        restricted = ndi.binary_opening(restricted, np.ones((3, 3, 3)))
        st = cluster_stats(restricted, cc, CFG["min_cluster_cm3"])
        lat, lv, rv = laterality_pct(restricted, mid_idx, cc)
        f["restricted_diffusion"] = dict(**st, laterality_pct=lat,
                                         left_cm3=lv, right_cm3=rv)
        f["_restricted_mask"] = restricted
    elif "dwi" in vols:
        f["restricted_diffusion"] = dict(
            note="DWI present without ADC -- restricted diffusion cannot be "
                 "confirmed. DWI hyperintensity alone does not distinguish acute "
                 "infarct from T2 shine-through.")

    # ---- T1 cavity (chronic stroke / encephalomalacia) -------------------
    if "t1" in vols:
        t1 = vols["t1"]
        t1_med = float(np.median(t1[brain]))
        depth_brain = ndi.distance_transform_edt(brain, sampling=zooms)

        # A chronic cavity is CSF-dark *where the other hemisphere is normal
        # tissue*. That contrast with the mirror location is what makes it a
        # lesion rather than anatomy, and testing it directly is far more robust
        # than trying to enumerate and subtract every normal CSF space. The
        # ventricles are dark on both sides and drop out; so do the sulci,
        # cisterns and fissures, which come in matched pairs.
        #
        # The mirrored volume is smoothed first so that a few millimetres of
        # head tilt -- which no single reflection plane can correct -- does not
        # land the comparison point inside a sulcus and invent a cavity.
        mir = np.roll(t1[::-1], t1.shape[0] - 1 - 2 * mid_idx, axis=0)
        mir_s = ndi.gaussian_filter(mir, sigma=3.0 / zooms.mean())

        cavity = (brain
                  & (t1 < CFG["t1_cavity_frac"] * t1_med)
                  & (mir_s > CFG["t1_contralateral_normal_frac"] * t1_med))

        # Sulcal CSF is shallow and sheet-like; a cavity is deep and blobby.
        # These two gates clean up what the mirror test leaves behind, mostly
        # near the surface where the reflection is least reliable.
        cavity &= depth_brain > CFG["cavity_min_depth_mm"]
        raw_cm3 = round(float(cavity.sum()) * cc, 2)
        cavity = ndi.binary_opening(
            cavity, np.ones((3, 3, 3)),
            iterations=max(1, int(round(CFG["cavity_open_mm"] / zooms.min()))))

        st = cluster_stats(cavity, cc, CFG["cavity_min_cm3"])
        lat, lv, rv = laterality_pct(cavity, mid_idx, cc)
        f["t1_cavity"] = dict(**st, laterality_pct=lat, left_cm3=lv, right_cm3=rv,
                              csf_like_before_opening_cm3=raw_cm3)

        # Kept only for the periventricular fraction below, which is a relative
        # measure and tolerant of an imperfect proxy. It is deliberately not
        # used to gate the cavity any more -- the mirror test does that better.
        vent = ventricle_proxy(t1, brain, depth_brain, zooms, mid_idx)

        if vent is not None:
            vlat, vl, vr = laterality_pct(vent, mid_idx, cc)
            f["ventricle_proxy"] = dict(volume_cm3=round(float(vent.sum()) * cc, 2),
                                        laterality_pct=vlat,
                                        left_cm3=vl, right_cm3=vr)
            f["_vent_mask"] = vent

    # ---- periventricular fraction of the FLAIR load ----------------------
    vent = f.get("_vent_mask")
    hyper = f.get("_flair_hyper_mask", f.get("_t2_hyper_mask"))
    if vent is not None and hyper is not None and hyper.sum() > 0:
        dist = ndi.distance_transform_edt(~vent, sampling=zooms)
        pv = hyper & (dist <= CFG["periventricular_mm"])
        f["periventricular_fraction"] = round(float(pv.sum()) / float(hyper.sum()), 3)

    return {k: v for k, v in f.items() if not k.startswith("_")}, f


# --------------------------------------------------------------------------
# Hypothesis ranking
# --------------------------------------------------------------------------

def rank(f, present):
    """Turn features into ranked hypotheses with explicit supporting evidence.

    Rules, not a classifier. A rule set can state its own reasoning, which is
    what makes the output auditable by the person who has to sign off on it.
    """
    H = []

    rd = f.get("restricted_diffusion")
    if rd and rd.get("total_cm3", 0) >= 1.0:
        ev = [f"restricted diffusion (DWI-bright, ADC-dark) {rd['total_cm3']} cm3",
              f"{rd['count']} cluster(s), largest {rd['largest_cm3']} cm3",
              f"laterality {rd['laterality_pct']}% (L {rd['left_cm3']} / R {rd['right_cm3']} cm3)"]
        conf = "HIGH" if (rd["largest_fraction"] >= CFG["focal_dominance"]
                          and (rd["laterality_pct"] or 0) > CFG["symmetric_lat_pct"]) else "MEDIUM"
        H.append(dict(lesion_type="acute_ischaemic_stroke", confidence=conf,
                      in_scope=True, evidence=ev))
    elif rd and "note" in rd:
        H.append(dict(lesion_type="acute_ischaemic_stroke", confidence="UNKNOWN",
                      in_scope=True, evidence=[rd["note"]]))

    cav = f.get("t1_cavity")
    if cav and cav.get("largest_cm3", 0) >= 3.0:
        ev = [f"CSF-like T1 cavity outside the ventricles, largest {cav['largest_cm3']} cm3",
              f"laterality {cav['laterality_pct']}%"]
        conf = "MEDIUM"
        vp = f.get("ventricle_proxy")
        if (vp and (vp.get("volume_cm3") or 0) >= 5.0
                and (vp.get("laterality_pct") or 0) > 20.0):
            ev.append(f"ventricular asymmetry {vp['laterality_pct']}% "
                      "(consistent with ex-vacuo dilation)")
            conf = "HIGH"
        if (cav.get("laterality_pct") or 0) > CFG["symmetric_lat_pct"]:
            ev.append("unilateral, as expected for a vascular territory")
        H.append(dict(lesion_type="chronic_stroke", confidence=conf,
                      in_scope=True, evidence=ev))

    hyp = f.get("flair_hyper") or f.get("t2_hyper")
    if hyp and hyp.get("total_cm3", 0) >= 1.0:
        pv = f.get("periventricular_fraction")
        lat = hyp.get("laterality_pct")
        ev = [f"FLAIR/T2 hyperintense load {hyp['total_cm3']} cm3 in "
              f"{hyp['count']} cluster(s)",
              f"largest cluster {hyp['largest_cm3']} cm3 "
              f"({hyp['largest_fraction']:.0%} of load)",
              f"laterality {lat}%"]
        if pv is not None:
            ev.append(f"periventricular fraction {pv:.0%}")
        score = 0
        if lat is not None and lat <= CFG["symmetric_lat_pct"]:
            score += 1                       # bilateral/symmetric
        if hyp["largest_fraction"] < CFG["focal_dominance"]:
            score += 1                       # distributed, not one focus
        if hyp["count"] >= 5:
            score += 1                       # many foci
        if pv is not None and pv >= 0.4:
            score += 1                       # hugs the ventricles
        conf = "HIGH" if score >= 3 else ("MEDIUM" if score == 2 else "LOW")
        H.append(dict(lesion_type="wmh", confidence=conf, in_scope=True,
                      evidence=ev))

        # A FLAIR-bright burden that is focal and unilateral is not WMH.
        if (lat is not None and lat > CFG["symmetric_lat_pct"]
                and hyp["largest_fraction"] >= CFG["focal_dominance"]):
            H.append(dict(
                lesion_type="focal_lesion_not_wmh", confidence="MEDIUM",
                in_scope=False,
                evidence=["FLAIR burden is unilateral and dominated by a single "
                          "cluster, which is not the WMH pattern",
                          "consider subacute/chronic infarct, tumour, "
                          "demyelinating lesion or abscess -- needs visual or "
                          "clinical review before segmenting"]))

        # WMH and MS share the FLAIR signature; no numeric rule separates them.
        if hyp["count"] >= 3:
            H.append(dict(
                lesion_type="ms_cannot_exclude", confidence="UNKNOWN",
                in_scope=False,
                evidence=["multifocal FLAIR hyperintensity is common to WMH and "
                          "MS; juxtacortical, infratentorial and Dawson's-finger "
                          "morphology distinguish them and are not measured here",
                          "confirm with clinical context or visual review before "
                          "treating this as WMH"]))

    if not H:
        H.append(dict(lesion_type="none_detected", confidence="LOW", in_scope=True,
                      evidence=["no lesion signature above threshold in the "
                                "supplied modalities",
                                "absence of a signature is not absence of a lesion "
                                "-- check that the right sequences were supplied "
                                "and that thresholds suit this protocol"]))

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
    H.sort(key=lambda h: (order[h["confidence"]], not h["in_scope"]))
    return H


def missing_modality_notes(present):
    n = []
    if "dwi" in present and "adc" not in present:
        n.append("ADC missing: acute infarct cannot be confirmed from DWI alone "
                 "(T2 shine-through mimics it). Supply ADC.")
    if "dwi" not in present and "adc" not in present:
        n.append("No DWI/ADC: acute ischaemia cannot be assessed at all. If acute "
                 "stroke is the question, this scan cannot answer it.")
    if "flair" not in present and "t2" not in present:
        n.append("No FLAIR or T2: WMH and most chronic lesion burden cannot be "
                 "assessed.")
    if "t1" not in present:
        n.append("No T1w: chronic cavity detection and the ventricle proxy are "
                 "unavailable.")
    if "swi" in present:
        n.append("SWI supplied but not analysed here; haemorrhage and microbleeds "
                 "are outside this probe's scope.")
    return n


def main():
    ap = argparse.ArgumentParser(description="Rank lesion-type hypotheses")
    for m in ("t1", "t2", "flair", "dwi", "adc", "swi"):
        ap.add_argument(f"--{m}", default=None)
    ap.add_argument("--mask", default=None, help="brain mask (strongly recommended)")
    ap.add_argument("--json", dest="json_path", default=None)
    args = ap.parse_args()

    supplied = {m: getattr(args, m) for m in ("t1", "t2", "flair", "dwi", "adc", "swi")
                if getattr(args, m)}
    if not supplied:
        print("ERROR: supply at least one modality", file=sys.stderr)
        sys.exit(2)

    vols, zooms, shape, aff = {}, None, None, None
    skipped = []
    for m, p in supplied.items():
        v, z, a, s = load_ras(p)
        if shape is None:
            shape, zooms, aff = s, z, a
        elif s != shape or not np.allclose(a, aff, atol=1e-3):
            # No registration is attempted here -- silently resampling would
            # invent cross-modal agreement that the data does not support.
            skipped.append(m)
            continue
        vols[m] = v

    if not vols:
        print("ERROR: no modality matched the reference grid", file=sys.stderr)
        sys.exit(2)

    cc = float(np.prod(zooms)) / 1000.0
    if args.mask:
        mv, _, _, ms = load_ras(args.mask)
        if ms != shape:
            print("ERROR: brain mask grid does not match images", file=sys.stderr)
            sys.exit(2)
        brain = mv > 0.5
        mask_src = args.mask
    else:
        # NumPy arrays do not have a scalar truth value.  Select the preferred
        # reference by key instead of using boolean ``or`` on an array.
        ref = vols["t1"] if "t1" in vols else next(iter(vols.values()))
        brain = crude_brain_mask(ref, zooms)
        mask_src = "crude internal estimate (supply --mask for better results)"

    mid_idx, head_dice = find_midsagittal(brain, zooms)
    feats, _ = analyse(vols, zooms, brain, cc, mid_idx)
    hyps = rank(feats, set(vols))
    notes = missing_modality_notes(set(supplied))
    if skipped:
        notes.append("Not analysed because their grid differs from the reference "
                     f"({', '.join(skipped)}): co-register first, or run the probe "
                     "separately per grid. No resampling was done.")
    if not args.mask:
        notes.append("No brain mask supplied; a crude internal estimate was used. "
                     "Run brain extraction first for reliable numbers.")

    result = dict(modalities_supplied=sorted(supplied), modalities_analysed=sorted(vols),
                  brain_mask=mask_src, brain_volume_cm3=round(float(brain.sum()) * cc, 1),
                  midsagittal_index=int(mid_idx), head_symmetry_dice=round(head_dice, 4),
                  features=feats, hypotheses=hyps, notes=notes, config=CFG)

    # ---- report ----------------------------------------------------------
    print("=== Lesion signature probe ===")
    print(f"Modalities analysed : {', '.join(sorted(vols))}"
          + (f"   (skipped: {', '.join(skipped)})" if skipped else ""))
    print(f"Brain mask          : {mask_src}")
    print(f"Brain volume        : {result['brain_volume_cm3']} cm3")
    print(f"Midline symmetry    : Dice {result['head_symmetry_dice']}")
    print()
    for k, v in feats.items():
        if isinstance(v, dict):
            print(f"{k}:")
            for kk, vv in v.items():
                print(f"    {kk:<20} {vv}")
        else:
            print(f"{k}: {v}")
    print()
    print("Ranked hypotheses")
    print("-" * 72)
    for i, h in enumerate(hyps, 1):
        flag = "" if h["in_scope"] else "   [OUT OF SCOPE / REFER]"
        print(f"{i}. {h['lesion_type']:<28} {h['confidence']}{flag}")
        for e in h["evidence"]:
            print(f"     - {e}")
    print("-" * 72)
    for n in notes:
        print(f"NOTE: {n}")
    print("\nThis probe narrows the field. It does not diagnose. Confirm the type "
          "with clinical context or visual review before segmenting.")

    if args.json_path:
        with open(args.json_path, "w") as fh:
            json.dump(result, fh, indent=2)
        print(f"\nJSON written: {args.json_path}")


if __name__ == "__main__":
    main()
