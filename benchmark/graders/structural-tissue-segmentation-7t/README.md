# Grader: `structural-tissue-segmentation-7t`

A **consensus-calibrated grader** for multi-class brain **parcellation** of a 7T MP2RAGE scan
(CEREBRUM-7T `ds003642`, `sub-025`, 0.63 mm isotropic). It grades a six-structure label map —
grey matter, basal ganglia, white matter, ventricles/CSF, cerebellum, brainstem — against a
consensus of the panel's segmentations. Companion to the binary `structural-brain-extraction-7t`
tasks on the same subject.

It is the multi-class analogue of the brain-extraction grader: instead of one binary mask scored
against a STAPLE consensus, each of six classes is scored against a **majority-vote consensus** of
the panel's tools, split into per-class **unanimous-core** (all tools agree) and **majority-boundary**
(partial-volume disagreement) zones. Every threshold is calibrated by leave-one-tool-out. See
[`PROVENANCE.md`](PROVENANCE.md).

## The reference

Built from several independent sources rather than one, so that the agreement between
them, and not any single tool's opinion, defines what counts as correct. Which sources,
how they were combined, the surface tolerance and the calibrated caps are documented in
`calibration/structural-tissue-segmentation-7t/PROVENANCE.md` inside the gated reference dataset
[`neurodeskorg/skills-comm-ground-truth`](https://huggingface.co/datasets/neurodeskorg/skills-comm-ground-truth).

That detail is gated because it describes the answer: in one benchmark wave, agent runs
retrieved these files from GitHub and one rebuilt the panel consensus from them. Access
is granted on request, and everything needed to audit *how* grading works — the gates,
weights, verdict thresholds and the scoring scale — stays here.

## Ships its own scorer

Parcellation needs a different scorer from the binary brain-extraction one, so this pack carries
**`score_tissue_seg.py`** (per-class Dice / NSD / core-recall + the multi-class gates):

```bash
# fetch the reference (see reference/README.md), then:
python3 score_tissue_seg.py --seg agent_dseg.nii.gz --pack . [--json result.json]
```

The agent must output an **integer label map** with the fixed legend
`1=GM 2=basal_ganglia 3=WM 4=ventricles 5=cerebellum 6=brainstem` in native T1w space.

## Scoring

- **Per-class metrics:** Dice, NSD (surface agreement within a per-class tolerance `τ`), and
  core-recall (fraction of the unanimous core recovered). Quality = mean of the six per-class
  qualities, each mapped through the LOTO envelope (median = full marks, worst = pass line).
- **Gates (→ `invalid`):** `valid_labels` (integer map, the six classes present), `native_grid`,
  and `no_class_collapse` (every class must recover ≥ 50 % of its unanimous core — catches a
  swapped or missing class, e.g. GM/WM confusion).

## Layout

```
structural-tissue-segmentation-7t/
├── rubrics/<subject>.json      # per-subject per-class τ, LOTO envelope, weights, gates
├── score_tissue_seg.py      # the multi-class scorer
├── reference/               # consensus NIfTIs — fetched from the Hub, plus the selected rubric.json
│   ├── README.md
│   └── .gitignore
├── README.md
└── PROVENANCE.md
```

Reference: Hugging Face `neurodeskorg/skills-comm-ground-truth`, path `structural_gt/structural-tissue-segmentation-7t/<subject>/`.
The pack is frozen once; scoring never re-calibrates.

## Verdicts

Best to worst. `quality` is the weighted score in 0–100; the thresholds are in `rubric.json`.

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
