#!/usr/bin/env python3
"""score_registration.py — grade a T1w-to-MNI registration for the
`structural-mni-registration` benchmark task.

This is the GRADER-side scorer, not an agent-facing skill.

Why not image similarity alone: correlation between a warped T1w and the template is dominated
by gross head position and is nearly saturated once any affine has been applied, so it barely
separates an affine from a nonlinear warp. The sensitive measurement is **label propagation** —
carry the subject's own tissue segmentation through the same transform and ask where the tissue
landed. That is the standard way registration is evaluated, and it is tool-agnostic: every
registration package can apply its own transform to a second image.

The reference is not another tool's warp. It is the **template's own tissue priors**, which state
where CSF, grey matter and white matter belong in MNI space independently of any registration
software. A population prior is not a per-subject truth, so the thresholds are not absolute:
`rubric.json` carries the envelope actually achieved by a panel of independent nonlinear
registrations on this subject (see PROVENANCE.md), and scoring is relative to that.

Pack layout (--pack DIR):
    rubric.json                          calibrated numbers (envelope, weights, gates, grid)
    reference/template_T1w.nii.gz        MNI152NLin2009cAsym T1w
    reference/template_brain_mask.nii.gz
    reference/template_probseg_CSF.nii.gz, _GM.nii.gz, _WM.nii.gz

Usage:
    score_registration.py --warped agent_T1w_in_mni.nii.gz --dseg agent_dseg_in_mni.nii.gz \
        --pack PACK_DIR [--json out.json]

Exit 0 when valid (verdict != invalid), 1 otherwise. Deps: numpy, scipy, nibabel.
"""
import argparse
import json
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage as ndi

STRUCT = ndi.generate_binary_structure(3, 1)

# Two kinds of registration task share this scorer, chosen by rubric["mode"]:
#
#   label_propagation  (default) -- the subject's tissue segmentation is carried through the
#       agent's transform and compared with the template's tissue priors. Sensitive to how well
#       a same-modality warp aligns anatomy.
#   cross_modal -- for BOLD-to-MNI, where there is no usable tissue segmentation in the moving
#       image's space and its contrast differs from the template. Scores where the brain landed
#       (mask overlap, placement) plus normalised mutual information, which is contrast-agnostic.
MODE_LABEL, MODE_CROSS = "label_propagation", "cross_modal"
# Label convention of the segmentation the task hands the agent. Verified from the data rather
# than assumed: on the subject's T1w the mean intensity per label is WM > GM > CSF, which fixes
# the mapping as 1=GM, 2=WM, 3=CSF. rubric.json carries it so the scorer never guesses.
TISSUES = {"GM": 1, "WM": 2, "CSF": 3}
LOWER_BETTER = {"abs_brain_volume_err_pct", "com_offset_mm"}


def same_grid(a, b, tol=1e-3):
    return a.shape[:3] == b.shape[:3] and np.allclose(a.affine, b.affine, atol=tol)


def load_on_grid(path, ref_img, label=False):
    """Load a submission on the reference grid.

    Returns (data, notes, nonfinite). Some resamplers write NaN outside the
    field of view rather than zero, which is a convention rather than a defect, so non-finite
    values are zeroed here and judged later against the brain mask: NaN in the background is
    fine, NaN inside the brain is not.
    """
    raw = nib.load(str(path))
    img = nib.as_closest_canonical(raw)
    data = np.asanyarray(img.dataobj).astype(np.float64)
    notes = []
    nonfinite = ~np.isfinite(data)
    if nonfinite.any():
        notes.append(f"non_finite_zeroed({int(nonfinite.sum())})")
        data = np.nan_to_num(data)
    if not same_grid(img, ref_img):
        notes.append(f"grid_mismatch{tuple(img.shape[:3])}")
        order = 0 if label else 1
        xfm = np.linalg.inv(img.affine) @ ref_img.affine
        data = ndi.affine_transform(data, xfm[:3, :3], offset=xfm[:3, 3],
                                    output_shape=ref_img.shape[:3], order=order,
                                    mode="constant", cval=0)
        nonfinite = ndi.affine_transform(nonfinite.astype(np.uint8), xfm[:3, :3],
                                         offset=xfm[:3, 3], output_shape=ref_img.shape[:3],
                                         order=0, mode="constant", cval=0) > 0
        notes.append("resampled")
    return data, notes, nonfinite


