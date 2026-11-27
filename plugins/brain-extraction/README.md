# Brain extraction

Adult brain extraction and skull-stripping quality control using autonomous
tool selection, SLURM execution, grid-checked masks, and numeric/visual QC.

## Skills

| Skill | Slash command | Use |
|---|---|---|
| `brain-extraction/` | `/brain-extraction` | Select a documented compatible method, submit a pinned SLURM workflow, and publish a grid-checked adult brain mask. |
| `brain-extraction-qc/` | `/brain-extraction-qc` | Compute numeric QC, render outline/mosaic PNGs, and produce a structured report plus human verification form. |

Both skills target Neurodesk. Detailed method invocations and QC criteria are in `references/` and load only when needed.

The publication contract accepts adult brain masks in the 900–1900 cm³ range.
It has no override and does not support paediatric, neonatal, rodent, markedly
atrophic, or post-resection anatomy.

The `brain-lesion` plugin uses this collection when it needs a brain mask for
lesion QC. Keep this contribution at its existing repository location so those
handoffs resolve.

## Install

```bash
# Session-only testing
claude --plugin-dir ./plugins/brain-extraction

# Permanent install
claude plugin install ./plugins/brain-extraction
```

The bundled publication and QC helpers live in each skill's `scripts/`
directory. Their pinned host-side dependencies are listed in
`python-requirements.txt`; do not install packages during a Slurm job.

## Contributors

- Brent McPherson
- micmas (workflow and QC updates)
