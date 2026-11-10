#!/usr/bin/env python3
"""Uniform grading front-end for the benchmark.

The task scorers emit different result shapes and take differently named prediction flags.
This wrapper is the single entry point the CI grading job calls. It:

  1. looks a task up in run_manifest.json (task -> pack, scorer, prediction flag, detail shape),
  2. finds the agent's submission at the ONE contracted path (no fuzzy file discovery),
  3. runs the correct scorer as a subprocess,
  4. wraps the raw result in a stable envelope with a numeric, rankable `score`
     plus run provenance (model, condition, timestamp),
  5. normalises the per-scorer detail block under a common `detail` key.

`aggregate` mode reads many envelopes and produces a ranked leaderboard.json.

The three scorers are never modified — all cross-scorer uniformity lives here.

Envelope schema (schema_version 1.0):

    {
      "schema_version": "1.0",
      "task_id": str,
      "subject": str | null,        # the subject graded, for a task graded per subject
      "model": str,                 # e.g. "qwen"           (runner-supplied)
      "condition": str,             # "baseline" | "skill"  (runner-supplied)
      "timestamp": str,             # ISO-8601 UTC          (runner-supplied or now)
      "scorer": str,                # scorer filename
      "pack": str,                  # pack dir (relative)
      "valid": bool,                # == (no gate failures)
      "verdict": str,               # invalid|unacceptable|marginal|acceptable|within_reference_variability
      "score": float,               # 0..100 quality  -> PRIMARY RANK KEY
      "tiebreak": float,            # secondary rank key (mean Dice), for equal scores
      "gate_failures": [str],
      "load_notes": [str],
      "detail": {"kind": "binary"|"multiclass", ...},
      "raw": {...}                  # full untouched scorer output, for drill-down
    }
"""
import argparse
import glob
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import cases as cases_mod       # imported as benchmark.harness.grade_wrapper
except ImportError:
    import cases as cases_mod              # run as a script from this directory

SCHEMA_VERSION = "1.0"

# Ordering of the verdict vocabulary, worst -> best. Used only for display/tie context;
# ranking is on the numeric `score`, which is already monotonic with the verdict tier.
VERDICT_ORDER = ["invalid", "unacceptable", "marginal", "acceptable", "within_reference_variability"]


def _utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_root(manifest_path: Path, override: str | None) -> Path:
    """graders_root holds graders/ ; default = parent of the manifest's directory."""
    return Path(override).resolve() if override else manifest_path.resolve().parent.parent


def _mean_dice(raw: dict, detail_kind: str) -> float:
    """Secondary rank key: mean Dice across whatever the task measures. 0.0 if absent."""
    if detail_kind == "multiclass":
        pc = raw.get("per_class", {})
        vals = [c.get("dice") for c in pc.values() if isinstance(c, dict) and c.get("dice") is not None]
        return round(sum(vals) / len(vals), 4) if vals else 0.0
    d = (raw.get("metrics") or {}).get("dice")
    return round(float(d), 4) if d is not None else 0.0


def _normalise_detail(raw: dict, detail_kind: str) -> dict:
    """Fold each scorer's drill-down into one shape the dashboard can load uniformly."""
    if detail_kind == "multiclass":
        return {"kind": "multiclass", "per_class": raw.get("per_class", {})}
    return {"kind": "binary",
            "metrics": raw.get("metrics", {}),
            "subscores": raw.get("subscores", {})}