def dice(a, b):
    s = a.sum() + b.sum()
    return float(2 * (a & b).sum() / s) if s else 0.0


def normalised_mutual_information(a, b, bins=64):
    """NMI in [0, 1]. Cross-modal similarity: BOLD and a T1w template share structure but not
    an intensity relationship, so correlation is the wrong tool and MI is the standard one."""
    a = a.astype(np.float64); b = b.astype(np.float64)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    hist, _, _ = np.histogram2d(a.ravel(), b.ravel(), bins=bins)
    pxy = hist / hist.sum()
    px = pxy.sum(axis=1); py = pxy.sum(axis=0)
    nz = pxy > 0
    hxy = -(pxy[nz] * np.log(pxy[nz])).sum()
    hx = -(px[px > 0] * np.log(px[px > 0])).sum()
    hy = -(py[py > 0] * np.log(py[py > 0])).sum()
    return float(0.0 if hxy == 0 else (hx + hy - hxy) / max((hx + hy) / 2, 1e-12))


def edge_correlation(warped, target, brain, sigma=2.0):
    """Correlation of gradient magnitudes inside the brain, in [-1, 1].

    Boundary agreement rather than intensity agreement: a BOLD volume and a T1w template have
    unrelated intensities but their tissue boundaries coincide when the warp is right. This
    resolves misalignments that whole-brain mask overlap cannot see, because the outline of a
    brain-shaped object stays in roughly the right place even when its interior is displaced.
    """
    a = ndi.gaussian_gradient_magnitude(np.asarray(warped, np.float64), sigma=sigma)[brain]
    b = ndi.gaussian_gradient_magnitude(np.asarray(target, np.float64), sigma=sigma)[brain]
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def evaluate(warped, seg, ref, rubric):
    """ref: dict of template arrays. `seg` is the propagated segmentation in label_propagation
    mode, or the propagated brain mask in cross_modal mode. Returns the metric dictionary."""
    thr = rubric.get("prior_threshold", 0.5)
    mode = rubric.get("mode", MODE_LABEL)
    brain = ref["brain_mask"]
    vox_cm3 = float(np.prod(rubric["grid"]["zooms_mm"]) / 1000.0)
    m = {}

    if mode == MODE_LABEL:
        for name, code in rubric.get("tissue_labels", TISSUES).items():
            agent = seg == code
            target = ref[f"prior_{name}"] >= thr
            m[f"dice_{name.lower()}"] = dice(agent, target)
            m[f"vol_{name.lower()}_cm3"] = float(agent.sum() * vox_cm3)

    agent_brain = seg > 0
    m["brain_dice"] = dice(agent_brain, brain)
    m["brain_volume_cm3"] = float(agent_brain.sum() * vox_cm3)
    ref_brain_cm3 = float(brain.sum() * vox_cm3)
    m["abs_brain_volume_err_pct"] = 100 * abs(m["brain_volume_cm3"] - ref_brain_cm3) / ref_brain_cm3

    # image similarity inside the template brain, so a retained skull cannot dominate it
    a = warped[brain].astype(np.float64)
    b = ref["T1w"][brain].astype(np.float64)
    if mode == MODE_CROSS:
        m["nmi_in_brain"] = normalised_mutual_information(a, b)
        m["edge_corr"] = edge_correlation(warped, ref["T1w"], brain,
                                          sigma=rubric.get("edge_sigma", 2.0))
    elif a.std() > 0 and b.std() > 0:
        m["corr_in_brain"] = float(np.corrcoef(a, b)[0, 1])
    else:
        m["corr_in_brain"] = 0.0

    # how far the propagated brain sits from where it belongs; catches a warp that is
    # globally displaced while still overlapping
    if agent_brain.any():
        com_a = np.array(ndi.center_of_mass(agent_brain))
        com_b = np.array(ndi.center_of_mass(brain))
        zooms = np.asarray(rubric["grid"]["zooms_mm"], float)
        m["com_offset_mm"] = float(np.linalg.norm((com_a - com_b) * zooms))
    else:
        m["com_offset_mm"] = np.inf
    return m


