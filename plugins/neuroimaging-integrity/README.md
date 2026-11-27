# Neuroimaging integrity

Read-only checks for the completeness, consistency, and spatial interpretability of downloaded or task-input neuroimaging data.

## Skills

| Skill | Slash command | Use |
|---|---|---|
| `skills/data-integrity/` | `/data-integrity` | Audit DICOM series and NIfTI/BIDS inputs before analysis; report missing inventory, corruption, metadata conflicts, and geometry problems without repairing source data. |

The skill targets Neurodesk with Lmod and SLURM. It keeps detailed parser commands and QC criteria in load-on-demand references.

## Install

```bash
# Session-only testing
claude --plugin-dir ./plugins/neuroimaging-integrity

# Permanent install
claude plugin install ./plugins/neuroimaging-integrity
```

## Contributors

- micmas
