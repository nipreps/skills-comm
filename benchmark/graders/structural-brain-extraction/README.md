# Grader: `structural-brain-extraction`

A **consensus-calibrated grader** for the `structural-brain-extraction` benchmark task — a
more discriminating alternative to grading a skull-strip by *Dice against one reference mask*.

![How a brain-extraction submission is graded: five skull-strippers are fused by STAPLE into core, margin and background zones; a submission passes ten validity gates, then earns a 0-100 quality score weighting NSD 30%, core recall 25%, background inclusion 20%, HD95 15% and volume error 10%; an FSL BET run at f=0.7 would score about 71 on metrics alone but fails the focal-core-cut gate.](brain_extraction_grading.png)

*Full size: [`brain_extraction_grading.png`](brain_extraction_grading.png). Every number in it comes
from this pack's `rubrics/<subject>.json` and the test-evidence runs below.*

The prompt is tool-agnostic (`tool_mode: agnostic`), so the grader must ask *"is this a competent
brain mask?"*, not *"does it match one specific tool?"*. Every skull-stripper draws a slightly
different boundary and they disagree in a few predictable places (sagittal sinus, tentorium,
brainstem cut-off, sulcal CSF). So instead of one mask, the grader carries a **STAPLE consensus of a
panel of tools**, split into three zones, and scores only the *unambiguous* voxels:

| zone (value) | meaning | scored? |
|---|---|---|
| **core** (2) | every panel tool includes it | yes — dropping it = brain cut |
| **margin** (1) | the tools legitimately disagree | **no** — legitimate freedom |
| **background** (0) | no panel tool includes it | yes — including it = skull/dura/neck kept |

Every threshold (the surface tolerance τ, the per-metric pass/fail envelope, the gate caps) was
**calibrated from the data** (leave-one-tool-out), never hand-picked. See [`PROVENANCE.md`](PROVENANCE.md).

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/structural-brain-extraction/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

That detail is gated because it describes the answer: in one benchmark wave, agent runs
retrieved these files from GitHub and one rebuilt the panel consensus from them. Access
is granted on request, and everything needed to audit *how* grading works — the gates,
weights, verdict thresholds and the scoring scale — stays here.

## Layout

```
structural-brain-extraction/
├── rubrics/<subject>.json            # per-subject calibration: τ, envelope, weights, gate caps, grid
├── score_brain_mask.py               # the grader — importable score() + CLI
├── reference/                        # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md                     #   dataset path + fetch command
│   └── .gitignore                    #   keeps *.nii.gz out of git
├── brain_extraction_grading.png     # the explainer figure above
├── README.md
└── PROVENANCE.md
```

The consensus reference (`consensus_mask.nii.gz`, `consensus_zones.nii.gz`) is on the Hugging Face
Hub — `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction/<subject>/`.
Fetch it into `reference/` before grading:

```bash
python benchmark/harness/fetch_reference.py --task structural-brain-extraction
```

The pack is **frozen once** per benchmark subject; scoring a submission never re-calibrates — it
only computes the cheap per-mask metrics against this reference.

## Run it

```bash
python3 score_brain_mask.py --mask agent_mask.nii.gz --pack . \
    [--stripped agent_brain.nii.gz] [--json result.json]
```

Output is JSON: `verdict`, `quality` (0–100), `gate_failures`, `load_notes`, per-metric `metrics`
and `subscores`. Exit code is `0` for a valid submission, `1` if any gate failed — so it drops into
a harness as a pass/fail check. Depends only on `numpy`, `scipy`, `nibabel`.

Two stages: **gates** (any failure ⇒ `invalid`, score 0, gate named) then a **weighted quality**
mapped onto the leave-one-tool-out envelope. The five scored metrics and weights: NSD@τ (0.30),
core recall (0.25), background FP (0.20), HD95 (0.15), volume error (0.10). The gates include the
discriminating **`no_focal_core_loss`** — it fails a mask that cuts a *solid* chunk out of the
core beyond the calibrated cap, which a global core-recall would dilute. Solid means it survives
being shaved by one voxel, so a uniformly tighter boundary is priced by τ, NSD and HD95 instead of
being read as a missing structure. The same measure guards `no_focal_bg_inclusion`, so a mask
sitting a millimetre outside the margin is not read as a swallowed chunk of skull either.

## How it's wired into `benchmark/tasks.json`

The task's grader-only `solution` carries a `grader` block that points here (its `metric`,
`ground_truth`, and `ground_truth_location` describe this consensus grader — the old single-mask
Dice fields were replaced):

```json
"grader": {
  "kind": "consensus-calibrated",
  "pack": "benchmark/graders/structural-brain-extraction/",
  "reference_fetch": "python benchmark/harness/fetch_reference.py --task structural-brain-extraction",
  "entry": "score_brain_mask.py",
  "invoke": "python3 benchmark/graders/structural-brain-extraction/score_brain_mask.py --mask <AGENT_MASK> --pack benchmark/graders/structural-brain-extraction/",
  "validity_criterion": "verdict != invalid (script exit code 0)",
  "pass_criterion": "verdict is acceptable or within_reference_variability"
}
```

A harness fetches the reference (`reference_fetch`) and runs `invoke`. Exit code 0 means that the
submission passed all validity gates. The submission passes the benchmark when the verdict is
`acceptable` or `within_reference_variability`.

## Policy knobs

- **Reference panel** (`rubrics/<subject>.json:reference_tools`) — defines the consensus AND every threshold.
  Adding a tool only *loosens* the benchmark, because the core is an intersection.
- **`focal_max_cm3`** — calibrated (`SLACK` × worst held-out focal miss, floored), the miss measured
  the same way the scorer measures a submission's: largest component surviving a max(1.5 mm, one voxel) shave.
  5.0 cm³ across this task's subjects. Larger = more lenient on localised cuts.
- **`native_grid` gate** — here a header-only deoblique (the sform/qform rewritten with the
  voxel data unmoved, as several tools emit) is recovered onto the native grid
  rather than failed; flip to strict if the task should reject any header that doesn't match the input.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubrics/<subject>.json`.

| verdict | meaning |
|---|---|
| `within_reference_variability` | inside the panel's own leave-one-tool-out spread — every metric is at least as good as the weakest the reference tools themselves achieve, so the submission cannot be told apart from a panel member |
| `acceptable` | `quality >= 60` |
| `marginal` | `quality >= 30` |
| `unacceptable` | below that |
| `invalid` | a validity gate failed; `quality` is forced to 0 |

A submission passes when the verdict is `within_reference_variability` or `acceptable`.
`within_reference_variability` is the top grade, not a hedge: it says the answer sits
inside the disagreement the reference itself carries, which is as close as this task can
measure.
