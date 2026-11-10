#!/usr/bin/env python3
"""score_tissue_seg.py — grade a multi-class brain parcellation submission against a frozen
consensus pack (STAPLE-style majority vote of the panel's segmentations, split into per-class
unanimous-core / majority-boundary zones). Sibling of the binary score_brain_mask.py.

Reference pack (--pack DIR):
    rubric.json                          calibrated per-class envelope, tau, weights, gate caps
    reference/consensus_seg.nii.gz       fused label map (0..6)
    reference/consensus_agreement.nii.gz per-voxel #tools backing the label (3=unanimous core)

Labels: 0=background 1=GM 2=basal_ganglia 3=WM 4=ventricles 5=cerebellum 6=brainstem.

Usage:  score_tissue_seg.py --seg agent_dseg.nii.gz --pack PACK_DIR [--json out.json]
Exit 0 when valid (verdict != invalid), 1 otherwise.
Deps: numpy, scipy, nibabel.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, nibabel as nib
from scipy import ndimage as ndi

STRUCT = ndi.generate_binary_structure(3, 1)
LABELS = {1: "GM", 2: "basal_ganglia", 3: "WM", 4: "ventricles", 5: "cerebellum", 6: "brainstem"}
CLASSES = list(LABELS)


def same_grid(a, b, tol=1e-3):
    return a.shape[:3] == b.shape[:3] and np.allclose(a.affine, b.affine, atol=tol)


def _surface(m):
    return m & ~ndi.binary_erosion(m, STRUCT, border_value=1)


def surface_nsd(cand, ref, zooms, tau_mm):
    sc, sr = _surface(cand), _surface(ref)
    if sc.sum() == 0 or sr.sum() == 0:
        return np.nan
    d_cr = ndi.distance_transform_edt(~sr, sampling=zooms)[sc]
    d_rc = ndi.distance_transform_edt(~sc, sampling=zooms)[sr]
    return float(((d_cr <= tau_mm).sum() + (d_rc <= tau_mm).sum()) / (d_cr.size + d_rc.size))


def per_class_metrics(seg, consensus, agreement, zooms, tau):
    """dice / nsd / core_recall / volume for each labelled class."""
    vox_cm3 = float(np.prod(zooms) / 1000.0)
    out = {}
    for k in CLASSES:
        A, C = seg == k, consensus == k
        core = C & (agreement == 3)
        inter = (A & C).sum()
        out[k] = {
            "dice": 2 * inter / max(A.sum() + C.sum(), 1),
            "nsd": surface_nsd(A, C, zooms, tau.get(str(k), tau.get(k, 1.0))),
            "core_recall": (A & core).sum() / max(core.sum(), 1),
            "volume_cm3": float(A.sum() * vox_cm3),
            "ref_volume_cm3": float(C.sum() * vox_cm3),
        }
    return out


def resample_labels_nn(seg, affine, ref_img):
    """Nearest-neighbour resample an integer label map onto the reference grid (order=0
    preserves labels). Used when a submission is not in native space, so it can still be
    scored — the native_grid gate records that it was off-grid."""
    xfm = np.linalg.inv(affine) @ ref_img.affine
    out = ndi.affine_transform(seg.astype(np.int16), xfm[:3, :3], offset=xfm[:3, 3],
                               output_shape=ref_img.shape[:3], order=0, mode="constant", cval=0)
    return out.astype(np.int16)


def load_seg(path, ref_img):
    raw = nib.load(str(path))
    img = nib.as_closest_canonical(raw)
    data = np.asanyarray(img.dataobj)
    notes = []
    if np.isnan(np.asarray(data, float)).any():
        notes.append("contains_nan"); data = np.nan_to_num(data)
    seg = np.rint(np.asarray(data, float)).astype(np.int16)
    if not same_grid(img, ref_img):
        notes.append(f"grid_mismatch{tuple(img.shape[:3])}")
        seg = resample_labels_nn(seg, img.affine, ref_img)
        notes.append("resampled_nn")
    return seg, notes


def validity_gates(seg, notes, consensus, agreement, rubric):
    g = {}
    present = set(np.unique(seg)) - {0}
    g["valid_labels"] = present.issubset(set(CLASSES)) and len(present) >= len(CLASSES) - 1
    g["native_grid"] = not any(n.startswith("grid_mismatch") for n in notes)
    # A class "collapses" (missing/swapped) when it recovers meaningfully less of its unanimous
    # core than the WORST reference tool does. The floor is LOTO-calibrated per class: a small,
    # well-agreed structure (basal ganglia, WM: LOTO-worst ~0.91-0.94) gets a high floor; a fuzzy
    # one (GM: ~0.75) a lower one. Margin gives a submission some slack below the worst tool.
    env = rubric.get("envelope", {})
    margin = rubric.get("collapse_margin", 0.20)
    fixed = rubric.get("core_recall_floor", 0.5)  # fallback if no envelope
    ok = True
    for k in CLASSES:
        core = (consensus == k) & (agreement == 3)
        if not core.sum():
            continue
        worst = env.get(str(k), {}).get("core_recall", {}).get("worst")
        floor = max(0.25, worst - margin) if worst is not None else fixed
        if (seg == k)[core].mean() < floor:
            ok = False
    g["no_class_collapse"] = ok
    return g


def subscore(value, env, lower_better=False, slack=1.5):
    if not np.isfinite(value):
        return 0.0
    good, worst = env["median"], env["worst"]
    if lower_better:
        fail = worst + slack * max(worst - good, 1e-6)
        return float(np.clip((fail - value) / max(fail - good, 1e-9), 0, 1))
    fail = worst - slack * max(good - worst, 1e-6)
    return float(np.clip((value - fail) / max(good - fail, 1e-9), 0, 1))


def subject_rubric(pack):
    """The rubric to grade against.

    A pack that holds a rubrics/ directory is graded per subject, and
    fetch_reference.py --subject selects that subject's rubric into reference/. There is
    deliberately no fallback for such a pack: grading one subject against another's
    calibration would produce a plausible wrong number rather than an error.
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