def validity_gates(warped, seg, notes_w, notes_s, rubric, m, nonfinite_w, brain,
                   seg_raw=None):
    g = {}
    g["warped_on_template_grid"] = not any(n.startswith("grid_mismatch") for n in notes_w)
    g["dseg_on_template_grid"] = not any(n.startswith("grid_mismatch") for n in notes_s)
    # NaN outside the head is a resampler convention; NaN inside the brain is a broken warp
    g["warped_finite_in_brain"] = not bool((nonfinite_w & brain).any())
    present = set(np.unique(seg).astype(int).tolist()) - {0}
    if rubric.get("mode", MODE_LABEL) == MODE_LABEL:
        codes = set(rubric.get("tissue_labels", TISSUES).values())
        g["valid_labels"] = present.issubset(codes) and len(present) >= 2
    else:
        # Tested on the submitted values, not on np.rint(seg): rounding maps anything in [0, 1]
        # onto {0, 1}, so a probability map would pass silently while a {0, 255} mask -- which
        # several tools write -- would fail. A mask is binary when it holds one non-zero value,
        # whatever that value is; `seg > 0` is what the metrics use downstream.
        raw = seg if seg_raw is None else seg_raw
        nz = np.unique(np.round(np.asarray(raw, np.float64)[np.asarray(raw) != 0], 6))
        g["binary_mask"] = nz.size <= 1
    g["nonempty"] = bool((seg > 0).any())
    lo, hi = rubric["plausible_brain_volume_cm3"]
    g["brain_volume_plausible"] = bool(lo <= m["brain_volume_cm3"] <= hi)
    g["brain_in_place"] = bool(m["com_offset_mm"] <= rubric["max_com_offset_mm"])
    return g


def subscore(value, env, key, slack):
    """Full marks at the median independent nonlinear registration, zero credit at `floor`.

    `floor` is the median of the affine-only arms, so the scale reads directly: 0 means the
    submission did no better than a 12-DOF affine, 100 means it matched a typical nonlinear
    registration. Anchoring on the affine rather than on a slack multiple of the panel spread
    matters here because the panel tools agree very closely (WM Dice within 0.015 of each
    other) — a slack-based floor would sit inside that spread and make the score brittle.
    """
    lo_better = key in LOWER_BETTER
    full = env["median"]
    zero = env.get("floor")
    if zero is None:                      # no affine arm for this metric: fall back to slack
        worst = env["worst"]
        zero = (worst + slack * abs(worst - full) if lo_better
                else worst - slack * abs(full - worst))
    if lo_better:
        return float(np.clip((zero - value) / max(zero - full, 1e-9), 0, 1))
    return float(np.clip((value - zero) / max(full - zero, 1e-9), 0, 1))


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


