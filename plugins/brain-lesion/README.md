# Brain-lesion workflows

Autonomous routing and reproducible segmentation/QC for common brain-lesion tasks. The skills use MRI evidence and explicit uncertainty; they do not make clinical diagnoses.

## Skills

| Skill | Slash command | Use |
|---|---|---|
| `skills/lesion-identification/` | `/lesion-identification` | Characterize an unspecified or ambiguous lesion and report evidence and uncertainty. |
| `skills/lesion-segmentation/` | `/lesion-segmentation` | Route generic segmentation requests to identification and, when evidence meets its eligibility rule, a supported pathology-specific workflow. |
| `skills/acute-stroke-segmentation/` | `/acute-stroke-segmentation` | Segment an established acute ischaemic lesion from diffusion MRI. |
| `skills/chronic-stroke-segmentation/` | `/chronic-stroke-segmentation` | Segment an established chronic infarct or encephalomalacic cavity from structural MRI. |
| `skills/wmh-segmentation/` | `/wmh-segmentation` | Segment established white-matter hyperintensities from structural MRI. |
| `skills/lesion-segmentation-qc/` | `/lesion-segmentation-qc` | Assess lesion masks with numeric checks, visual overlays, and a human verification form. |

The workflows target Neurodesk with version-pinned modules and SLURM. Detailed tool invocations, QC criteria, and output contracts live in each skill's `references/` directory.

## Install

```bash
# Session-only testing
claude --plugin-dir ./plugins/brain-lesion

# Permanent install
claude plugin install ./plugins/brain-lesion
```

## Dependencies

Install or make available the `neuroimaging-integrity` plugin for its
`data-integrity` handoff. Brain-mask generation and brain-mask QC workflows
also require the existing `brain-extraction` collection. The procedures report
unavailable dependencies and stop safely; they do not ask for a tool choice or
manufacture a replacement workflow.

Host-side QC and publication helpers use the pinned packages in
`python-requirements.txt`; do not install packages during a Slurm analysis job.

## Contributors

- micmas
