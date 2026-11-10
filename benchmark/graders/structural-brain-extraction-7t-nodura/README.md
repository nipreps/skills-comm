# Grader: `structural-brain-extraction-7t-nodura`

A **consensus-calibrated grader with an added dura gate** for the *same* 7T MP2RAGE subjects as
`structural-brain-extraction-7t` (CEREBRUM-7T `ds003642`), but for an **explicit
"remove the dura" prompt**. It tests **instruction-following**: does the submission not only extract
the brain but also strip the dura the prompt asked for?

## Why an explicit no-dura prompt

Skull-strippers disagree on how much of the outer CSF/dura rim to keep, and that is normally an
unstated convention — penalising it would be unfair. Putting **"remove the dura" in the prompt**
turns it into a *stated requirement*: a mask that retains a dura rim is now objectively failing the
task, not picking a defensible convention.

## How it grades

The submission is scored by the **shared scorer**, pointed at this pack:

```bash
# fetch the reference (see reference/README.md), then:
python3 ../structural-brain-extraction/score_brain_mask.py \
    --mask agent_mask.nii.gz --pack . [--stripped agent_brain.nii.gz] [--json result.json]
```

Grading composes two things:

1. **A valid brain extraction** — the same core/margin/background consensus as the `-7t` task
   (the brain, incl. cerebellum + brainstem, must be kept).
2. **The `no_dura_inclusion` gate** — the submission must not extend past the **dura-out pial
   envelope** into the dura/skull. `dura_over_env_cm3 = volume(mask AND NOT envelope)`; the gate
   fails (→ `invalid`) when it exceeds **`dura_max_cm3` = 50 cm³** (fixed). The gate is one-sided:
   keeping *less* than the envelope is not penalised here (the core/focal gates already guard
   against cutting brain).

The gate activates only because this pack ships `reference/dura_envelope.nii.gz`; the shared scorer
skips it for every other pack.

## The envelope (dura-out reference)

Built from the **union of the four whole-brain tissue segmentations** shipped with CEREBRUM-7T
shipped with the dataset — all dura-out by construction. The union covers the
cerebellum + brainstem (which the cerebrum-focused segmentations alone miss); the sulci are then
**filled** by a 5-voxel (3.1 mm) morphological closing + hole-fill so the boundary is the outer
**pial** surface. This is deliberate: the envelope penalises *dura*, not *sulcal CSF*.

## Same output, different verdict

![How the 7T no-dura gate works: four coronal panels of one subject. The first shades the consensus core, which is scored, and the margin, which never is. The second draws the pial envelope against the consensus reference, which itself sits partly outside it. The third shows a dura-aware stripper well inside the cap and passing. The fourth shows a rim-retaining stripper many times over the cap, a thick rim over the vertex and inferior surface, failing.](nodura_dura_gate.png)

The point of the task, scored on this subject's tools:

| tool, at its defaults | dura beyond envelope | `-7t` (standard) | `-7t-nodura` (this pack) |
|---|---|---|---|
| a dura-aware stripper | well inside the cap | within_reference_variability | within_reference_variability |
| a rim-retaining stripper | many times the cap | marginal | **invalid** (`no_dura_inclusion`) |

The rim-retaining tool's identical mask is merely mediocre on the standard task and fails outright here — the
instruction-following signal. The consensus reference itself sits 15.2–33.7 cm³ outside the
envelope, so the cap has to clear that before it can fail anything.

## Layout

```
structural-brain-extraction-7t-nodura/
├── rubrics/policy.json  # shared policy: weights, gates, verdict thresholds. The calibrated half and this subject's own fields are merged in from the gated dataset at fetch time
├── reference/           # consensus + dura_envelope NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-brain-extraction-7t-nodura/<subject>/`.
The pack is frozen once; scoring never re-calibrates.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in the merged `reference/rubric.json`.

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
