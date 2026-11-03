#!/usr/bin/env python3
"""Exercise every graded task through its shipped scorer.

Each task is probed with submissions of known quality, and the point is not that a
number comes out but that the ordering is right: something a competent person would
produce must pass, something broken must be refused, and where a task claims to separate
two approaches, it must actually separate them.

Probes by task shape:

  mask and segmentation tasks
      perfect       an exact copy of the graded reference -> must score 100, no gate fails
      empty         all zeros on the same grid             -> must be invalid
      wrong rubric  another subject's rubric               -> must be refused outright,
                    because a perfect answer scores 100 whichever rubric is applied and a
                    silently wrong envelope is the failure the per-subject split exists
                    to prevent

  registration tasks
      the panel's own arms, nonlinear and affine. These tasks claim that label
      propagation separates a nonlinear warp from an affine one, so the affine arms must
      score below the nonlinear ones. A copy of the reference is not a probe here: the
      reference is the template's tissue priors, not anything a submission produces.

Read-only. Nothing is uploaded, pinned or deleted.

Usage: smoke_test.py [--task TASK]...
"""
import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np

REPO = Path("/home/jovyan/Git_repositories/skills-comm/benchmark")
STAGE = Path("/home/jovyan/benchmark_v0.4/hf_stage")
CAL = Path("/home/jovyan/benchmark_v0.4/hf_calibration")
BUILD = Path("/home/jovyan/benchmark_v0.4")
MAN = json.load(open(REPO / "harness/run_manifest.json"))["tasks"]

# which reference file a submission is compared against, per scorer family
GRADED = {"score_lesion_seg.py": "lesion_mask.nii.gz",
          "score_brain_mask.py": "consensus_mask.nii.gz",
          "score_tissue_seg.py": "consensus_seg.nii.gz"}

# registration probes: (label, expectation, warped, dseg) relative to the build dir
REG_PROBES = {
    "structural-mni-registration": [
        ("ANTs SyN", "nonlinear", "ground_truth_registration/panel/ants/ants_syn_T1w.nii.gz",
         "ground_truth_registration/panel/ants/ants_syn_dseg.nii.gz"),
        ("FSL FNIRT", "nonlinear", "ground_truth_registration/panel/fsl/fsl_fnirt_T1w.nii.gz",
         "ground_truth_registration/panel/fsl/fsl_fnirt_dseg.nii.gz"),
        ("NiftyReg f3d", "nonlinear", "ground_truth_registration/panel/niftyreg/nr_f3d_T1w.nii.gz",
         "ground_truth_registration/panel/niftyreg/nr_f3d_dseg.nii.gz"),
        ("ANTs affine", "affine", "ground_truth_registration/panel/ants/ants_affine_T1w.nii.gz",
         "ground_truth_registration/panel/ants/ants_affine_dseg.nii.gz"),
        ("FSL FLIRT", "affine", "ground_truth_registration/panel/fsl/fsl_flirt_T1w.nii.gz",
         "ground_truth_registration/panel/fsl/fsl_flirt_dseg.nii.gz"),
        ("NiftyReg aladin", "affine", "ground_truth_registration/panel/niftyreg/nr_aladin_T1w.nii.gz",
         "ground_truth_registration/panel/niftyreg/nr_aladin_dseg.nii.gz"),
    ],
    "functional-bold-to-mni": [
        ("ANTs, EPI corrected", "good",
         "ground_truth_bold_mni/panel/ants_correct_boldref.nii.gz",
         "ground_truth_bold_mni/panel/ants_correct_boldmask.nii.gz"),
        ("ANTs, no EPI correction", "degraded",
         "ground_truth_bold_mni/panel/ants_no_epi_boldref.nii.gz",
         "ground_truth_bold_mni/panel/ants_no_epi_boldmask.nii.gz"),
        ("ANTs, reversed phase encoding", "wrong",
         "ground_truth_bold_mni/panel/ants_reversed_boldref.nii.gz",
         "ground_truth_bold_mni/panel/ants_reversed_boldmask.nii.gz"),
    ],
}

_mods = {}


def scorer(rel):
    if rel not in _mods:
        sp = importlib.util.spec_from_file_location(f"sc{len(_mods)}", REPO / rel)
        m = importlib.util.module_from_spec(sp)
        sys.modules[f"sc{len(_mods)}"] = m
        sp.loader.exec_module(m)
        _mods[rel] = m
    return _mods[rel]


def build_pack(task, spec, subject, rubric_from=None):
    """A temporary pack holding the reference and the merged rubric, as fetch_reference
    assembles it."""
    t = Path(tempfile.mkdtemp())
    (t / "reference").mkdir()
    base = spec["ref_dir"].replace("/{subject}", "")
    # the staging tree holds what was uploaded from here; a task whose reference was
    # never staged locally is read from the pack's own fetched reference/ instead
    src = STAGE / base / subject if subject else STAGE / base
    fallback = REPO / spec["pack_dir"] / "reference"
    for f in spec["reference_files"]:
        p = src / f
        if not p.is_file():
            p = fallback / f
        if not p.is_file():
            shutil.rmtree(t)
            raise FileNotFoundError(f"{f}: not in {src} nor {fallback}")
        shutil.copy(p, t / "reference" / f)
    who = rubric_from or subject
    rp = (REPO / "graders" / task / "rubrics" / f"{who}.json") if who else \
         (REPO / "graders" / task / "rubric.json")
    r = json.loads(rp.read_text())
    if r.pop("_calibration", None) is not None:
        c = CAL / task / f"{who}.json"
        if not c.is_file():
            shutil.rmtree(t)
            raise FileNotFoundError(c)
        r.update(json.loads(c.read_text()))
    (t / "reference" / "rubric.json").write_text(json.dumps(r, indent=2))
    return t


