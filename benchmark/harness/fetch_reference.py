#!/usr/bin/env python3
"""Fetch a task's grader-side reference NIfTIs into its pack/reference/.

Policy: code on GitHub, reference data on the Hugging Face Hub. A rubric straddles the
two -- its policy half is code and stays in the repo, its calibrated half describes the
reference and ships gated -- so this script merges them into the reference/rubric.json
the scorer reads. This runs in the GRADING plane
only — never in the plane where the agent produces its answer, so the ground truth is never
exposed to the model.

Reads run_manifest.json for the task's ref_dir + reference_files and pulls each from the reference
dataset repo at the pinned revision, so a grading run scores against an exact, named reference set.

Access to the dataset is gated, which is what keeps the reference out of the execution plane: the
grading job supplies a read token via the HF_TOKEN environment variable, and the plane where the
agent works has none. Idempotent — files already present are left untouched.

    python fetch_reference.py --task clinical-wmh-segmentation
    python fetch_reference.py --task structural-brain-extraction --case case-042

A task graded per subject needs --subject, or --case with the case id a benchmark run
names; the reference dataset's cases.json (see cases.py) says which subjects a task has
and which subject a case is.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

try:
    from . import cases as cases_mod       # imported as benchmark.harness.fetch_reference
except ImportError:
    import cases as cases_mod              # run as a script from this directory


def fetch(task_id, manifest_path, graders_root=None, force=False, revision=None,
          subject=None):
    manifest_path = Path(manifest_path)
    m = json.load(open(manifest_path))
    if task_id not in m["tasks"]:
        raise SystemExit(f"ERROR: task '{task_id}' not in {manifest_path}")
    spec = m["tasks"][task_id]
    root = Path(graders_root).resolve() if graders_root else manifest_path.resolve().parent.parent
    defaults = m["defaults"]
    repo_id = defaults["reference_repo"]
    repo_type = defaults.get("reference_repo_type", "dataset")
    # A task may pin its own revision. The per-subject references were uploaded in a
    # later commit than the single-subject ones, and those still resolve at the older
    # pin, so one default for the whole manifest would move references nobody rebuilt.
    rev = revision or spec.get("reference_revision") or defaults.get("reference_revision")
    ref_dir = spec["ref_dir"]                        # e.g. clinical_gt/clinical-wmh-segmentation
    calib_dir = defaults.get("calibration_dir", "calibration")
    rubrics_dir = defaults.get("rubrics_dir", "rubrics")
    # Whether a subject is required is decided by `per_subject`, not by the shape of
    # ref_dir. Most per-subject tasks keep one reference directory per subject and carry
    # {subject} in the path, but a registration task does not: its reference is a
    # template, identical for every subject, and only the calibration differs. Copying a
    # template per subject would add nothing to the Hub but weight.
    per_subject = spec.get("per_subject") or "{subject}" in ref_dir
    allowed = spec.get("subjects") or []
    if per_subject and not allowed:
        # The subjects live in the gated cases.json, not in the manifest: the allowed
        # list comes from there, and a case id becomes its subject.
        cs = cases_mod.load(m, rev)
        allowed = cases_mod.subjects_of(cs, task_id)
        if subject is not None:
            subject = cases_mod.resolve(cs, task_id, subject)
    if per_subject:
        # Checked against the list rather than interpolated blindly: a typo would
        # otherwise come back as a confusing 404 from the Hub.
        if subject is None:
            raise SystemExit(
                f"ERROR: '{task_id}' is graded per subject; pass --subject.\n"
                f"Available: {', '.join(allowed) if allowed else '(none listed)'}")
        if allowed and subject not in allowed:
            raise SystemExit(f"ERROR: '{subject}' is not a subject of '{task_id}'.\n"
                             f"Available: {', '.join(allowed)}")
        if "{subject}" in ref_dir:
            ref_dir = ref_dir.replace("{subject}", subject)
    elif subject:
        raise SystemExit(f"ERROR: '{task_id}' has a single reference; --subject does not "
                         "apply to it")

    dest = root / spec["pack_dir"] / "reference"
    dest.mkdir(parents=True, exist_ok=True)

    # Reference filenames are the same for every subject, so "already present" cannot be
    # read as "already correct": fetching subject B into a directory still holding
    # subject A would skip every file and leave A's masks beside B's rubric. The marker
    # records whose reference is in there, and a different subject forces a re-fetch.
    marker = dest / ".subject"
    held = marker.read_text().strip() if marker.is_file() else None
    shared_ref = subject is not None and "{subject}" not in spec["ref_dir"]
    if subject and held != subject and not shared_ref:
        if held is not None:
            print(f"  [switch] reference/ holds {held}; re-fetching for {subject}")
        force = True

    for fname in spec["reference_files"]:
        local = dest / fname
        if local.exists() and not force:
            print(f"  [skip] {fname} already present")
            continue
        remote = f"{ref_dir}/{fname}"
        print(f"  [fetch] {repo_id}@{rev or 'main'}:{remote} -> {local}")
        try:
            got = hf_hub_download(repo_id=repo_id, repo_type=repo_type, filename=remote,
                                  revision=rev, force_download=force)
        except Exception as e:
            hint = ""
            if "401" in str(e) or "403" in str(e) or "gated" in str(e).lower():
                hint = ("\nThe dataset is gated. Set HF_TOKEN to a token whose account has been "
                        "granted\naccess, then retry. Request access on the dataset page.")
            raise SystemExit(f"ERROR: could not fetch {remote} from {repo_id}\n"
                             f"{type(e).__name__}: {e}{hint}")
        # Copy out of the shared cache so the pack owns its reference and a later cache sweep
        # cannot empty it mid-run.
        shutil.copyfile(got, local)
    # The rubric arrives in two halves. Policy -- gates, weights, slack, the verdict
    # thresholds, the fixed caps and every *_basis that explains them -- lives in the
    # repo, so grading criteria can be read and reviewed without gated access and so they
    # version with the scorer that applies them. The calibrated half -- which tools made
    # the consensus, tau, the envelope, the focal cap and the reference volumes -- is
    # answer key: it describes this reference and, in the case of reference_tools, says
    # exactly how to reproduce it. Benchmark wave 7 recorded 22 runs reading rubric text
    # off public GitHub, so that half ships with the gated reference instead and is
    # merged here, where the agent cannot reach it.
    if subject:
        # The policy half is one file per task, with nothing about any subject in it: the
        # subject's own part (item, prompt, grid) ships gated beside its reference, so the
        # public repository names no subject anywhere.
        src = root / spec["pack_dir"] / "rubrics" / "policy.json"
        if not src.is_file():
            raise SystemExit(f"ERROR: no rubric policy at {src}")
        rubric = json.loads(src.read_text())
        merged_from = None
        if rubric.pop("_subject", None) is not None:
            remote = f"{rubrics_dir}/{task_id}/{subject}.json"
            print(f"  [fetch] {repo_id}@{rev or 'main'}:{remote}")
            try:
                got = hf_hub_download(repo_id=repo_id, repo_type=repo_type,
                                      filename=remote, revision=rev,
                                      force_download=force)
            except Exception as e:
                raise SystemExit(
                    f"ERROR: {src.name} expects the subject's gated rubric but {remote} could "
                    f"not be fetched from {repo_id}\n{type(e).__name__}: {e}")
            part = json.loads(Path(got).read_text())
            clash = sorted(set(part) & set(rubric))
            if clash:
                raise SystemExit(f"ERROR: {remote} and {src.name} both define {clash}")
            rubric.update(part)
            merged_from = remote
        if rubric.pop("_calibration", None) is not None:
            remote = f"{calib_dir}/{task_id}/{subject}.json"
            print(f"  [fetch] {repo_id}@{rev or 'main'}:{remote}")
            try:
                got = hf_hub_download(repo_id=repo_id, repo_type=repo_type,
                                      filename=remote, revision=rev,
                                      force_download=force)
            except Exception as e:
                raise SystemExit(
                    f"ERROR: {src.name} expects gated calibration but {remote} could not "
                    f"be fetched from {repo_id}\n{type(e).__name__}: {e}\n"
                    "The rubric is policy-only without it and would grade against the "
                    "wrong thresholds, so this is fatal rather than a warning.")
            calib = json.loads(Path(got).read_text())
            clash = sorted(set(calib) & set(rubric))
            if clash:
                raise SystemExit(f"ERROR: {remote} and {src.name} both define {clash}; "
                                 "the split is supposed to be disjoint")
            rubric.update(calib)
            merged_from = f"{merged_from} + {remote}" if merged_from else remote
        (dest / "rubric.json").write_text(json.dumps(rubric, indent=2) + "\n")
        print(f"  [rubric] {src.name}"
              + (f" + {merged_from}" if merged_from else "")
              + f" -> {dest / 'rubric.json'}")

    if subject:
        marker.write_text(subject + "\n")
    print(f"reference ready: {dest}")
    return dest


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fetch a task's reference into its grader pack.")
    ap.add_argument("--task", required=True)
    ap.add_argument("--manifest", default=str(Path(__file__).parent / "run_manifest.json"))
    ap.add_argument("--graders-root")
    ap.add_argument("--force", action="store_true", help="re-fetch even if present")
    ap.add_argument("--revision", help="override the revision pinned in the manifest")
    ap.add_argument("--subject", help="which subject's reference to fetch, for the tasks "
                                      "that are graded per subject")
    ap.add_argument("--case", dest="subject", help="the case id a run names; the reference "
                                                   "dataset's cases.json maps it to the subject")
    a = ap.parse_args(argv)
    fetch(a.task, a.manifest, a.graders_root, a.force, a.revision, a.subject)
    return 0


if __name__ == "__main__":
    sys.exit(main())