def grade(task_id, submission_dir, manifest_path, graders_root=None,
          model="unknown", condition="baseline", timestamp=None, subject=None):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if task_id not in manifest["tasks"]:
        raise SystemExit(f"ERROR: task '{task_id}' not in {manifest_path}. "
                         f"Known: {', '.join(sorted(manifest['tasks']))}")
    spec = manifest["tasks"][task_id]
    # A task graded per subject needs the subject named, and it has to be one of its
    # own; a task with one reference takes none. Checked here, not left to str.format,
    # where a missing subject is a KeyError and a wrong one a quiet path to nothing.
    allowed = spec.get("subjects") or []
    if spec.get("per_subject") and not allowed:
        # The subjects live in the gated cases.json, not in the manifest: the allowed
        # list comes from there, and a case id becomes its subject.
        cs = cases_mod.load(manifest, spec.get("reference_revision"))
        allowed = cases_mod.subjects_of(cs, task_id)
        if subject is not None:
            subject = cases_mod.resolve(cs, task_id, subject)
    if spec.get("per_subject"):
        if subject is None:
            raise SystemExit(f"ERROR: '{task_id}' is graded per subject; pass --subject.\n"
                             f"Available: {', '.join(allowed) if allowed else '(none listed)'}")
        if allowed and subject not in allowed:
            raise SystemExit(f"ERROR: '{subject}' is not a subject of '{task_id}'.\n"
                             f"Available: {', '.join(allowed)}")
    elif subject:
        raise SystemExit(f"ERROR: '{task_id}' has a single reference; --subject does not "
                         "apply to it")
    fields = {"task_id": task_id, "subject": subject or ""}
    root = _resolve_root(manifest_path, graders_root)

    scorer = root / spec["scorer"]
    pack = root / spec["pack_dir"]
    if not scorer.exists():
        raise SystemExit(f"ERROR: scorer not found: {scorer}")
    # A pack carries either one rubric, or rubrics/policy.json for the tasks graded per
    # subject, which fetch_reference.py --subject merges with the subject's gated part
    # into reference/rubric.json. Requiring rubric.json of a per-subject pack would mean
    # keeping a copy of one subject's calibration at the pack root, where nothing reads
    # it and nothing says which subject it describes.
    if not ((pack / "rubric.json").exists() or (pack / "rubrics" / "policy.json").is_file()):
        raise SystemExit(f"ERROR: no rubric.json and no rubrics/policy.json in pack: {pack}")

    # The contracted path: the task's own, else the manifest default for a task graded
    # per subject (submission_path, one level deeper) or for one with a single reference.
    defaults = manifest["defaults"]
    out_rel = (spec.get("submission_output_path")
               or defaults["submission_path" if subject else "submission_output_path"]
               ).format(**fields)
    pred = Path(submission_dir) / out_rel
    if not pred.exists():
        # A missing contracted output is a submission failure, not a harness crash:
        # report it as an invalid verdict so it still lands on the leaderboard at 0.
        return _envelope(task_id, spec, model, condition, timestamp,
                         raw={"verdict": "invalid", "quality": 0.0,
                              "gate_failures": ["missing_output"],
                              "load_notes": [f"no submission at {out_rel}"]},
                         subject=subject)

    # Build: python <scorer> <pred_flag> <pred> --pack <pack> --json <tmp> [extra inputs]
    result_json = Path(submission_dir) / f".grade_{task_id}.json"
    cmd = [sys.executable, str(scorer), spec["pred_flag"], str(pred),
           "--pack", str(pack), "--json", str(result_json)]
    for flag, rel in (spec.get("required_inputs") or {}).items():
        cand = Path(submission_dir) / rel.format(**fields)
        if not cand.exists():
            return _envelope(
                task_id, spec, model, condition, timestamp,
                raw={"verdict": "invalid", "quality": 0.0,
                     "gate_failures": [f"missing_required_output:{cand.name}"],
                     "load_notes": [f"no submission at {rel.format(**fields)}"]},
                subject=subject,
            )
        cmd += [flag, str(cand)]
    for flag, rel in (spec.get("optional_inputs") or {}).items():
        cand = Path(submission_dir) / rel.format(**fields)
        if cand.exists():
            cmd += [flag, str(cand)]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    # Scorers exit 1 on gate failure by design — that is NOT a harness error. A harness
    # error is: no result file written (crash / bad args). Detect that explicitly.
    if not result_json.exists():
        raise SystemExit(f"ERROR: scorer produced no result for {task_id} (exit {proc.returncode}).\n"
                         f"cmd: {' '.join(cmd)}\nstderr:\n{proc.stderr}")
    raw = json.load(open(result_json))
    result_json.unlink(missing_ok=True)
    return _envelope(task_id, spec, model, condition, timestamp, raw, subject=subject)


def _envelope(task_id, spec, model, condition, timestamp, raw, subject=None):
    detail_kind = spec["detail_kind"]
    gate_failures = raw.get("gate_failures", [])
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "subject": subject,
        "model": model,
        "condition": condition,
        "timestamp": timestamp or _utcnow_iso(),
        "scorer": Path(spec["scorer"]).name,
        "pack": spec["pack_dir"],
        "valid": not gate_failures,
        "verdict": raw.get("verdict", "invalid"),
        "score": float(raw.get("quality", 0.0)),
        "tiebreak": _mean_dice(raw, detail_kind),
        "gate_failures": gate_failures,
        "load_notes": raw.get("load_notes", []),
        "detail": _normalise_detail(raw, detail_kind),
        "raw": raw,
    }