def verdict_of(r):
    gf = r["gate_failures"]
    failed = [k for k, v in gf.items() if v] if isinstance(gf, dict) else (gf or [])
    return r["verdict"], r["quality"], failed


def run_segmentation(task, spec, rows):
    sc = scorer(spec["scorer"])
    name = Path(spec["scorer"]).name
    graded = GRADED[name]
    base = spec["ref_dir"].replace("/{subject}", "")
    subs = spec.get("subjects") or [None]
    for i, sub in enumerate(subs):
        src = (STAGE / base / sub if sub else STAGE / base) / graded
        # perfect
        t = build_pack(task, spec, sub)
        shutil.copy(src, t / "pred.nii.gz")
        v, q, f = verdict_of(sc.score(str(t / "pred.nii.gz"), str(t)))
        rows.append((task, sub or "-", "perfect copy", "pass at 100",
                     f"{v} q{q:.1f}", not f and abs(q - 100) < 1e-6))
        shutil.rmtree(t)
        # empty
        t = build_pack(task, spec, sub)
        img = nib.load(str(src))
        nib.save(nib.Nifti1Image(np.zeros(img.shape, "uint8"), img.affine, img.header),
                 t / "pred.nii.gz")
        try:
            v, q, f = verdict_of(sc.score(str(t / "pred.nii.gz"), str(t)))
            rows.append((task, sub or "-", "all zeros", "invalid", f"{v} q{q:.1f}",
                         v == "invalid"))
        except SystemExit as e:
            rows.append((task, sub or "-", "all zeros", "invalid", "refused", True))
        shutil.rmtree(t)
        # wrong rubric, only where there is another subject to borrow from
        if sub and len(subs) > 1:
            other = subs[(i + 1) % len(subs)]
            try:
                t = build_pack(task, spec, sub, rubric_from=other)
                shutil.copy(src, t / "pred.nii.gz")
                v, q, f = verdict_of(sc.score(str(t / "pred.nii.gz"), str(t)))
                rows.append((task, sub, f"rubric of {other}", "refused",
                             f"SCORED {v} q{q:.1f}", False))
                shutil.rmtree(t)
            except SystemExit:
                rows.append((task, sub, f"rubric of {other}", "refused", "refused", True))


def run_registration(task, spec, rows):
    sc = scorer(spec["scorer"])
    probes = REG_PROBES.get(task, [])
    if not probes:
        rows.append((task, "-", "(no probe defined)", "-", "skipped", None))
        return
    seen = {}
    for label, kind, w, d in probes:
        wp, dp = BUILD / w, BUILD / d
        if not wp.is_file() or not dp.is_file():
            rows.append((task, "-", label, kind, "mask absent", None))
            continue
        t = build_pack(task, spec, None)
        try:
            v, q, f = verdict_of(sc.score(str(wp), str(dp), str(t)))
        except SystemExit as e:
            rows.append((task, "-", label, kind, f"refused: {str(e)[:40]}", None))
            shutil.rmtree(t)
            continue
        shutil.rmtree(t)
        seen.setdefault(kind, []).append(q)
        rows.append((task, "-", label, kind, f"{v} q{q:.1f}", None))
    # the ordering claim: a nonlinear warp must beat an affine one
    if "nonlinear" in seen and "affine" in seen:
        ok = min(seen["nonlinear"]) > max(seen["affine"])
        rows.append((task, "-", "nonlinear > affine", "ordering",
                     f"min nonlinear {min(seen['nonlinear']):.1f} vs "
                     f"max affine {max(seen['affine']):.1f}", ok))
    if "good" in seen and "wrong" in seen:
        ok = min(seen["good"]) > max(seen["wrong"])
        rows.append((task, "-", "corrected > reversed", "ordering",
                     f"{min(seen['good']):.1f} vs {max(seen['wrong']):.1f}", ok))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", action="append")
    a = ap.parse_args()
    rows = []
    for task in sorted(a.task or MAN):
        spec = MAN[task]
        print(f"... {task}", flush=True)
        try:
            if Path(spec["scorer"]).name == "score_registration.py":
                run_registration(task, spec, rows)
            else:
                run_segmentation(task, spec, rows)
        except Exception as e:
            rows.append((task, "-", "harness", "-", f"{type(e).__name__}: {str(e)[:50]}",
                         False))

    print(f"\n{'task':38s} {'subject':14s} {'probe':22s} {'expected':12s} "
          f"{'observed':34s} ok")
    bad = 0
    for task, sub, probe, exp, obs, ok in rows:
        mark = "-" if ok is None else ("yes" if ok else "NO")
        bad += ok is False
        print(f"{task[:38]:38s} {sub[:14]:14s} {probe[:22]:22s} {exp[:12]:12s} "
              f"{obs[:34]:34s} {mark}")
    checked = sum(1 for r in rows if r[5] is not None)
    print(f"\n{len(rows)} probes, {checked} with a pass/fail expectation, {bad} failing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
