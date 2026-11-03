"""Split each rubric into the policy half that stays in git and the calibrated half that
moves to the gated dataset.

Wave 7 recorded 22 runs reading rubric and PROVENANCE text off public GitHub. What is
worth hiding is not the policy -- a reviewer must be able to read how grading works
without gated access -- but the numbers that describe this particular reference, above
all which tools produced it.

Moves (answer key):
  reference_tools / panel   the exact tools to run to reproduce the consensus
  tau_mm, envelope          derived from the panel's own spread
  focal_max_cm3             derived from the panel's leave-one-out
  consensus                 reference volumes
  reference_notes           lesion volume and foci counts
  focal_basis, dura_basis   prose quoting the numbers above

Stays (policy, literature, or derivable from the image the agent is given):
  gates, weights, slack, verdict_thresholds, plausible volumes, metric_thresholds and
  their literature basis, the fixed caps and their basis, grid, labels, item, prompt.

Usage: split_rubrics.py [--write]
"""
import argparse
import json
import os
from pathlib import Path

# This file lives in benchmark/harness/, so the graders sit beside it.
G = Path(__file__).resolve().parent.parent / "graders"
# Where the gated half is written for upload; not part of the repository.
STAGE = Path(os.environ.get("SKILLS_COMM_BUILD", ".")).expanduser() / "hf_calibration"
MOVE = ["reference_tools", "panel", "tau_mm", "envelope", "focal_max_cm3", "consensus",
        "reference_notes", "focal_basis", "dura_basis"]

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--write", action="store_true")
a = ap.parse_args()

print(f"{'task':40s} {'subject':14s} {'moved':>6s} {'kept':>5s}  fields moved")
n = 0
for rub in sorted(G.glob("*/rubrics/*.json")):
    task, sub = rub.parts[-3], rub.stem
    d = json.loads(rub.read_text())
    moved = {k: d[k] for k in MOVE if k in d}
    kept = {k: v for k, v in d.items() if k not in moved}
    if not moved:
        print(f"{task:40s} {sub:14s} {'-':>6s} {len(kept):5d}  (nothing to move)")
        continue
    # a marker so a merge failure is loud rather than a silently policy-only rubric
    kept["_calibration"] = "gated: fetched from the reference dataset and merged by fetch_reference.py"
    n += 1
    print(f"{task:40s} {sub:14s} {len(moved):6d} {len(kept):5d}  {', '.join(moved)[:60]}")
    if a.write:
        rub.write_text(json.dumps(kept, indent=2) + "\n")
        out = STAGE / task
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{sub}.json").write_text(json.dumps(moved, indent=2) + "\n")
print(f"\n{n} rubrics split" + ("" if a.write else " (dry run; pass --write)"))
if a.write:
    print(f"calibration staged under {STAGE}")