def score(seg_path, pack_dir):
    pack = Path(pack_dir)
    rubric = json.load(open(subject_rubric(pack)))

    # The rubric must belong to the reference beside it. Subjects of one task share a
    # matrix and their class volumes sit within a few percent, so neither identifies a
    # subject; the scan affine does, and is unique across every subject of every task.
    want_aff = (rubric.get("grid") or {}).get("raw_affine")
    if want_aff is not None:
        ref_p = pack / "reference" / "consensus_seg.nii.gz"
        if ref_p.is_file():
            have_aff = nib.load(str(ref_p)).affine
            if not np.allclose(np.asarray(want_aff, float), have_aff, atol=1e-3):
                raise SystemExit(
                    "ERROR: this rubric does not describe this reference -- its grid "
                    "affine does not match consensus_seg.nii.gz. The rubric and the "
                    "reference are for different subjects.")
    refd = pack / "reference"
    for f in ("consensus_seg.nii.gz", "consensus_agreement.nii.gz"):
        if not (refd / f).exists():
            raise SystemExit(f"ERROR: {f} not found in {refd}. Fetch the reference with "
                             "(see reference/README.md).")
    cimg = nib.as_closest_canonical(nib.load(str(refd / "consensus_seg.nii.gz")))
    consensus = np.asanyarray(cimg.dataobj).astype(np.int16)
    agreement = np.asanyarray(nib.as_closest_canonical(
        nib.load(str(refd / "consensus_agreement.nii.gz"))).dataobj).astype(np.uint8)
    zooms = np.asarray(cimg.header.get_zooms()[:3], float)

    seg, notes = load_seg(seg_path, cimg)
    gates = validity_gates(seg, notes, consensus, agreement, rubric)
    m = per_class_metrics(seg, consensus, agreement, zooms, rubric["tau_mm"])

    # per-class quality from the calibrated envelope; overall = mean of class qualities
    env, weights = rubric["envelope"], rubric["weights"]
    cls_q = {}
    for k in CLASSES:
        parts = {"dice": subscore(m[k]["dice"], env[str(k)]["dice"], slack=rubric["slack"]),
                 "nsd": subscore(m[k]["nsd"], env[str(k)]["nsd"], slack=rubric["slack"]),
                 "core_recall": subscore(m[k]["core_recall"], env[str(k)]["core_recall"], slack=rubric["slack"])}
        cls_q[k] = 100 * sum(weights[p] * parts[p] for p in weights)
    quality = float(np.mean(list(cls_q.values())))

    within = all(m[k]["dice"] >= env[str(k)]["dice"]["worst"] for k in CLASSES)
    vt = rubric["verdict_thresholds"]
    failures = [k for k, ok in gates.items() if not ok]
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

    return {"verdict": verdict, "quality": round(quality, 2), "gate_failures": failures,
            "load_notes": notes,
            "per_class": {LABELS[k]: {"dice": round(m[k]["dice"], 4), "nsd": round(m[k]["nsd"], 4),
                                      "core_recall": round(m[k]["core_recall"], 4),
                                      "quality": round(cls_q[k], 1)} for k in CLASSES}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade a multi-class parcellation against the frozen pack.")
    ap.add_argument("--seg", required=True, help="agent label map (NIfTI, labels 1..6)")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    r = score(a.seg, a.pack)
    print(json.dumps(r, indent=2))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=2)
    return 0 if not r["gate_failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
