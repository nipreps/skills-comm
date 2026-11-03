# Benchmark grading harness

Automated, uniform grading for the neuroimaging benchmark. An open-weight model runs a task
prompt unattended (it picks its own tools), produces the required output files, and this harness scores
it against a frozen reference — producing a numeric, rankable result.

## The two planes

The model *doing* a task needs a full neuroimaging stack; the grader needs only `numpy`,
`nibabel` and `scipy`. So the pipeline splits, and the split is also the anti-leak boundary:

```
 EXECUTION PLANE  (wherever the tools live)           GRADING PLANE  (any github-hosted runner)
 ─────────────────────────────────────────────        ──────────────────────────────────────────
 reads the task prompt from tasks.json                 downloads submissions/<task>/
 agent picks and runs its own tools                    fetches the reference into pack/reference/
 writes the required output files          ──────►      merges the gated calibration into the rubric
 never sees the reference                              runs the scorer via grade_wrapper.py
 nor the calibration                                   emits a ranked-ready envelope JSON
```

The reference NIfTIs live only in the grading plane, pulled from the Hugging Face Hub at grade
time, so the ground truth is never in the agent's input. A rubric straddles the boundary: its
policy half — gates, weights, verdict thresholds — is in this repository and readable by anyone,
while the half describing the reference is gated and merged in the grading plane only.

The execution plane is whatever environment supplies the task's tools; nothing in the harness
depends on which. A plane that can run the task prompt and write the required output paths can be
graded, whether that is a container, a cluster or a workstation.

## Files

| file | role |
|---|---|
| `run_manifest.json` | one entry per gradeable task: which pack, which scorer, the prediction flag (`--mask`/`--seg`/`--pred`), the detail shape, and the reference location + filenames. The single source of truth the tooling reads. |
| `fetch_reference.py` | pulls a task's reference NIfTIs from the Hugging Face dataset `neurodeskorg/skills-comm-ground-truth` at the revision pinned in the manifest, into its `pack/reference/`. The dataset is gated, so this needs a read token in `HF_TOKEN` for an account with access. Idempotent. |
| `smoke_test.py` | probes every graded task through its shipped scorer: a copy of the reference must score 100, an empty mask must be invalid, another subject's rubric must be refused, and the registration tasks must rank a nonlinear warp above an affine one. Read-only; takes `--build` for the tree holding staged references. |
| `split_rubrics.py` | the one-shot migration that divided each rubric into the policy half kept here and the calibrated half that ships gated. Kept as the record of how the split was made. |
| `grade_wrapper.py` | the uniform front-end. Dispatches to the correct scorer, wraps the result in a stable envelope, and aggregates many envelopes into a ranked leaderboard. |

## The output contract (why grading is deterministic)

Every gradeable task prompt in `tasks.json` mandates exact output paths. The primary output is
always `submissions/<task_id>/output.nii.gz`. Registration tasks also require a transformed
segmentation or mask, and brain-extraction tasks can include `stripped.nii.gz`. One
`submissions/` tree holds one folder per task, so a run over many tasks stays namespaced. The
grader reads only the paths in `run_manifest.json`; it does not search for outputs.

## The scoring model — a tier *and* a number

Each scorer runs a cascade of gates, then a score, then one override — and you always get a
rankable number:

1. **Validity gates** (binary, native grid, non-empty, plausible volume, plus task-specific gates
   like no-dura-inclusion, lesion-retained, no-class-collapse). Any failure → `verdict = "invalid"`,
   `score = 0`.
2. **Quality** (only if all gates pass) → a weighted 0–100 from per-metric subscores, banded into
   `unacceptable / marginal / acceptable` at the pack's `verdict_thresholds`.
