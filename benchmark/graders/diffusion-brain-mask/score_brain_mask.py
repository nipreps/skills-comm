#!/usr/bin/env python3
"""score_brain_mask.py — grade a brain-extraction submission for the
`structural-brain-extraction` benchmark task.

This is the GRADER-side scorer, not an agent-facing skill: it decides whether a
produced brain mask is competent, against a *frozen reference pack* that was
calibrated once from a panel of tools (see PROVENANCE.md).

Why not a single Dice-vs-one-mask check: every skull-stripper draws a slightly
different boundary, and they disagree in a few predictable places. So the pack
carries a STAPLE consensus of a tool panel split into three zones —

    core (2)        every panel tool includes it  -> must be kept  (scored)
    margin (1)      the tools legitimately disagree   -> free         (never scored)
    background (0)  no panel tool includes it      -> must be out   (scored)

and scores only the two unambiguous zones. Every threshold — the surface
tolerance tau, the per-metric pass/fail envelope, the gate caps — is read from
rubric.json, which was calibrated by leave-one-tool-out. Nothing here is
hand-picked, and scoring a submission never re-calibrates.

Pack layout (--pack DIR):
    rubric.json                        calibrated numbers (tau, envelope, weights, gates)
    reference/consensus_mask.nii.gz    binary consensus (STAPLE p>=0.5), native T1w grid
    reference/consensus_zones.nii.gz   0=background, 1=margin, 2=core

Usage:
    score_brain_mask.py --mask agent_mask.nii.gz --pack PACK_DIR \
        [--stripped agent_brain.nii.gz] [--json out.json]

Exit code is 0 when the submission is valid (not gate-failed), 1 otherwise, so
the grader can be used as a pass/fail check in a harness.

Dependencies: numpy, scipy, nibabel.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import nibabel as nib
from scipy import ndimage as ndi

BIN_TOL = 1e-6
STRUCT = ndi.generate_binary_structure(3, 1)
# How deep a shave a region must survive to count as a solid piece of anatomy rather
# than a boundary offset, floored at one voxel of the grid in use.
# See _largest_solid_component_cm3.
SOLID_SHAVE_MM = 1.5
# metrics where a smaller value is better (used by the envelope mapping)
LOWER_BETTER = {"assd_mm", "hd95_mm", "core_miss_cm3", "focal_core_miss_cm3",
                "focal_bg_incl_cm3", "bg_fp_cm3", "bg_fp_frac_of_ref", "abs_volume_err_pct"}


# --------------------------------------------------------------------------- #
# Geometry / loading
# --------------------------------------------------------------------------- #
def same_grid(a, b, tol=1e-3):
    return a.shape[:3] == b.shape[:3] and np.allclose(a.affine, b.affine, atol=tol)


def is_header_only_deoblique(raw_img, ref_shape, ref_affine, tol=1e-3):
    """True when a submission shares the reference's sampling lattice but had its
    obliquity stripped from the header only, which some skull-strippers do. The
    data is still index-aligned to the input, so it must be read on the native
    grid rather than resampled by the (now-wrong) affine."""
    if tuple(raw_img.shape[:3]) != tuple(ref_shape[:3]):
        return False
    a = raw_img.affine
    za = np.linalg.norm(a[:3, :3], axis=0)
    zb = np.linalg.norm(np.asarray(ref_affine)[:3, :3], axis=0)
    same_zooms = np.allclose(za, zb, atol=tol)
    same_origin = np.allclose(a[:3, 3], np.asarray(ref_affine)[:3, 3], atol=tol)
    differs = not np.allclose(a, ref_affine, atol=tol)
    return bool(same_zooms and same_origin and differs)


def resample_nn(mask, affine, ref_img):
    xfm = np.linalg.inv(affine) @ ref_img.affine
    out = ndi.affine_transform(mask.astype(np.uint8), xfm[:3, :3], offset=xfm[:3, 3],
                               output_shape=ref_img.shape[:3], order=0, mode="constant", cval=0)
    return out.astype(bool)


def load_mask(path, ref_img, raw_shape, raw_affine):
    """Load a submission as a boolean mask on the reference grid. Returns (mask, notes)."""
    raw = nib.load(str(path))
    img = nib.as_closest_canonical(raw)
    data = np.asanyarray(img.dataobj).astype(np.float64)
    notes = []
    if np.isnan(data).any():
        notes.append("contains_nan")
        data = np.nan_to_num(data)
    vals = np.unique(data)
    if vals.size > 2:
        notes.append(f"not_binary({vals.size}_values)")
    elif not np.isin(vals, [0, 1]).all():
        notes.append("values_not_0_1")
    mask = data > BIN_TOL
    if not same_grid(img, ref_img):
        if raw_affine is not None and is_header_only_deoblique(raw, raw_shape, raw_affine):
            notes.append("deobliqued_header_native_grid")
        else:
            notes.append(f"grid_mismatch{tuple(img.shape[:3])}")
            mask = resample_nn(mask, img.affine, ref_img)
            notes.append("resampled_nn")
    return mask, notes


# --------------------------------------------------------------------------- #
# Metrics and gates (formulas match the calibration recorded in PROVENANCE.md)
# --------------------------------------------------------------------------- #
def _surface(m):
    return m & ~ndi.binary_erosion(m, STRUCT, border_value=1)


def _largest_component_cm3(binary, vox_cm3):
    lab, n = ndi.label(binary, STRUCT)
    return float(np.bincount(lab.ravel())[1:].max() * vox_cm3) if n else 0.0


def _largest_solid_component_cm3(binary, vox_cm3, zooms):
    """Largest connected component that survives having SOLID_SHAVE_MM shaved off it.

    Volume alone cannot tell a boundary convention from missing anatomy. A whole mask
    offset inward by a millimetre and a lobe cut off can be the same number of cm3 in one
    connected region: on these references a uniform 2 mm trim registers 3 to 232 cm3 of
    "focal" loss while removing nothing a radiologist would name, and on the inclusion
    side a 1 mm rim over half the cortical surface registers 59 to 116 cm3.

    Shaving first separates them. A layer survives only if it is thicker than twice the
    shave, so the shave is a distance rather than a voxel count: the quantity in question
    is anatomical thickness and the grids here span 0.63 to 2.5 mm. A one-voxel erosion
    asks for three voxels of thickness, 1.9 mm at 7T, which a two- to three-voxel dura
    rind clears -- that is how one slipped through and pushed a cap from 8 to 53 cm3. At
    SOLID_SHAVE_MM a structure has to exceed 3 mm, near cortical thickness, while dura
    and CSF rinds at 1 to 2 mm do not.

    The floor at one voxel matters on a coarse grid: a 1.5 mm shave removes nothing at
    all on the 2.5 mm diffusion grid, since no voxel there is within 1.5 mm of the
    outside, and the measure would quietly fall back to a raw component volume. A grid
    cannot resolve a layer thinner than its own voxel, so one voxel is the least that
    can be asked of it.

    Boundary disagreement is not unscored -- tau, NSD and HD95 price it, total core loss
    feeds core_recall and the catastrophic gate, and total background inclusion feeds
    bg_fp. These two gates are for the other failure: a piece of anatomy that is simply
    gone, or a piece of skull that is simply included.
    """
    if binary.any():
        shave = max(SOLID_SHAVE_MM, float(np.max(zooms)))
        binary = ndi.distance_transform_edt(binary, sampling=zooms) > shave
    return _largest_component_cm3(binary, vox_cm3)


def surface_metrics(cand, ref_binary, zooms, tau_mm):
    sc, sr = _surface(cand), _surface(ref_binary)
    if sc.sum() == 0 or sr.sum() == 0:
        return dict(assd_mm=np.nan, hd95_mm=np.nan, nsd=np.nan)
    d_cr = ndi.distance_transform_edt(~sr, sampling=zooms)[sc]
    d_rc = ndi.distance_transform_edt(~sc, sampling=zooms)[sr]
    both = np.concatenate([d_cr, d_rc])
    nsd = ((d_cr <= tau_mm).sum() + (d_rc <= tau_mm).sum()) / both.size
    return dict(assd_mm=float(both.mean()), hd95_mm=float(np.percentile(both, 95)), nsd=float(nsd))


def evaluate(mask, zones, ref_binary, zooms, tau_mm):
    vox_cm3 = float(np.prod(zooms) / 1000.0)
    core, margin, background = zones == 2, zones == 1, zones == 0
    m = {}
    m["volume_cm3"] = float(mask.sum() * vox_cm3)
    m["volume_err_pct"] = 100 * (mask.sum() - ref_binary.sum()) / max(ref_binary.sum(), 1)
    m["abs_volume_err_pct"] = abs(m["volume_err_pct"])
    m["dice"] = 2 * (mask & ref_binary).sum() / max(mask.sum() + ref_binary.sum(), 1)
    m["core_recall"] = (mask & core).sum() / max(core.sum(), 1)
    m["core_miss_cm3"] = (core & ~mask).sum() * vox_cm3
    m["focal_core_miss_cm3"] = _largest_solid_component_cm3(core & ~mask, vox_cm3, zooms)
    m["bg_fp_cm3"] = (mask & background).sum() * vox_cm3
    m["focal_bg_incl_cm3"] = _largest_solid_component_cm3(mask & background, vox_cm3, zooms)
    m["bg_fp_frac_of_ref"] = (mask & background).sum() / max(ref_binary.sum(), 1)
    m["margin_inclusion"] = (mask & margin).sum() / max(margin.sum(), 1)
    m.update(surface_metrics(mask, ref_binary, zooms, tau_mm))
    return m


def validity_gates(mask, notes, zones, rubric, vox_cm3, zooms, stripped_mask=None,
                   dura_envelope=None, lesion_mask=None):
    core = zones == 2
    g = {}
    g["binary"] = not any(n.startswith("not_binary") or n == "values_not_0_1" for n in notes)
    g["native_grid"] = not any(n.startswith("grid_mismatch") for n in notes)
    g["nonempty"] = bool(mask.sum() > 0)
    lo, hi = rubric["plausible_volume_cm3"]
    g["volume_plausible"] = bool(lo <= mask.sum() * vox_cm3 <= hi)
    lab, n = ndi.label(mask, STRUCT)
    sizes = np.bincount(lab.ravel())[1:] if n else np.array([0])
    g["single_component"] = bool(n > 0 and sizes.max() / sizes.sum() > 0.98)
    filled = ndi.binary_fill_holes(mask)
    g["no_internal_holes"] = bool((filled.sum() - mask.sum()) / max(mask.sum(), 1) < 0.02)
    # The floor was computed from the rubric and then discarded, the gate testing a
    # hardcoded 0.90 instead. No rubric sets consensus.max_core_loss today, so nothing was
    # misgraded, but a task that set it would have been silently overridden.
    min_core_kept = 1 - rubric.get("consensus", {}).get("max_core_loss", 0.10)
    g["no_catastrophic_core_loss"] = bool(
        (mask & core).sum() / max(core.sum(), 1) > min_core_kept)
    g["no_focal_core_loss"] = bool(
        _largest_solid_component_cm3(core & ~mask, vox_cm3, zooms)
        <= rubric["focal_max_cm3"])
    g["no_focal_bg_inclusion"] = bool(
        _largest_solid_component_cm3(mask & (zones == 0), vox_cm3, zooms)
        <= rubric.get("focal_bg_max_cm3", 40.0))
    if stripped_mask is not None:
        g["stripped_matches_mask"] = bool((stripped_mask == mask).mean() > 0.99)
    # Dura gate (activates only for packs that ship a dura envelope, e.g. the 7T "no-dura" task):
    # a submission must not extend past the pial envelope into the dura/skull. One-sided — keeping
    # LESS than the envelope is not penalised here (the core/focal gates guard against cutting brain).
    if dura_envelope is not None:
        over_env_cm3 = float((mask & ~dura_envelope).sum() * vox_cm3)
        g["no_dura_inclusion"] = bool(over_env_cm3 <= rubric.get("dura_max_cm3", 30.0))
    # Lesion-retention gate (activates only for packs shipping a lesion mask, e.g. the stroke task):
    # a pathological cavity (chronic infarct, resection) is brain tissue that must stay in the mask;
    # intensity strippers that treat the CSF-like lesion as background carve it out and fail here.
    if lesion_mask is not None and lesion_mask.sum() > 0:
        retained = float((mask & lesion_mask).sum() / lesion_mask.sum())
        g["lesion_retained"] = bool(retained >= rubric.get("lesion_retained_min", 0.85))
    return g


def subscore(value, env, key, slack):
    if not np.isfinite(value):
        return 0.0
    good, worst = env["median"], env["worst"]
    if key in LOWER_BETTER:
        fail = worst + slack * max(worst - good, 1e-6)
        return float(np.clip((fail - value) / max(fail - good, 1e-9), 0, 1))
    fail = worst - slack * max(good - worst, 1e-6)
    return float(np.clip((value - fail) / max(good - fail, 1e-9), 0, 1))


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


def score(mask_path, pack_dir, stripped_path=None):
    """Grade one submission. Returns a dict with verdict, quality, metrics, gates."""
    pack = Path(pack_dir)
    rubric = json.load(open(subject_rubric(pack)))
    ref_dir = pack / "reference"
    missing = [f for f in ("consensus_mask.nii.gz", "consensus_zones.nii.gz")
               if not (ref_dir / f).exists()]
    if missing:
        raise SystemExit(
            f"ERROR: reference file(s) {missing} not found in {ref_dir}.\n"
            "Fetch the reference first (see reference/README.md):\n"
            "  python benchmark/harness/fetch_reference.py --task <task-id>")
    ref_img = nib.as_closest_canonical(nib.load(str(pack / "reference" / "consensus_mask.nii.gz")))
    zones = np.asanyarray(nib.as_closest_canonical(
        nib.load(str(pack / "reference" / "consensus_zones.nii.gz"))).dataobj).astype(np.int16)
    ref_binary = np.asanyarray(ref_img.dataobj) > BIN_TOL
    zooms = np.asarray(ref_img.header.get_zooms()[:3], float)
    vox_cm3 = float(np.prod(zooms) / 1000.0)

    # The rubric must belong to the reference it is grading, and the test has to be
    # something that actually separates subjects. Neither grid shape nor consensus volume
    # does: subjects of one task share a matrix, and the closest pair of core volumes is
    # 0.08% apart in the stroke task and under 1% in three others, so a volume comparison
    # loose enough not to false-positive is too loose to catch anything. Measured on the
    # nine per-subject tasks, every subject's scan affine is unique, so that is the test.
    want_aff = (rubric.get("grid") or {}).get("raw_affine")
    if want_aff is not None:
        have_aff = nib.load(str(pack / "reference" / "consensus_mask.nii.gz")).affine
        if not np.allclose(np.asarray(want_aff, float), have_aff, atol=1e-3):
            raise SystemExit(
                "ERROR: this rubric does not describe this reference -- its grid affine "
                "does not match consensus_mask.nii.gz. The rubric and the reference are "
                "for different subjects.")

    # A volume far from what the rubric states means the reference changed under the
    # rubric even though the subject matches; loose on purpose, so it flags a rebuild
    # rather than a neighbouring subject.
    stated_core = (rubric.get("consensus") or {}).get("core_cm3")
    if stated_core:
        measured_core = float((zones == 2).sum() * vox_cm3)
        if abs(measured_core - stated_core) > 0.10 * stated_core:
            raise SystemExit(
                f"ERROR: this rubric states a core of {stated_core:.2f} cm3 but the loaded "
                f"consensus_zones.nii.gz has {measured_core:.2f} cm3 -- more than 10% "
                "apart. The reference has changed since the rubric was calibrated.")

    raw_shape = rubric["grid"].get("raw_shape")
    raw_affine = rubric["grid"].get("raw_affine")

    mask, notes = load_mask(mask_path, ref_img, raw_shape, raw_affine)
    stripped_mask = None
    if stripped_path:
        stripped_mask, _ = load_mask(stripped_path, ref_img, raw_shape, raw_affine)

    # Optional dura envelope (present only for the "no-dura" task); must share the reference grid.
    dura_envelope = None
    env_path = pack / "reference" / "dura_envelope.nii.gz"
    if env_path.exists():
        env_img = nib.as_closest_canonical(nib.load(str(env_path)))
        if not same_grid(env_img, ref_img):
            raise SystemExit(f"ERROR: dura_envelope grid {env_img.shape[:3]} does not match the "
                             f"consensus reference grid {ref_img.shape[:3]}.")
        dura_envelope = np.asanyarray(env_img.dataobj) > BIN_TOL

    # Optional expert lesion mask (present only for the pathology/lesion tasks); shares the ref grid.
    lesion_mask = None
    les_path = pack / "reference" / "lesion_mask.nii.gz"
    if les_path.exists():
        les_img = nib.as_closest_canonical(nib.load(str(les_path)))
        if not same_grid(les_img, ref_img):
            raise SystemExit(f"ERROR: lesion_mask grid {les_img.shape[:3]} does not match the "
                             f"consensus reference grid {ref_img.shape[:3]}.")
        lesion_mask = np.asanyarray(les_img.dataobj) > BIN_TOL

    gates = validity_gates(mask, notes, zones, rubric, vox_cm3, zooms, stripped_mask,
                           dura_envelope, lesion_mask)
    metrics = evaluate(mask, zones, ref_binary, zooms, rubric["tau_mm"])
    if dura_envelope is not None:
        metrics["dura_over_env_cm3"] = float((mask & ~dura_envelope).sum() * vox_cm3)
    if lesion_mask is not None and lesion_mask.sum() > 0:
        metrics["lesion_retained_frac"] = float((mask & lesion_mask).sum() / lesion_mask.sum())

    failures = [k for k, ok in gates.items() if not ok]
    weights = rubric["weights"]
    subs = {k: subscore(metrics[k], rubric["envelope"][k], k, rubric["slack"]) for k in weights}
    quality = 100 * sum(weights[k] * subs[k] for k in subs)

    within = all((metrics[k] <= rubric["envelope"][k]["worst"]) if k in LOWER_BETTER
                 else (metrics[k] >= rubric["envelope"][k]["worst"]) for k in weights)
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

    return {"verdict": verdict, "quality": round(quality, 2),
            "gate_failures": failures, "load_notes": notes,
            "metrics": {k: round(float(v), 4) for k, v in metrics.items()},
            "subscores": {k: round(v, 4) for k, v in subs.items()}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade a brain-extraction submission against the frozen pack.")
    ap.add_argument("--mask", required=True, help="agent brain mask (NIfTI)")
    ap.add_argument("--pack", required=True, help="grader pack directory (holds rubric.json + reference/)")
    ap.add_argument("--stripped", help="optional agent skull-stripped image, for the mask/image consistency gate")
    ap.add_argument("--json", help="write the full result to this path")
    args = ap.parse_args(argv)

    result = score(args.mask, args.pack, args.stripped)
    print(json.dumps(result, indent=2))
    if args.json:
        json.dump(result, open(args.json, "w"), indent=2)
    return 0 if not result["gate_failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