def _rank(subs):
    """Rank submissions best -> worst: primary score desc, then mean-Dice tiebreak desc."""
    ordered = sorted(subs, key=lambda e: (e["score"], e["tiebreak"]), reverse=True)
    for i, e in enumerate(ordered, 1):
        e["rank"] = i
    return ordered


def aggregate(envelope_glob, out_path):
    """Read many envelopes and emit a ranked leaderboard: per-task ranking + a wide matrix."""
    files = sorted(glob.glob(envelope_glob))
    envs = [json.load(open(f)) for f in files]
    by_task = {}
    for e in envs:
        by_task.setdefault(e["task_id"], []).append(e)

    tasks = {}
    for tid, subs in sorted(by_task.items()):
        ranked = _rank(subs)
        tasks[tid] = [
            {"rank": e["rank"], "model": e["model"], "condition": e["condition"],
             "verdict": e["verdict"], "valid": e["valid"], "score": round(e["score"], 2),
             "tiebreak": e["tiebreak"], "gate_failures": e["gate_failures"]}
            for e in ranked
        ]

    # Wide matrix: (model, condition) -> {task_id: score}, plus a mean across tasks.
    matrix = {}
    for e in envs:
        key = f"{e['model']}::{e['condition']}"
        matrix.setdefault(key, {"model": e["model"], "condition": e["condition"], "scores": {}})
        matrix[key]["scores"][e["task_id"]] = round(e["score"], 2)
    for row in matrix.values():
        s = list(row["scores"].values())
        row["mean_score"] = round(sum(s) / len(s), 2) if s else 0.0

    board = {"generated": _utcnow_iso(), "schema_version": SCHEMA_VERSION,
             "n_submissions": len(envs), "tasks": tasks,
             "matrix": sorted(matrix.values(), key=lambda r: r["mean_score"], reverse=True)}
    if out_path:
        json.dump(board, open(out_path, "w"), indent=2)
    return board


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uniform grading front-end + leaderboard aggregator.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grade", help="grade one submission -> envelope JSON")
    g.add_argument("--task", required=True, help="task_id (must be in the manifest)")
    g.add_argument("--subject", help="the subject graded, for a task graded per subject "
                                     "(per_subject in the manifest); its output is read at "
                                     "submissions/<task_id>/<subject>/")
    g.add_argument("--case", dest="subject", help="the case id a run names; the reference "
                                                  "dataset's cases.json maps it to the subject, "
                                                  "and the output is read under the subject")
    g.add_argument("--submission-dir", required=True, help="dir holding submission/output.nii.gz")
    g.add_argument("--manifest", default=str(Path(__file__).parent / "run_manifest.json"))
    g.add_argument("--graders-root", help="override; default = parent of the manifest's dir")
    g.add_argument("--model", default="unknown")
    g.add_argument("--condition", default="baseline", help="baseline | skill")
    g.add_argument("--timestamp", help="ISO-8601; default = now (UTC)")
    g.add_argument("--out", help="write the envelope here (also printed to stdout)")

    a = sub.add_parser("aggregate", help="many envelopes -> ranked leaderboard.json")
    a.add_argument("--glob", required=True, help="glob for envelope JSONs, e.g. 'results/*.json'")
    a.add_argument("--out", required=True)

    ls = sub.add_parser("list", help="print the live (gradeable) task IDs from the manifest")
    ls.add_argument("--manifest", default=str(Path(__file__).parent / "run_manifest.json"))
    ls.add_argument("--verbose", action="store_true", help="also show scorer + detail kind")

    args = ap.parse_args(argv)
    if args.cmd == "list":
        tasks = json.load(open(args.manifest))["tasks"]
        for tid in sorted(tasks):
            if args.verbose:
                s = tasks[tid]
                print(f"{tid:42s} {Path(s['scorer']).name:22s} {s['detail_kind']}")
            else:
                print(tid)
        return 0
    if args.cmd == "grade":
        env = grade(args.task, args.submission_dir, args.manifest, args.graders_root,
                    args.model, args.condition, args.timestamp, args.subject)
        print(json.dumps(env, indent=2))
        if args.out:
            json.dump(env, open(args.out, "w"), indent=2)
        # Exit code mirrors validity so CI can branch, but the envelope is always written.
        return 0 if env["valid"] else 1
    if args.cmd == "aggregate":
        board = aggregate(args.glob, args.out)
        print(f"wrote {args.out}: {board['n_submissions']} submissions across "
              f"{len(board['tasks'])} tasks, {len(board['matrix'])} model×condition rows")
        return 0


if __name__ == "__main__":
    sys.exit(main())
