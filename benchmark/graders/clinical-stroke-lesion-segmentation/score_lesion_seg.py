#!/usr/bin/env python3
"""score_lesion_seg.py — grade a lesion-segmentation submission against a frozen EXPERT mask.

Unlike the brain-extraction / tissue graders (which score against a tool *consensus*), lesion
segmentation is graded against a single expert manual mask — automated lesion tools disagree too
much to form a trustworthy consensus, so the dataset's expert tracing IS the ground truth. Because
one subject gives no leave-one-out envelope, the pass/fail thresholds are FIXED per task in
rubric.json; the `threshold_basis` field there records where each number comes from.

Metrics:
  dice                overlap with the expert mask
  lesion_f1           lesion-WISE detection F1 (connected components; small lesions that tank Dice
                      still register as detected/missed) — precision/recall over lesion instances
  abs_volume_err_pct  |predicted - expert| volume, % of expert

Lesion counting is rubric-driven: `overlap_frac_for_match` is the fraction of a reference lesion a
prediction must cover to count as detected, and the optional `min_lesion_voxels` drops components
below that size from both maps before matching — a task whose reference carries many sub-detectable
specks sets it to the convention its thresholds were taken from. Absent, nothing is dropped.

`copy_suspect_dice` fails a submission whose overlap is too perfect to
be a segmentation — for tasks whose dataset ships the reference mask next to the images.

Pack (--pack DIR): rubric.json + reference/lesion_mask.nii.gz (expert mask, native grid).
Usage:  score_lesion_seg.py --pred agent_lesion.nii.gz --pack PACK_DIR [--json out.json]
Exit 0 when valid (verdict != invalid), 1 otherwise. Deps: numpy, scipy, nibabel.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, nibabel as nib
from scipy import ndimage as ndi

BIN_TOL = 1e-6
STRUCT = ndi.generate_binary_structure(3, 1)


def same_grid(a, b, tol=1e-3):
    return a.shape[:3] == b.shape[:3] and np.allclose(a.affine, b.affine, atol=tol)


def load_mask(path, ref_img):
    raw = nib.load(str(path)); img = nib.as_closest_canonical(raw)
    data = np.nan_to_num(np.asanyarray(img.dataobj).astype(np.float64))
    notes = []
    vals = np.unique(data)
    if vals.size > 2 or not np.isin(vals, [0, 1]).all():
        notes.append("not_binary")
    m = data > BIN_TOL
    if not same_grid(img, ref_img):
        notes.append(f"grid_mismatch{tuple(img.shape[:3])}")
        xfm = np.linalg.inv(img.affine) @ ref_img.affine
        m = ndi.affine_transform(m.astype(np.uint8), xfm[:3, :3], offset=xfm[:3, 3],
                                 output_shape=ref_img.shape[:3], order=0, mode="constant", cval=0) > 0
        notes.append("resampled_nn")
    return m, notes


def countable(labels, n, min_vox):
    """Component indices large enough to count as lesion instances."""
    if n == 0:
        return []
    if min_vox <= 1:
        return list(range(1, n + 1))
    sizes = np.bincount(labels.ravel(), minlength=n + 1)
    return [i for i in range(1, n + 1) if sizes[i] >= min_vox]


def lesion_wise_f1(pred, ref, min_overlap, min_vox=0):
    """Detection F1 over connected components. A reference lesion counts detected if a predicted
    component overlaps >= min_overlap of it; a predicted component is a false positive if it
    overlaps no reference lesion. Components smaller than min_vox are not counted on either side."""
    rl, nr_all = ndi.label(ref, STRUCT)
    pl, np_all = ndi.label(pred, STRUCT)
    ref_idx = countable(rl, nr_all, min_vox)
    pred_idx = countable(pl, np_all, min_vox)
    if not ref_idx and not pred_idx:
        return 1.0, 1.0, 1.0, 0, 0, 0
    tp = 0
    for i in ref_idx:
        comp = rl == i
        if (pred & comp).sum() >= min_overlap * comp.sum():
            tp += 1
    fn = len(ref_idx) - tp
    fp = 0
    for j in pred_idx:
        comp = pl == j
        if (ref & comp).sum() == 0:
            fp += 1
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-9)
    return f1, prec, rec, tp, fp, fn


def surface_metrics(pred, ref, zooms):
    sp = pred & ~ndi.binary_erosion(pred, STRUCT, border_value=1)
    sr = ref & ~ndi.binary_erosion(ref, STRUCT, border_value=1)
    if sp.sum() == 0 or sr.sum() == 0:
        return dict(assd_mm=np.nan, hd95_mm=np.nan)
    d1 = ndi.distance_transform_edt(~sr, sampling=zooms)[sp]
    d2 = ndi.distance_transform_edt(~sp, sampling=zooms)[sr]
    both = np.concatenate([d1, d2])
    return dict(assd_mm=float(both.mean()), hd95_mm=float(np.percentile(both, 95)))


def subscore(value, full, pass_, lower_better=False):
    if not np.isfinite(value):
        return 0.0
    if lower_better:
        return float(np.clip((pass_ - value) / max(pass_ - full, 1e-9), 0, 1))
    return float(np.clip((value - pass_) / max(full - pass_, 1e-9), 0, 1))


def subject_rubric(pack):
    """The rubric to grade against.

    `tau_mm`, `focal_max_cm3`, the consensus volumes and the grid all belong to one
    subject. A pack that holds a rubrics/ directory is graded per subject, and
    fetch_reference.py --subject selects that subject's rubric into reference/.

    There is deliberately no fallback for such a pack. Quietly grading one subject
    against another's calibration is the failure this split exists to prevent, and it
    would be invisible in the result: the run would simply apply the wrong boundary
    tolerance and the wrong focal cap. A missing selection is an error.
    """
    fetched = pack / "reference" / "rubric.json"
    if fetched.is_file():
        return fetched
    if (pack / "rubrics").is_dir():
        have = sorted(p.stem for p in (pack / "rubrics").glob("*.json"))
        raise SystemExit(
            f"ERROR: {pack.name} is graded per subject and no subject rubric has been "
            f"selected.\nRun: fetch_reference.py --task {pack.name} --subject <subject>\n"
            f"Subjects: {', '.join(have)}")
    return pack / "rubric.json"


def score(pred_path, pack_dir):
    pack = Path(pack_dir); rubric = json.load(open(subject_rubric(pack)))
    ref_p = pack / "reference" / "lesion_mask.nii.gz"
    if not ref_p.exists():
        raise SystemExit(f"ERROR: reference/lesion_mask.nii.gz not in {pack/'reference'}. "
                         "Fetch it with benchmark/harness/fetch_reference.py.")
    rimg = nib.as_closest_canonical(nib.load(str(ref_p)))
    ref = np.asanyarray(rimg.dataobj) > BIN_TOL
    # The rubric must belong to the reference it is grading. This task has no consensus
    # volume to compare, but each subject's scan has its own affine, so that is what is
    # checked: a rubric selected for another subject is refused rather than applied.
    want_aff = (rubric.get("grid") or {}).get("raw_affine")
    if want_aff is not None:
        have_aff = nib.load(str(ref_p)).affine
        if not np.allclose(np.asarray(want_aff, float), have_aff, atol=1e-3):
            raise SystemExit(
                "ERROR: this rubric does not describe this reference -- its grid affine "
                "does not match lesion_mask.nii.gz. The rubric and the reference are for "
                "different subjects.")

    zooms = np.asarray(rimg.header.get_zooms()[:3], float)
    vox_cm3 = float(np.prod(zooms) / 1000.0)

    pred, notes = load_mask(pred_path, rimg)
    th = rubric["metric_thresholds"]
    m = {}
    m["dice"] = 2 * (pred & ref).sum() / max(pred.sum() + ref.sum(), 1)
    f1, prec, rec, tp, fp, fn = lesion_wise_f1(pred, ref, rubric.get("overlap_frac_for_match", 0.1),
                                               rubric.get("min_lesion_voxels", 0))
    m["lesion_f1"] = f1; m["lesion_precision"] = prec; m["lesion_recall"] = rec
    m["tp"], m["fp"], m["fn"] = tp, fp, fn
    m["pred_vol_cm3"] = float(pred.sum() * vox_cm3); m["ref_vol_cm3"] = float(ref.sum() * vox_cm3)
    m["abs_volume_err_pct"] = 100 * abs(pred.sum() - ref.sum()) / max(ref.sum(), 1)
    m.update(surface_metrics(pred, ref, zooms))

    gates = {}
    gates["binary"] = "not_binary" not in notes
    gates["native_grid"] = not any(n.startswith("grid_mismatch") for n in notes)
    gates["nonempty"] = bool(pred.sum() > 0)
    lo, hi = rubric.get("plausible_vol_cm3", [0.1, 500])
    gates["volume_plausible"] = bool(lo <= m["pred_vol_cm3"] <= hi)
    # Some datasets publish the reference mask beside the images the task hands out, so a
    # submission can be a download rather than a segmentation. The threshold sits far above
    # what segmenting the image can reach -- the best published method on this reference is
    # nowhere near it -- so overlap this exact is the reference itself, and the submission is
    # not a valid answer to the task.
    copy_dice = rubric.get("copy_suspect_dice")
    if copy_dice is not None:
        gates["not_reference_copy"] = bool(m["dice"] < copy_dice)
    failures = [k for k, ok in gates.items() if not ok]

    weights = rubric["weights"]
    subs = {
        "dice": subscore(m["dice"], th["dice"]["full"], th["dice"]["pass"]),
        "lesion_f1": subscore(m["lesion_f1"], th["lesion_f1"]["full"], th["lesion_f1"]["pass"]),
        "abs_volume_err_pct": subscore(m["abs_volume_err_pct"], th["abs_volume_err_pct"]["full"],
                                       th["abs_volume_err_pct"]["pass"], lower_better=True),
    }
    quality = 100 * sum(weights[k] * subs[k] for k in weights)
    within = (m["dice"] >= th["dice"]["full"] and m["lesion_f1"] >= th["lesion_f1"]["full"]
              and m["abs_volume_err_pct"] <= th["abs_volume_err_pct"]["full"])
    vt = rubric["verdict_thresholds"]
    if failures:
        verdict, quality = "invalid", 0.0
    elif within:
        verdict = "within_reference_variability"
    elif quality >= vt["acceptable"]:
        verdict = "acceptable"
    elif quality >= vt["marginal"]:
        verdict = "marginal"
    else:
        verdict = "unacceptable"

    result = {"verdict": verdict, "quality": round(quality, 2), "gate_failures": failures,
              "load_notes": notes, "subscores": {k: round(v, 3) for k, v in subs.items()},
              "metrics": {k: round(float(v), 4) for k, v in m.items()}}

    if copy_dice is not None:
        result["suspected_reference_copy"] = bool(m["dice"] >= copy_dice)

    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade a lesion segmentation against the frozen expert mask.")
    ap.add_argument("--pred", required=True, help="agent lesion mask (NIfTI, binary)")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    r = score(a.pred, a.pack)
    print(json.dumps(r, indent=2))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=2)
    return 0 if not r["gate_failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
