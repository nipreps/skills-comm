"""Split each rubric into the policy half that stays in git and the calibrated half that
moves to the gated dataset.

Wave 7 recorded 22 runs reading rubric and PROVENANCE text off public GitHub. What is
worth hiding is not the policy -- a reviewer must be able to read how grading works
without gated access -- but the numbers that describe this particular reference, above
all which tools produced it.

Moves (answer key):
  reference_tools / panel   the exact tools to run to reproduce the consensus
  floor_arms                the arm the zero point is anchored on, by name
  tau_mm, envelope          derived from the panel's own spread
  focal_max_cm3             derived from the panel's leave-one-out
  consensus                 reference volumes
  reference_notes           lesion volume and foci counts
  focal_basis, dura_basis   prose quoting the numbers above
  _pack.note                prose naming the panel and the tools dropped from it
  focal_bg_basis            prose naming the non-panel masks the cap was measured on
  collapse_margin_basis     prose naming the panel and the parcellation it was checked against

Two tasks move more, because of what their reference is. The registration tasks are graded
against the template itself, so `grid` describes the reference rather than the subject's own
image. The WMH reference is a set of human tracings, so `metric_thresholds`, `inter_rater`
and `notes` report what those raters achieved.

Stays (policy, literature, or derivable from the image the agent is given):
  gates, weights, slack, verdict_thresholds, plausible volumes, the reasoning behind
  each threshold, the fixed caps and their basis, labels, item, prompt.

The reasoning for a threshold stays public even where the value does not: a reviewer must
be able to read how grading works, and check it against the literature, without gated
access.

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
MOVE = ["reference_tools", "panel", "floor_arms", "tau_mm", "envelope", "focal_max_cm3",
        "consensus", "reference_notes", "focal_basis", "dura_basis", "focal_bg_basis",
        "collapse_margin_basis"]
EXTRA = {"structural-mni-registration": ["grid"],
         "functional-bold-to-mni": ["grid"],
         "clinical-wmh-segmentation": ["metric_thresholds", "inter_rater", "notes"]}

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--write", action="store_true")
a = ap.parse_args()

print(f"{'task':40s} {'subject':14s} {'moved':>6s} {'kept':>5s}  fields moved")
n = 0
for rub in sorted(G.glob("*/rubrics/*.json")):
    task, sub = rub.parts[-3], rub.stem
    d = json.loads(rub.read_text())
    moved = {k: d[k] for k in MOVE + EXTRA.get(task, []) if k in d}
    # `grid` itself stays for the mask tasks -- the scorer reads raw_affine off it -- but
    # `grid.tool` names the panel member whose output defined the grid, and nothing reads it
    kept = {k: v for k, v in d.items() if k not in moved}
    if isinstance(kept.get("grid"), dict) and "tool" in kept["grid"]:
        kept["grid"] = {k: v for k, v in kept["grid"].items() if k != "tool"}
        moved.setdefault("grid_tool", d["grid"]["tool"])
    # `_pack.reference` says where to fetch the reference and stays; `_pack.note` says
    # what it was built from
    if isinstance(kept.get("_pack"), dict) and "note" in kept["_pack"]:
        kept["_pack"] = {k: v for k, v in kept["_pack"].items() if k != "note"}
        moved.setdefault("pack_note", d["_pack"]["note"])
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
        dst = out / f"{sub}.json"
        # merge rather than replace: a later run that moves one more field must not drop
        # what an earlier one put there
        prev = json.loads(dst.read_text()) if dst.is_file() else {}
        prev.update(moved)
        dst.write_text(json.dumps(prev, indent=2) + "\n")
print(f"\n{n} rubrics split" + ("" if a.write else " (dry run; pass --write)"))
if a.write:
    print(f"calibration staged under {STAGE}")