def score(warped_path, dseg_path, pack_dir):
    pack = Path(pack_dir)
    rubric = json.load(open(subject_rubric(pack)))
    refdir = pack / "reference"
    # cross_modal mode scores mask overlap and NMI, so the tissue priors are not needed
    need = ["template_T1w.nii.gz", "template_brain_mask.nii.gz"]
    if rubric.get("mode", MODE_LABEL) == MODE_LABEL:
        need += [f"template_probseg_{t}.nii.gz" for t in rubric.get("tissue_labels", TISSUES)]
    missing = [n for n in need if not (refdir / n).exists()]
    if missing:
        raise SystemExit(f"ERROR: missing reference file(s) in {refdir}: {missing}. "
                         "Fetch them with benchmark/harness/fetch_reference.py.")

    tpl_img = nib.as_closest_canonical(nib.load(str(refdir / "template_T1w.nii.gz")))
    ref = {"T1w": np.asanyarray(tpl_img.dataobj).astype(np.float64),
           "brain_mask": np.asanyarray(nib.as_closest_canonical(
               nib.load(str(refdir / "template_brain_mask.nii.gz"))).dataobj) > 0.5}
    if rubric.get("mode", MODE_LABEL) == MODE_LABEL:
        for t in rubric.get("tissue_labels", TISSUES):
            ref[f"prior_{t}"] = np.asanyarray(nib.as_closest_canonical(
                nib.load(str(refdir / f"template_probseg_{t}.nii.gz"))).dataobj).astype(np.float64)

    warped, notes_w, nonfinite_w = load_on_grid(warped_path, tpl_img, label=False)
    seg, notes_s, _ = load_on_grid(dseg_path, tpl_img, label=True)
    seg_raw = seg
    seg = np.rint(seg).astype(int)

    labels = rubric.get("tissue_labels", TISSUES)
    m = evaluate(warped, seg, ref, rubric)
    gates = validity_gates(warped, seg, notes_w, notes_s, rubric, m, nonfinite_w,
                           ref["brain_mask"], seg_raw=seg_raw)
    failures = [k for k, ok in gates.items() if not ok]

    weights = rubric["weights"]
    subs = {k: subscore(m[k], rubric["envelope"][k], k, rubric["slack"]) for k in weights}
    quality = 100 * sum(weights[k] * subs[k] for k in weights)
    within = all((m[k] <= rubric["envelope"][k]["worst"]) if k in LOWER_BETTER
                 else (m[k] >= rubric["envelope"][k]["worst"]) for k in weights)
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

    # Diagnostic, never scored. The task says to warp the SUPPLIED segmentation, which keeps
    # 1=GM 2=WM 3=CSF. An agent that instead re-segments with, say, FSL FAST gets the same label
    # set in a different order and scores badly for a reason that looks like bad registration.
    # Naming it turns a confusing zero into an actionable one.
    best_perm = None
    if rubric.get("mode", MODE_LABEL) == MODE_LABEL:
        best_mean = sum(m[f"dice_{t.lower()}"] for t in labels) / len(labels)
        import itertools as _it
        codes = [labels[t] for t in labels]
        for perm in _it.permutations(codes):
            if list(perm) == codes:
                continue
            alt = {t: perm[i] for i, t in enumerate(labels)}
            mean = sum(dice(seg == alt[t], ref[f"prior_{t}"] >= rubric.get("prior_threshold", 0.5))
                       for t in labels) / len(labels)
            if mean > best_mean:
                best_mean, best_perm = mean, alt
    result_extra = {}
    if best_perm is not None:
        result_extra["suspected_label_permutation"] = {
            "mapping": best_perm, "mean_tissue_dice_if_applied": round(best_mean, 4)}

    return {"verdict": verdict, "quality": round(quality, 2), "gate_failures": failures,
            **result_extra,
            "load_notes": notes_w + notes_s,
            "subscores": {k: round(v, 3) for k, v in subs.items()},
            "metrics": {k: (round(float(v), 4) if np.isfinite(v) else None) for k, v in m.items()}}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Grade a registration into MNI. The scoring mode is set by the "
                    "pack's rubric.json: label_propagation for T1w-to-MNI, "
                    "cross_modal for BOLD-to-MNI.")
    ap.add_argument("--warped", required=True,
                    help="agent image resampled into MNI: the T1w, or the BOLD reference (NIfTI)")
    ap.add_argument("--dseg", required=True,
                    help="agent label volume carried through the same transform: the tissue "
                         "segmentation in label_propagation mode, the brain mask in cross_modal "
                         "mode (NIfTI)")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    r = score(a.warped, a.dseg, a.pack)
    print(json.dumps(r, indent=2))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=2)
    return 0 if not r["gate_failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
