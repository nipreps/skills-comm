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
import os
import shutil
import sys
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np

# This file lives in benchmark/harness/, so the benchmark root is two levels up.
REPO = Path(__file__).resolve().parent.parent
# The build tree holds the staged references, the gated calibration and each task's
# working directory. It is not part of the repository: pass --build, or set
# SKILLS_COMM_BUILD. Probes whose inputs are absent are reported as absent, not failed,
# so the test still runs usefully without it.
BUILD = Path(os.environ.get("SKILLS_COMM_BUILD", "")).expanduser() if os.environ.get(
    "SKILLS_COMM_BUILD") else None
STAGE = CAL = None
MAN = json.load(open(REPO / "harness/run_manifest.json"))["tasks"]

# which reference file a submission is compared against, per scorer family
GRADED = {"score_lesion_seg.py": "lesion_mask.nii.gz",
          "score_brain_mask.py": "consensus_mask.nii.gz",
          "score_tissue_seg.py": "consensus_seg.nii.gz"}

# Registration probes. A registration task is not probed with a copy of its reference --
# the reference is the template, not anything a submission produces -- so the probes are
# the panel's own arms, and the claim under test is the ordering between them.
#
# `flat` maps the arms the original single-subject build wrote outside panel/; every
# other subject has all of them under subjects/<id>/panel/.
REG_PROBES = {
    "structural-mni-registration": {
        "build": "ground_truth_registration",
        "control": "sub-0006",
        "suffix": ("_T1w.nii.gz", "_dseg.nii.gz"),
        "flat": {},
        "arms": [("ANTs SyN", "nonlinear", "ants/ants_syn"),
                 ("FSL FNIRT", "nonlinear", "fsl/fsl_fnirt"),
                 ("NiftyReg f3d", "nonlinear", "niftyreg/nr_f3d"),
                 ("ANTs affine", "affine", "ants/ants_affine"),
                 ("FSL FLIRT", "affine", "fsl/fsl_flirt"),
                 ("NiftyReg aladin", "affine", "niftyreg/nr_aladin")],
        "order": ("nonlinear", "affine"),
    },
    "functional-bold-to-mni": {
        "build": "ground_truth_bold_mni",
        "control": "sub-0019",
        "suffix": ("_boldref.nii.gz", "_boldmask.nii.gz"),
        "flat": {"fsl_chain": "fsl_arm/fsl_chain",
                 "direct_affine": "probe/direct_affine",
                 "direct_syn": "probe/direct_syn"},
        "arms": [("ANTs, correct chain", "anatomy-mediated", "ants_correct"),
                 ("FSL chain", "anatomy-mediated", "fsl_chain"),
                 ("ANTs, no EPI stage", "candidate", "ants_no_epi"),
                 ("ANTs, reversed list", "candidate", "ants_reversed"),
                 ("direct affine", "direct", "direct_affine"),
                 ("direct SyN", "direct", "direct_syn")],
        "order": ("anatomy-mediated", "direct"),
    },
}


def probe_paths(cfg, subject):
    """(label, kind, warped, dseg) for one subject, relative to the build dir."""
    b, w_sfx, d_sfx = cfg["build"], *cfg["suffix"]
    out = []
    for label, kind, stem in cfg["arms"]:
        rel = (cfg["flat"].get(stem, f"panel/{stem}")
               if subject in (None, cfg["control"])
               else f"subjects/{subject}/panel/{stem}")
        out.append((label, kind, f"{b}/{rel}{w_sfx}", f"{b}/{rel}{d_sfx}"))
    return out

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
    cfg = REG_PROBES.get(task)
    if not cfg:
        rows.append((task, "-", "(no probe defined)", "-", "skipped", None))
        return
    sc = scorer(spec["scorer"])
    # A per-subject registration task shares one template reference and varies only the
    # rubric, so each subject's panel is probed against its own envelope.
    for sub in (spec.get("subjects") or [None]):
        run_registration_subject(task, spec, cfg, sc, sub, rows)


def run_registration_subject(task, spec, cfg, sc, subject, rows):
    seen = {}
    for label, kind, w, d in probe_paths(cfg, subject):
        wp, dp = BUILD / w, BUILD / d
        if not wp.is_file() or not dp.is_file():
            rows.append((task, subject or "-", label, kind, "arm absent", None))
            continue
        t = build_pack(task, spec, subject)
        try:
            v, q, f = verdict_of(sc.score(str(wp), str(dp), str(t)))
        except SystemExit as e:
            rows.append((task, subject or "-", label, kind,
                         f"refused: {str(e)[:30]}", None))
            shutil.rmtree(t)
            continue
        shutil.rmtree(t)
        seen.setdefault(kind, []).append(q)
        rows.append((task, subject or "-", label, kind, f"{v} q{q:.1f}", None))
    # the ordering claim this task makes, checked on this subject rather than on average
    good, bad = cfg["order"]
    if good in seen and bad in seen:
        ok = min(seen[good]) > max(seen[bad])
        rows.append((task, subject or "-", f"{good} > {bad}", "ordering",
                     f"{min(seen[good]):.1f} vs {max(seen[bad]):.1f}", ok))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", action="append")
    ap.add_argument("--build", help="the build tree holding hf_stage/, hf_calibration/ "
                                    "and each task's working directory; defaults to "
                                    "$SKILLS_COMM_BUILD")
    a = ap.parse_args()
    global BUILD, STAGE, CAL
    if a.build:
        BUILD = Path(a.build).expanduser()
    if BUILD is None:
        print("No build tree given (--build or $SKILLS_COMM_BUILD). Only probes that "
              "read from each pack's own reference/ will run.", file=sys.stderr)
        BUILD = Path("/nonexistent")
    STAGE, CAL = BUILD / "hf_stage", BUILD / "hf_calibration"
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