3. **`within_reference_variability`** overrides the band when *every* scored metric lands inside what the pack's
   own references achieve. Each pack sets that bar from its calibration: a consensus-calibrated pack
   asks for every metric at least as good as the worst held-out tool, an inter-rater-calibrated pack
   asks for full marks on every metric. It is a separate test, not a score threshold — so a submission
   can be `within_reference_variability` without scoring 100, and `score` is **not** monotonic with the tier.

   For a consensus-calibrated pack the tier starts at **60**, not near 100. A metric mapped onto the
   leave-one-tool-out envelope reaches `slack / (1 + slack)` at the worst held-out tool, which is
   exactly 0.60 at the slack used here, so a submission sitting at the weak edge of the envelope on
   every metric scores 60 and still qualifies. A low score carrying this tier therefore means
   "inside the reference's own spread, at its weak edge" — not a contradiction. Agent submissions
   rarely land there, because sitting at the weak edge on *all* metrics at once is uncommon; a
   reference tool on a widely-spread panel can.

`valid` and `score` are independent: a submission can be valid but score low (e.g. a mask that
passes every gate but overlaps the reference poorly). Only `invalid` forces the score to 0.

Two packs carry a one-page figure of the whole cascade — reference construction, gates, weights, and
a worked case where the gate and the score disagree. They are worth reading before the others,
because they cover the two ways a pack is calibrated:

| figure | calibration | shows |
|---|---|---|
| [`structural-brain-extraction`](../graders/structural-brain-extraction/README.md) | consensus of a tool panel, leave-one-tool-out | a mask that scores ~71 on metrics yet fails a gate |
| [`clinical-wmh-segmentation`](../graders/clinical-wmh-segmentation/README.md) | inter-rater, three expert tracings | a mask that finds every lesion (F1 = 1.0) and still only reaches `marginal` |

## Envelope schema (`schema_version 1.0`)

`grade_wrapper.py grade` emits one JSON per submission:

```json
{ "task_id": "...", "model": "...", "condition": "baseline|skill", "timestamp": "...Z",
  "valid": true, "verdict": "within_reference_variability", "score": 100.0, "tiebreak": 1.0,
  "gate_failures": [], "detail": { "kind": "binary|multiclass", ... },
  "raw": { ...full untouched scorer output for drill-down... } }
```

`detail` normalises the two scorer families: `binary` carries `metrics` + `subscores`; `multiclass`
carries `per_class`. `tiebreak` (mean Dice) breaks ties at equal `score`.

## Running it

```bash
# list the live (gradeable) task IDs — the functional subset of the full catalog
python grade_wrapper.py list            # add --verbose for scorer + detail kind

# fetch the grader-side reference for a task (gated dataset; export HF_TOKEN first).
# Most tasks are graded per subject and need --subject; the manifest lists which, and
# fetch_reference names the available subjects if one is required and missing.
python fetch_reference.py --task clinical-wmh-segmentation --subject Utrecht_39

# grade one submission -> envelope JSON
# --submission-dir is the working root; the grader looks for
# <root>/submissions/<task_id>/output.nii.gz (so one root can hold many tasks)
python grade_wrapper.py grade \
  --task clinical-wmh-segmentation --subject Utrecht_39 --submission-dir ./run_qwen \
  --model qwen --condition baseline --out results/qwen.json

# rank many envelopes -> leaderboard.json (per-task ranking + model x task matrix)
python grade_wrapper.py aggregate --glob "results/*.json" --out results/leaderboard.json
```

Add a task by giving it an entry in `run_manifest.json` (pack, scorer, flag, reference) — no
code change needed.

The full task catalog (`tasks.json`) stays complete; the automated subset is the manifest.
Live tasks also carry `"grading": "automated"` in `tasks.json`, so the functional set is
queryable from the catalog itself. `run_manifest.json` remains the source of truth for what the
harness grades.

## CI

`.github/workflows/grade.yml` drives this on GitHub:

- **`grade`** — reusable (`workflow_call`) + manual: scores one real submission and uploads its
  envelope. The execution-plane workflow calls this per run.
- **`selftest`** — on every push touching `harness/` or `graders/`: synthesises a perfect
  submission (a copy of the reference) and a broken one (all-zeros), and asserts the grader
  returns `within_reference_variability`/100 and `invalid` respectively. Runs entirely on a github-hosted
  runner — it validates the grading contract without involving the execution plane at all.
